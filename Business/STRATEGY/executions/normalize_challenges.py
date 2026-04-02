"""
Normalize PropFirmMatch challenge data and load into SQLite database.
Produces:
  - propmatch_challenges.db  (SQLite)
  - data_quality_report.txt  (console + file)
"""
import csv, json, sqlite3, re, os, sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# ── paths ───────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent / "resources" / "PropFirmData"

def _find_latest_json() -> Path:
    """Always use the most recently modified challenges JSON."""
    candidates = sorted(BASE.glob("propmatch_challenges_*.json"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No propmatch_challenges_*.json found in {BASE}")
    return candidates[-1]

try:
    INPUT_JSON = _find_latest_json()
except FileNotFoundError:
    INPUT_JSON = None
OUTPUT_DB  = BASE / "propmatch_challenges.db"
OUTPUT_CSV = BASE / "propmatch_challenges_normalized.csv"
REPORT_TXT = BASE / "data_quality_report.txt"

# ── known platform tokens ──────────────────────────────────────────────────────
KNOWN_PLATFORMS = [
    "BrightFunded Platform",
    "Match Trader",
    "TradeLocker",
    "TradingView",
    "Vo Volumetrica FX",
    "ThinkTrader",
    "cTrader",
    "DXTrade",
    "DxTrade",
    "MT4",
    "MT5",
]
# sort longest-first so greedy match works
KNOWN_PLATFORMS.sort(key=len, reverse=True)

PLATFORM_ALIASES = {
    "DxTrade": "DXTrade",
    "(DXTrade)": "DXTrade",
    "MatchTrader": "Match Trader",
    "(MatchTrader)": "Match Trader",
    "Vo Volumetrica FX": "Volumetrica FX",
}

PLATFORM_NOISE = {
    "Platform",
    "Terminal",
    "CF",
    "CFT",
    "Breakout",
}


def split_platforms(raw_list: list[str]) -> list[str]:
    """Split space-concatenated platform strings into individual platforms."""
    if not raw_list:
        return []
    text = " ".join(raw_list)
    platforms = []
    remaining = text
    while remaining.strip():
        remaining = remaining.strip()
        matched = False
        for p in KNOWN_PLATFORMS:
            if remaining.startswith(p):
                platforms.append(p)
                remaining = remaining[len(p):]
                matched = True
                break
        if not matched:
            # take next word as unknown platform
            word, *rest = remaining.split(None, 1)
            platforms.append(word)
            remaining = rest[0] if rest else ""
    # dedupe while preserving order, normalize aliases, and drop noise tokens
    seen = set()
    out = []
    for p in platforms:
        norm = PLATFORM_ALIASES.get(p, p.replace("DxTrade", "DXTrade").strip())
        if not norm:
            continue
        if norm.startswith("(") and norm.endswith(")"):
            norm = norm.strip("() ")
        norm = PLATFORM_ALIASES.get(norm, norm)
        if not norm or norm in PLATFORM_NOISE:
            continue
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


def canonicalize_platforms(raw_list: list[str]) -> list[str]:
    platforms = split_platforms(raw_list)
    filtered = []
    seen = set()
    for platform in platforms:
        canonical = PLATFORM_ALIASES.get(platform, platform)
        if canonical in PLATFORM_NOISE:
            continue
        if canonical not in seen:
            seen.add(canonical)
            filtered.append(canonical)
    return filtered


def _title_from_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    parts = [part for part in slug.split("-") if part]
    if not parts:
        return None
    return " ".join(part.upper() if part.isupper() else part.capitalize() for part in parts)


def _firm_from_program_name(program_name: str | None) -> str | None:
    if not program_name:
        return None
    firm_name = program_name.split(" - ", 1)[0].strip()
    return firm_name or None


def clean_firm_name(raw: str | None, firm_slug: str | None = None, program_name: str | None = None) -> str:
    """Fix corrupted firm names and recover real names from program_name or slug."""
    raw = (raw or "").strip()

    # pattern: Name<number><number>Name  (rating+reviews got concatenated)
    m = re.match(r'^(.+?)(\d+\.\d+)(\d+)\1$', raw)
    if m:
        raw = m.group(1).strip()

    if raw and raw != "NEW":
        return raw

    inferred_name = _firm_from_program_name(program_name)
    if inferred_name:
        return inferred_name

    slug_name = _title_from_slug(firm_slug)
    if slug_name:
        return slug_name

    return "Unknown"


def parse_allocation(raw: str | None) -> float | None:
    """Parse 'Up to 132.5k', '$300k', '400k', '2M' etc to numeric."""
    if not raw:
        return None
    text = raw.replace(",", "").strip()
    m = re.search(r'([\d.]+)\s*(k|m|K|M)?', text, re.IGNORECASE)
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(2) or "").upper()
    if unit == "K":
        val *= 1_000
    elif unit == "M":
        val *= 1_000_000
    return val


def parse_payout_days(timing: str) -> int | None:
    """Extract first numeric day count from payout timing string."""
    if not timing:
        return None
    m = re.search(r'(\d+)\s*(?:days?|calend[ae]r\s*days?|business\s*days?|trading\s*days?)', timing, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.match(r'^(\d+)$', timing.strip())
    if m:
        return int(m.group(1))
    return None


def clean_payout_frequency(raw: str | None) -> str | None:
    """Strip trailing 'Firm Overview' from payout_frequency_panel."""
    if not raw:
        return None
    return re.sub(r'\s*Firm Overview\s*$', '', raw).strip() or None


def parse_reset_fee(raw: str | None) -> float | None:
    """Parse reset_fee_text to numeric dollar amount if possible."""
    if not raw or raw.lower() == "no":
        return None
    m = re.search(r'[\$€£]([\d,.]+)', raw)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def normalize_drawdown_type(raw: str | None) -> str | None:
    if not raw or raw == "-":
        return None
    return raw


def parse_account_size_label(raw: str | None) -> int | None:
    """Parse account-size labels like '2.5K', '625S', or '$100,000'."""
    if not raw:
        return None

    text = raw.strip().upper().replace(",", "").replace("$", "")
    if not text:
        return None

    matches = re.findall(r'(\d+(?:\.\d+)?)\s*([KMS])\b', text)
    if matches:
        value_text, suffix = matches[-1]
        value = float(value_text)
        if suffix == 'K':
            return int(round(value * 1000))
        if suffix == 'M':
            return int(round(value * 1_000_000))
        if suffix == 'S':
            return int(round(value))

    number_matches = re.findall(r'\d+(?:\.\d+)?', text)
    if number_matches:
        return int(round(float(number_matches[-1])))

    return None


def canonical_account_size(raw_account_size, program_name: str | None) -> int | None:
    """Prefer an explicit size token in program_name when it conflicts with scraped size."""
    inferred = parse_account_size_label(program_name)
    if inferred is not None:
        return inferred

    if raw_account_size is None:
        return None

    try:
        return int(raw_account_size)
    except (TypeError, ValueError):
        return parse_account_size_label(str(raw_account_size))


# Map panel "Max Loss Type" → drawdown_type when table column is absent
_MAX_LOSS_TO_DRAWDOWN = {
    "static":    "Static",
    "trailing":  "Trailing",
    "semi-trailing": "Semi-Trailing",
    "eod":       "Balance/Equity - Highest at EOD",
    "end of day": "Balance/Equity - Highest at EOD",
}

def _infer_drawdown_type(max_loss_type: str | None) -> str | None:
    """Infer drawdown_type from the panel's Max Loss Type field."""
    if not max_loss_type:
        return None
    key = max_loss_type.strip().lower()
    return _MAX_LOSS_TO_DRAWDOWN.get(key, max_loss_type)


def normalize_challenge(c: dict) -> dict:
    """Transform a raw scraped challenge dict into a normalized flat row."""
    firm = clean_firm_name(
        c.get("firm", ""),
        firm_slug=c.get("firm_slug"),
        program_name=c.get("program_name"),
    )
    pts = c.get("profit_targets", [])

    # parse scrape metadata
    scrape = c.get("_scrape", {})

    platforms_raw = c.get("platforms", [])
    platforms = canonicalize_platforms(platforms_raw) if platforms_raw else []

    alloc_raw = c.get("max_allocation_per_challenge")
    total_alloc = c.get("total_max_allocation")
    # fix bad total_max_allocation parses (< 1000 when alloc_per is in thousands)
    parsed_alloc = parse_allocation(alloc_raw)
    if total_alloc is not None and parsed_alloc is not None:
        if total_alloc < parsed_alloc:
            total_alloc = parsed_alloc  # at minimum equal to per-challenge

    payout_panel = clean_payout_frequency(c.get("payout_frequency_panel"))
    payout_timing = c.get("payout_timing", "")

    account_size = canonical_account_size(c.get("account_size"), c.get("program_name"))

    return {
        "firm": firm,
        "canonical_firm": firm,
        "firm_slug": c.get("firm_slug"),
        "program_name": c.get("program_name"),
        "rating": c.get("rating"),
        "reviews": c.get("reviews"),
        "account_size": account_size,
        "steps": c.get("steps"),
        "steps_label": c.get("steps_label"),
        "asset_class": c.get("asset_class"),
        "currency": c.get("currency"),
        "country": c.get("country"),

        # fees
        "fee_original": c.get("fee_original"),
        "fee_discounted": c.get("fee_discounted"),
        "fee_assumed": c.get("fee_assumed"),
        "reset_fee": parse_reset_fee(c.get("reset_fee_text")),
        "activation_fee": c.get("activation_fee"),

        # profit targets
        "profit_target_phase1": pts[0] if len(pts) >= 1 else None,
        "profit_target_phase2": pts[1] if len(pts) >= 2 else None,
        "profit_target_phase3": pts[2] if len(pts) >= 3 else None,
        "profit_targets_json": json.dumps(pts) if pts else None,

        # drawdowns
        "daily_drawdown_pct": c.get("daily_drawdown_pct"),
        "max_drawdown_pct": c.get("max_drawdown_pct"),
        "pt_dd_ratio": c.get("pt_dd_ratio"),
        "drawdown_type": normalize_drawdown_type(c.get("drawdown_type")) or _infer_drawdown_type(c.get("max_loss_type")),
        "max_loss_type": c.get("max_loss_type"),
        "daily_drawdown_reset_type": c.get("daily_drawdown_reset_type"),

        # profit split & payouts
        "profit_split_pct": c.get("profit_split_pct"),
        "payout_timing": payout_timing,
        "payout_timing_clean": payout_panel or payout_timing,
        "payout_days": parse_payout_days(payout_timing),

        # trading rules
        "min_trading_days": c.get("min_trading_days"),
        "news_trading": 1 if c.get("news_trading") else (0 if "news_trading" in c else None),
        "copy_trading": 1 if c.get("copy_trading") else (0 if "copy_trading" in c else None),
        "eas_allowed": 1 if c.get("eas_allowed") else (0 if "eas_allowed" in c else None),
        "weekend_holding": 1 if c.get("weekend_holding") else (0 if "weekend_holding" in c else None),
        "overnight_holding": 1 if c.get("overnight_holding") else (0 if "overnight_holding" in c else None),
        "refundable_fee": 1 if c.get("refundable_fee") else (0 if "refundable_fee" in c else None),

        # platforms & leverage
        "platforms_raw": " | ".join(platforms_raw) if platforms_raw else None,
        "platforms": ", ".join(platforms) if platforms else None,
        "canonical_platforms": ", ".join(platforms) if platforms else None,
        "platform_count": len(platforms) if platforms else None,
        "leverage_eval": c.get("leverage_eval"),
        "leverage_funded": c.get("leverage_funded"),

        # allocations
        "max_alloc_per_challenge": parsed_alloc,
        "max_alloc_per_challenge_raw": alloc_raw,
        "total_max_allocation": total_alloc,

        # meta
        "loyalty_pts": c.get("loyalty_pts"),
        "program_type": c.get("program_type"),
        "discount_state": c.get("discount_state"),
        "panel_scraped": 1 if "_panel_scraped_at" in c else 0,
        "panel_error": c.get("_panel_error"),
        "scrape_page": scrape.get("page_number"),
        "scrape_row": scrape.get("row_position"),
        "scraped_at": scrape.get("scraped_at"),
    }


# ── SQLite schema ───────────────────────────────────────────────────────────────
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firm TEXT NOT NULL,
    canonical_firm TEXT,
    firm_slug TEXT,
    program_name TEXT,
    rating REAL,
    reviews INTEGER,
    account_size INTEGER,
    steps INTEGER,
    steps_label TEXT,
    asset_class TEXT,
    currency TEXT,
    country TEXT,

    fee_original REAL,
    fee_discounted REAL,
    fee_assumed REAL,
    reset_fee REAL,
    activation_fee REAL,

    profit_target_phase1 REAL,
    profit_target_phase2 REAL,
    profit_target_phase3 REAL,
    profit_targets_json TEXT,

    daily_drawdown_pct REAL,
    max_drawdown_pct REAL,
    pt_dd_ratio TEXT,
    drawdown_type TEXT,
    max_loss_type TEXT,
    daily_drawdown_reset_type TEXT,

    profit_split_pct REAL,
    payout_timing TEXT,
    payout_timing_clean TEXT,
    payout_days INTEGER,

    min_trading_days INTEGER,
    news_trading INTEGER,
    copy_trading INTEGER,
    eas_allowed INTEGER,
    weekend_holding INTEGER,
    overnight_holding INTEGER,
    refundable_fee INTEGER,

    platforms_raw TEXT,
    platforms TEXT,
    canonical_platforms TEXT,
    platform_count INTEGER,
    leverage_eval TEXT,
    leverage_funded TEXT,

    max_alloc_per_challenge REAL,
    max_alloc_per_challenge_raw TEXT,
    total_max_allocation REAL,

    loyalty_pts INTEGER,
    program_type TEXT,
    discount_state TEXT,
    panel_scraped INTEGER,
    panel_error TEXT,
    scrape_page INTEGER,
    scrape_row INTEGER,
    scraped_at TEXT
);
"""

INSERT_SQL = """
INSERT INTO challenges (
    firm, canonical_firm, firm_slug, program_name, rating, reviews,
    account_size, steps, steps_label, asset_class, currency, country,
    fee_original, fee_discounted, fee_assumed, reset_fee, activation_fee,
    profit_target_phase1, profit_target_phase2, profit_target_phase3, profit_targets_json,
    daily_drawdown_pct, max_drawdown_pct, pt_dd_ratio,
    drawdown_type, max_loss_type, daily_drawdown_reset_type,
    profit_split_pct, payout_timing, payout_timing_clean, payout_days,
    min_trading_days, news_trading, copy_trading, eas_allowed,
    weekend_holding, overnight_holding, refundable_fee,
    platforms_raw, platforms, canonical_platforms, platform_count, leverage_eval, leverage_funded,
    max_alloc_per_challenge, max_alloc_per_challenge_raw, total_max_allocation,
    loyalty_pts, program_type, discount_state,
    panel_scraped, panel_error, scrape_page, scrape_row, scraped_at
) VALUES (
    :firm, :canonical_firm, :firm_slug, :program_name, :rating, :reviews,
    :account_size, :steps, :steps_label, :asset_class, :currency, :country,
    :fee_original, :fee_discounted, :fee_assumed, :reset_fee, :activation_fee,
    :profit_target_phase1, :profit_target_phase2, :profit_target_phase3, :profit_targets_json,
    :daily_drawdown_pct, :max_drawdown_pct, :pt_dd_ratio,
    :drawdown_type, :max_loss_type, :daily_drawdown_reset_type,
    :profit_split_pct, :payout_timing, :payout_timing_clean, :payout_days,
    :min_trading_days, :news_trading, :copy_trading, :eas_allowed,
    :weekend_holding, :overnight_holding, :refundable_fee,
    :platforms_raw, :platforms, :canonical_platforms, :platform_count, :leverage_eval, :leverage_funded,
    :max_alloc_per_challenge, :max_alloc_per_challenge_raw, :total_max_allocation,
    :loyalty_pts, :program_type, :discount_state,
    :panel_scraped, :panel_error, :scrape_page, :scrape_row, :scraped_at
);
"""


# ── Data Quality Report ─────────────────────────────────────────────────────────
def generate_report(raw: list[dict], normalized: list[dict]) -> str:
    lines = []
    def w(s=""): lines.append(s)

    w("=" * 80)
    w("  PROPFIRMMATCH DATA QUALITY REPORT")
    w(f"  Generated: {datetime.now().isoformat()}")
    w(f"  Source: {INPUT_JSON.name}")
    w("=" * 80)

    # ── 1. Overview ──
    w("\n1. OVERVIEW")
    w(f"   Total raw records:       {len(raw)}")
    w(f"   Total normalized:        {len(normalized)}")
    panel_ok = sum(1 for r in normalized if r["panel_scraped"])
    panel_fail = sum(1 for r in normalized if not r["panel_scraped"])
    w(f"   Panel data available:    {panel_ok} ({panel_ok*100/len(normalized):.1f}%)")
    w(f"   Panel open failures:     {panel_fail} ({panel_fail*100/len(normalized):.1f}%)")

    # ── 2. Firm Distribution ──
    w("\n2. FIRM DISTRIBUTION")
    firm_counts = Counter(r["firm"] for r in normalized)
    w(f"   Unique firms: {len(firm_counts)}")
    for firm, cnt in firm_counts.most_common():
        w(f"   {cnt:>4}  {firm}")

    # corrupted firm names that were cleaned
    cleaned = [
        (
            c.get("firm", ""),
            clean_firm_name(
                c.get("firm", ""),
                firm_slug=c.get("firm_slug"),
                program_name=c.get("program_name"),
            ),
        )
        for c in raw
    ]
    fixed = [(orig, clean) for orig, clean in cleaned if orig != clean]
    if fixed:
        w(f"\n   Firm names CLEANED ({len(fixed)} rows):")
        for orig, clean in set(fixed):
            w(f"     '{orig}' → '{clean}'")

    # ── 3. Steps Breakdown ──
    w("\n3. STEPS BREAKDOWN")
    step_counts = Counter(r["steps_label"] for r in normalized)
    for label, cnt in sorted(step_counts.items()):
        w(f"   {cnt:>4}  {label}")

    # ── 4. Account Size Distribution ──
    w("\n4. ACCOUNT SIZE DISTRIBUTION")
    size_counts = Counter(r["account_size"] for r in normalized)
    for size, cnt in sorted(size_counts.items()):
        w(f"   {cnt:>4}  ${size:>10,}")

    # ── 5. Fee Analysis ──
    w("\n5. FEE ANALYSIS")
    fees = [r["fee_original"] for r in normalized if r["fee_original"] is not None]
    if fees:
        w(f"   Range:   ${min(fees):,.2f} – ${max(fees):,.2f}")
        w(f"   Mean:    ${sum(fees)/len(fees):,.2f}")
        w(f"   Median:  ${sorted(fees)[len(fees)//2]:,.2f}")
    eur = sum(1 for r in normalized if r["currency"] == "EUR")
    usd = sum(1 for r in normalized if r["currency"] == "USD")
    w(f"   USD prices: {usd}  |  EUR prices: {eur}")

    # ── 6. Drawdown Types ──
    w("\n6. DRAWDOWN TYPE DISTRIBUTION")
    dd_counts = Counter(r["drawdown_type"] or "NULL" for r in normalized)
    for dd, cnt in dd_counts.most_common():
        w(f"   {cnt:>4}  {dd}")

    # ── 7. Max Loss Types ──
    w("\n7. MAX LOSS TYPE DISTRIBUTION")
    ml_counts = Counter(r["max_loss_type"] or "NULL" for r in normalized)
    for ml, cnt in ml_counts.most_common():
        w(f"   {cnt:>4}  {ml}")

    # ── 8. Profit Split ──
    w("\n8. PROFIT SPLIT DISTRIBUTION")
    ps_counts = Counter(r["profit_split_pct"] for r in normalized if r["profit_split_pct"])
    for ps, cnt in sorted(ps_counts.items()):
        w(f"   {cnt:>4}  {ps}%")

    # ── 9. Payout Timing ──
    w("\n9. PAYOUT DAYS (parsed)")
    pd_counts = Counter(r["payout_days"] for r in normalized)
    for pd_val, cnt in sorted((k, v) for k, v in pd_counts.items() if k is not None):
        w(f"   {cnt:>4}  {pd_val} days")
    unparsed = pd_counts.get(None, 0)
    w(f"   {unparsed:>4}  (could not parse)")

    # ── 10. Trading Rules Coverage ──
    w("\n10. TRADING RULES COVERAGE")
    bool_fields = ["news_trading", "copy_trading", "eas_allowed",
                    "weekend_holding", "overnight_holding", "refundable_fee"]
    for f in bool_fields:
        has = sum(1 for r in normalized if r[f] is not None)
        true_ct = sum(1 for r in normalized if r[f] == 1)
        false_ct = sum(1 for r in normalized if r[f] == 0)
        w(f"   {f:<22} available={has:>3}  true={true_ct:>3}  false={false_ct:>3}")

    # ── 11. Platform Coverage ──
    w("\n11. PLATFORM COVERAGE")
    plat_counter = Counter()
    for r in normalized:
        if r["platforms"]:
            for p in r["platforms"].split(", "):
                plat_counter[p] += 1
    for plat, cnt in plat_counter.most_common():
        w(f"   {cnt:>4}  {plat}")
    no_plat = sum(1 for r in normalized if not r["platforms"])
    w(f"   {no_plat:>4}  (no platform data)")

    noisy_platform_rows = [r for r in normalized if r["platforms_raw"] and not r["platforms"]]
    if noisy_platform_rows:
        w(f"   {len(noisy_platform_rows):>4}  rows had raw platform text but no canonical platform match")

    # ── 12. Leverage Coverage ──
    w("\n12. LEVERAGE COVERAGE")
    has_lev = sum(1 for r in normalized if r["leverage_eval"])
    w(f"   Rows with leverage data: {has_lev}/{len(normalized)} ({has_lev*100/len(normalized):.1f}%)")

    # ── 13. Allocation Data ──
    w("\n13. ALLOCATION DATA")
    has_alloc = sum(1 for r in normalized if r["max_alloc_per_challenge"] is not None)
    w(f"   Rows with per-challenge alloc: {has_alloc}/{len(normalized)}")
    allocs = [r["max_alloc_per_challenge"] for r in normalized if r["max_alloc_per_challenge"]]
    if allocs:
        w(f"   Range: ${min(allocs):,.0f} – ${max(allocs):,.0f}")

    # ── 14. Field Completeness ──
    w("\n14. FIELD COMPLETENESS MATRIX")
    all_fields = list(normalized[0].keys())
    for f in sorted(all_fields):
        filled = sum(1 for r in normalized if r.get(f) is not None)
        pct = filled * 100 / len(normalized)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        w(f"   {f:<30} {filled:>4}/{len(normalized)}  {pct:>5.1f}%  {bar}")

    # ── 15. Potential Data Issues ──
    w("\n15. POTENTIAL DATA ISSUES")
    # check for suspiciously low fees
    low_fees = [(r["firm"], r["account_size"], r["fee_original"])
                for r in normalized if r["fee_original"] and r["fee_original"] < 20]
    if low_fees:
        w(f"   ⚠ {len(low_fees)} challenges with fee < $20:")
        for firm, size, fee in low_fees[:5]:
            w(f"     {firm} ${size:,} → ${fee:.2f}")

    # check fee/account_size ratio
    high_ratio = [(r["firm"], r["account_size"], r["fee_original"],
                   r["fee_original"]/r["account_size"]*100)
                  for r in normalized
                  if r["fee_original"] and r["account_size"]
                  and r["fee_original"]/r["account_size"] > 5]
    if high_ratio:
        w(f"   ⚠ {len(high_ratio)} challenges with fee > 5% of account size:")
        for firm, size, fee, ratio in sorted(high_ratio, key=lambda x: -x[3])[:5]:
            w(f"     {firm} ${size:,} fee=${fee:.2f} ({ratio:.1f}%)")

    # missing profit targets
    no_pt = sum(1 for r in normalized if r["profit_target_phase1"] is None)
    if no_pt:
        w(f"   ⚠ {no_pt} challenges with no profit target data")

    # 0 or negative drawdown
    bad_dd = sum(1 for r in normalized if r["max_drawdown_pct"] is not None and r["max_drawdown_pct"] <= 0)
    if bad_dd:
        w(f"   ⚠ {bad_dd} challenges with drawdown ≤ 0%")

    # duplicate program names
    names = [r["program_name"] for r in normalized if r["program_name"]]
    dupes = [n for n, cnt in Counter(names).items() if cnt > 1]
    if dupes:
        w(f"   ⚠ {len(dupes)} duplicate program names:")
        for d in dupes[:10]:
            w(f"     {d}")

    w("\n" + "=" * 80)
    w("  END OF REPORT")
    w("=" * 80)

    return "\n".join(lines)


def save_normalized_csv(normalized: list[dict]) -> None:
    fieldnames = list(normalized[0].keys())
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)


# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    print(f"Loading {INPUT_JSON} ...")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw = data["challenges"]
    print(f"Loaded {len(raw)} raw challenges")

    # Normalize
    normalized = [normalize_challenge(c) for c in raw]
    print(f"Normalized {len(normalized)} challenges")

    # Load into SQLite
    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()
        print(f"Removed old DB: {OUTPUT_DB.name}")

    conn = sqlite3.connect(str(OUTPUT_DB))
    cur = conn.cursor()
    cur.execute(CREATE_TABLE)

    for row in normalized:
        cur.execute(INSERT_SQL, row)

    conn.commit()
    print(f"Inserted {len(normalized)} rows into {OUTPUT_DB.name}")

    # Create useful views
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_summary AS
        SELECT
            firm,
            canonical_firm,
            steps_label,
            account_size,
            fee_original,
            profit_target_phase1 AS pt1,
            profit_target_phase2 AS pt2,
            daily_drawdown_pct AS dd_daily,
            max_drawdown_pct AS dd_max,
            drawdown_type,
            max_loss_type,
            profit_split_pct,
            payout_days,
            min_trading_days,
            canonical_platforms AS platforms,
            rating,
            reviews,
            country
        FROM challenges
        ORDER BY firm, steps_label, account_size;
    """)

    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_model_input AS
        SELECT
            id,
            firm,
            canonical_firm,
            program_name,
            account_size,
            steps,
            steps_label,
            fee_original AS fee,
            profit_target_phase1,
            profit_target_phase2,
            profit_target_phase3,
            daily_drawdown_pct,
            max_drawdown_pct,
            drawdown_type,
            max_loss_type,
            profit_split_pct,
            payout_days,
            min_trading_days,
            leverage_eval,
            leverage_funded,
            activation_fee,
            reset_fee,
            news_trading,
            copy_trading,
            eas_allowed,
            canonical_platforms,
            max_alloc_per_challenge,
            total_max_allocation,
            refundable_fee
        FROM challenges
        WHERE panel_scraped = 1
        ORDER BY firm, steps, account_size;
    """)

    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_firm_overview AS
        SELECT
            firm,
            canonical_firm,
            COUNT(*) AS challenge_count,
            GROUP_CONCAT(DISTINCT steps_label) AS step_types,
            MIN(account_size) AS min_size,
            MAX(account_size) AS max_size,
            MIN(fee_original) AS min_fee,
            MAX(fee_original) AS max_fee,
            ROUND(AVG(profit_split_pct), 1) AS avg_profit_split,
            ROUND(AVG(rating), 2) AS avg_rating,
            MAX(reviews) AS max_reviews,
            country
        FROM challenges
        GROUP BY firm, canonical_firm
        ORDER BY challenge_count DESC;
    """)

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM challenges")
    count = cur.fetchone()[0]
    print(f"Verified: {count} rows in DB")

    cur.execute("SELECT COUNT(*) FROM v_model_input")
    model_count = cur.fetchone()[0]
    print(f"Model-ready rows (with panel data): {model_count}")

    # Quick sample
    print("\n── Sample from v_firm_overview ──")
    cur.execute("SELECT * FROM v_firm_overview LIMIT 10")
    cols = [d[0] for d in cur.description]
    print("  " + " | ".join(cols))
    print("  " + "-" * 120)
    for row in cur.fetchall():
        print("  " + " | ".join(str(v) for v in row))

    conn.close()

    save_normalized_csv(normalized)
    print(f"Normalized CSV saved to {OUTPUT_CSV.name}")

    # Generate report
    report = generate_report(raw, normalized)
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to {REPORT_TXT.name}")
    print(report)


if __name__ == "__main__":
    if INPUT_JSON is None:
        raise FileNotFoundError(f"No propmatch_challenges_*.json found in {BASE}")
    main()
