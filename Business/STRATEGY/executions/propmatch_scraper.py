#!/usr/bin/env python3
"""
PropMatch Scraper v2 — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Comprehensive scraper for propfirmmatch.com.
Extracts FX challenges, Futures, firm details, and rules.

Actions:
  --action scrape-challenges   FX challenge table (all steps + pagination)
  --action scrape-futures      Futures challenge table
  --action scrape-firms        Firm detail pages (leverage, rules, variants)
  --action scrape-rules        Prop firm rules pages
  --action scrape-all          All scrapers in sequence

Flags:
  --login        Pause for manual Google login before scraping
  --max-pages N  Max pages per filter combo (default: 10)

Usage:
  python propmatch_scraper.py --action scrape-all --login
  python propmatch_scraper.py --action scrape-challenges
  python propmatch_scraper.py --action scrape-futures
  python propmatch_scraper.py --action scrape-firms --input propmatch_challenges_*.json
  python propmatch_scraper.py --action scrape-rules
"""

import sys, os, json, csv, argparse, re, time, glob
from datetime import datetime, timezone
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from shared.notion_client import log_task

AGENT = "Strategy"
WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DATA_DIR = os.path.join(WORKSPACE, 'Business', 'STRATEGY', 'resources', 'PropFirmData')
PROFILE_DIR = os.path.join(WORKSPACE, 'tmp', 'pw_profile_scraper')

BASE_URL = "https://propfirmmatch.com"
CHALLENGES_URL = f"{BASE_URL}/prop-firm-challenges"
FUTURES_URL = f"{BASE_URL}/futures/prop-firm-challenges"
RULES_URL = f"{BASE_URL}/prop-firm-rules"

STEP_TYPES = ["1_Step", "2_Steps", "3_Steps", "Instant"]
FUTURES_ACCOUNT_SIZES = [25000, 50000, 75000, 100000, 150000, 200000, 250000, 300000]
MAX_PAGES_DEFAULT = 10
PAGE_DELAY = 2.0


# ──────────────────────────────────────────────
# Parse helpers
# ──────────────────────────────────────────────

def _pf(text: str) -> float | None:
    """Extract first number from text."""
    if not text:
        return None
    m = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    return float(m.group()) if m else None


def _pi(text: str) -> int | None:
    """Extract first integer from text."""
    if not text:
        return None
    m = re.search(r'\d+', text.replace(',', ''))
    return int(m.group()) if m else None


def _parse_targets(text: str) -> list[float]:
    """Parse '8% 5%' or '$3,000' into list of target values."""
    # Dollar amounts (futures use absolute targets)
    dollars = re.findall(r'\$[\d,]+(?:\.\d+)?', text)
    if dollars:
        return [float(d.replace('$', '').replace(',', '')) for d in dollars]
    # Percentage targets
    return [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)%', text)]


def _parse_fee(text: str) -> tuple[float | None, float | None, str]:
    """Parse fee text. Returns (discounted, original, currency)."""
    currency = "EUR" if "€" in text else "USD"
    amounts = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
    amounts = [float(a) for a in amounts]
    if len(amounts) >= 2:
        return amounts[0], amounts[1], currency
    elif len(amounts) == 1:
        return amounts[0], amounts[0], currency
    return None, None, currency


def _parse_size(text: str) -> int | None:
    """Parse '100K' or '$100,000' into integer."""
    text = text.strip().upper()
    m = re.search(r'(\d+)K', text)
    if m:
        return int(m.group(1)) * 1000
    m = re.search(r'[\d,]+', text.replace(',', ''))
    if m:
        val = int(m.group())
        return val * 1000 if val < 1000 else val
    return None


def _parse_contract_size(text: str) -> dict:
    """Parse '4 | 40' into {minis: 4, micros: 40}."""
    parts = re.findall(r'\d+', text)
    if len(parts) >= 2:
        return {"minis": int(parts[0]), "micros": int(parts[1])}
    elif len(parts) == 1:
        return {"minis": int(parts[0]), "micros": None}
    return {"minis": None, "micros": None}


def _parse_consistency(text: str) -> dict:
    """Parse 'None | 35%' or '50% | None' into {eval: x, funded: y}."""
    parts = text.split('|') if '|' in text else text.split('/')
    if len(parts) >= 2:
        eval_val = parts[0].strip()
        funded_val = parts[1].strip()
    else:
        eval_val = funded_val = text.strip()
    return {"eval": eval_val, "funded": funded_val}


# ──────────────────────────────────────────────
# Browser management
# ──────────────────────────────────────────────

def _launch_browser(pw):
    """Launch Chromium with persistent profile for login state."""
    os.makedirs(PROFILE_DIR, exist_ok=True)
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=False,
        args=['--disable-blink-features=AutomationControlled'],
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page = ctx.new_page()
    page.add_init_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    )
    return ctx, page


def _wait_table(page, timeout=30000):
    """Wait for table to fully render (skeleton loaders gone + rows present)."""
    # 1. Wait for any skeleton loaders to disappear
    try:
        page.wait_for_function(
            'document.querySelectorAll(".animate-pulse").length === 0',
            timeout=timeout,
        )
    except:
        pass
    # 2. Wait for actual table rows to render (the real gate)
    try:
        page.wait_for_selector("table tbody tr", state="attached", timeout=timeout)
    except:
        pass
    time.sleep(PAGE_DELAY)


def _goto(page, url: str, timeout: int = 60000):
    """Navigate robustly — tolerate aborts and timeouts, then wait for table."""
    try:
        page.goto(url, wait_until="load", timeout=timeout)
    except Exception as e:
        err = str(e)
        if "ERR_ABORTED" not in err and "Timeout" not in err:
            raise
    _wait_table(page)


def _is_logged_in(page) -> bool:
    """Check if user is logged into PropFirmMatch."""
    if "auth.propfirmmatch.com" in page.url:
        return False
    for sel in ['a:has-text("Log in")', 'button:has-text("Log in")']:
        if page.query_selector(sel):
            return False
    for sel in [
        'button:has-text("Customize")',
        'button:has-text("Custom")',
        'a[href*="/account"]',
        'button:has-text("My Account")',
    ]:
        if page.query_selector(sel):
            return True
    return False


def _prompt_login(page):
    """Open login modal, wait for user to complete Google sign-in."""
    _goto(page, CHALLENGES_URL)

    login_btn = None
    for sel in ['a:has-text("Log in")', 'button:has-text("Log in")']:
        login_btn = page.query_selector(sel)
        if login_btn:
            break
    if login_btn:
        login_btn.click()
        time.sleep(2)

    print("\n" + "=" * 60)
    print("  ⚠️  LOG IN WITH GOOGLE IN THE BROWSER WINDOW NOW!")
    print("  Waiting on PropFirmMatch for up to 180 seconds ...")
    print("=" * 60)

    for i in range(90):
        time.sleep(2)
        if "propfirmmatch.com" not in page.url:
            continue
        if _is_logged_in(page):
            print("  ✅ Login detected!")
            return True
        if i % 10 == 0 and i > 0:
            print(f"    ... waiting ({i*2}s)")

    print("  ⏰ Timeout — proceeding without login")
    return False


def _setup_custom_columns(page) -> list[str]:
    """Enable Drawdown Type column via Customize Table. Returns new header list."""
    customize_btn = None
    for sel in [
        'button:has-text("Customize")',
        'button:has-text("Custom")',
        'button:has-text("Columns")',
        'button[aria-haspopup="dialog"]:right-of(:text("Steps"))',
        'button[aria-haspopup="dialog"]:near(:text("Filter"))',
    ]:
        try:
            customize_btn = page.query_selector(sel)
            if customize_btn:
                break
        except:
            pass
    if not customize_btn:
        print("    ⚠ Customize button not found")
        return []

    customize_btn.click()
    time.sleep(2)

    # Toggle Drawdown Type ON
    toggled = []
    for col_name in ["Drawdown Type", "Platforms"]:
        for sel in [
            f'div:has-text("{col_name}") >> [role="switch"]',
            f'label:has-text("{col_name}") >> [role="switch"]',
        ]:
            try:
                el = page.query_selector(sel)
                if el:
                    state = el.get_attribute("data-state") or el.get_attribute("aria-checked") or ""
                    if state != "checked" and state != "true":
                        el.click()
                        time.sleep(0.3)
                        toggled.append(col_name)
                    break
            except:
                pass

    # Click Apply
    for sel in ['button:has-text("Apply")', 'button:has-text("Save")', 'button:has-text("Done")']:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                time.sleep(2)
                _wait_table(page)
                break
        except:
            pass
    else:
        page.keyboard.press("Escape")
        time.sleep(1)

    if toggled:
        print(f"    ✓ Enabled custom columns: {toggled}")
    return toggled


def _disable_discounts(page) -> bool:
    """Best-effort attempt to disable any site discount toggle before scraping."""
    discount_labels = [
        "Discount",
        "Discounts",
        "Promo",
        "Promos",
        "Coupon",
        "Coupons",
    ]

    def _switch_on(el) -> bool:
        state = (el.get_attribute("data-state") or "").lower()
        aria = (el.get_attribute("aria-checked") or "").lower()
        checked = (el.get_attribute("checked") or "").lower()
        return state in {"checked", "on", "true"} or aria == "true" or checked == "checked"

    def _button_on(el) -> bool:
        pressed = (el.get_attribute("aria-pressed") or "").lower()
        state = (el.get_attribute("data-state") or "").lower()
        cls = (el.get_attribute("class") or "").lower()
        return pressed == "true" or state in {"checked", "on", "active", "true"} or "active" in cls

    toggled = False
    selectors = []
    for label in discount_labels:
        selectors.extend([
            f'[role="switch"]:near(:text("{label}"))',
            f'div:has-text("{label}") >> [role="switch"]',
            f'label:has-text("{label}") >> [role="switch"]',
            f'input[type="checkbox"]:near(:text("{label}"))',
            f'button:has-text("{label}")',
        ])

    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if not el:
                continue
            role = (el.get_attribute("role") or "").lower()
            tag = (el.evaluate("el => el.tagName") or "").lower()
            should_click = False
            if role == "switch":
                should_click = _switch_on(el)
            elif tag == "input":
                should_click = bool(el.is_checked())
            elif tag == "button":
                should_click = _button_on(el)
            if should_click:
                el.scroll_into_view_if_needed()
                el.click(timeout=5000)
                time.sleep(1)
                toggled = True
                print(f"    ✓ Disabled discount toggle via {sel}")
                break
        except:
            pass

    if not toggled:
        print("    • No discount toggle found; using original price field from table data")
    return toggled


# ──────────────────────────────────────────────
# Column detection & row parsing
# ──────────────────────────────────────────────

def _build_col_map(headers: list[str]) -> dict[str, int]:
    """Build a normalized column map from table headers."""
    col_map = {}
    for i, h in enumerate(headers):
        h_up = " ".join(h.replace('\n', ' ').split()).upper()
        if "FIRM" in h_up and "RANK" in h_up:
            col_map["firm"] = i
        elif h_up == "ACCOUNT SIZE":
            col_map["account_size"] = i
        elif h_up == "STEPS":
            col_map["steps"] = i
        elif "PROFIT TARGET" in h_up:
            col_map["profit_target"] = i
        elif "DAILY" in h_up and "LOSS" in h_up:
            col_map["daily_loss"] = i
        elif "MAX LOSS TYPE" in h_up:
            col_map["max_loss_type"] = i
        elif "MAX LOSS" in h_up and "TYPE" not in h_up:
            col_map["max_loss"] = i
        elif "PT" in h_up and "DD" in h_up:
            col_map["pt_dd"] = i
        elif "PROFIT SPLIT" in h_up:
            col_map["profit_split"] = i
        elif "MAX PAYOUT" in h_up:
            col_map["max_payout"] = i
        elif "MIN PAYOUT" in h_up:
            col_map["min_payout_threshold"] = i
        elif "PAYOUT FREQ" in h_up:
            col_map["payout_freq"] = i
        elif "LOYALTY" in h_up:
            col_map["loyalty_pts"] = i
        elif "DRAWDOWN" in h_up:
            col_map["drawdown_type"] = i
        elif "PLATFORM" in h_up:
            col_map["platforms"] = i
        elif "PRICE" in h_up:
            col_map["price"] = i
        elif "ACTIVATION" in h_up:
            col_map["activation_fee"] = i
        elif "CONTRACT SIZE" in h_up:
            col_map["max_contract_size"] = i
        elif "CONSISTENCY" in h_up:
            col_map["consistency_rule"] = i
    return col_map

def _detect_columns(page):
    """Find the main comparison table and return (table_el, headers, col_map)."""
    best_table = None
    best_headers = []
    best_map = {}

    for table in page.query_selector_all("table"):
        headers = []
        for th in table.query_selector_all("th"):
            try:
                headers.append(th.inner_text().strip())
            except:
                headers.append("")

        col_map = _build_col_map(headers)
        if "firm" in col_map and "price" in col_map:
            return table, headers, col_map
        if len(col_map) > len(best_map):
            best_table = table
            best_headers = headers
            best_map = col_map

    return best_table, best_headers, best_map


def _cell_text(cells, col_map, key) -> str:
    """Get cell text by column name, or empty string if not found."""
    idx = col_map.get(key)
    if idx is not None and idx < len(cells):
        try:
            return cells[idx].inner_text().strip()
        except:
            pass
    return ""


def _get_firm_slug(cells, col_map) -> str | None:
    """Extract firm page slug from the firm cell link."""
    idx = col_map.get("firm", 0)
    if idx < len(cells):
        link = cells[idx].query_selector('a[href*="/prop-firms/"]')
        if link:
            href = link.get_attribute("href") or ""
            return href.rstrip('/').split('/')[-1]
    return None


def _parse_firm_cell(text: str) -> tuple[str, float | None, int | None]:
    """Parse firm cell text into (name, rating, review_count)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = ""
    rating = None
    reviews = None
    for line in lines:
        if re.match(r'^\d+\.\d+$', line):
            rating = float(line)
        elif re.match(r'^\d+$', line):
            reviews = int(line)
        elif not name and len(line) > 1:
            name = line
    return name, rating, reviews


def _parse_table_row(cells, col_map, asset_class: str = "forex") -> dict | None:
    """Parse a single table row into a challenge dict using the column map."""
    firm_text = _cell_text(cells, col_map, "firm")
    name, rating, reviews = _parse_firm_cell(firm_text)
    if not name:
        return None

    slug = _get_firm_slug(cells, col_map)

    size_text = _cell_text(cells, col_map, "account_size")
    targets_text = _cell_text(cells, col_map, "profit_target")
    fee_text = _cell_text(cells, col_map, "price")
    fee_disc, fee_orig, currency = _parse_fee(fee_text)
    fee_assumed = fee_orig or fee_disc

    profit_targets = _parse_targets(targets_text)
    steps_text = _cell_text(cells, col_map, "steps")
    steps_val = _pi(steps_text)
    if not steps_val and "instant" in steps_text.lower():
        steps_val = 0

    challenge = {
        "firm": name,
        "firm_slug": slug,
        "rating": rating,
        "reviews": reviews,
        "account_size": _parse_size(size_text),
        "steps": steps_val or len(profit_targets) or 1,
        "steps_label": steps_text,
        "profit_targets": profit_targets,
        "daily_drawdown_pct": _pf(_cell_text(cells, col_map, "daily_loss")),
        "max_drawdown_pct": _pf(_cell_text(cells, col_map, "max_loss")),
        "pt_dd_ratio": _cell_text(cells, col_map, "pt_dd") or None,
        "profit_split_pct": _pf(_cell_text(cells, col_map, "profit_split")),
        "payout_timing": _cell_text(cells, col_map, "payout_freq") or None,
        "fee_discounted": fee_disc,
        "fee_original": fee_orig,
        "fee_assumed": fee_assumed,
        "fee_assumption": "original_no_discount" if fee_orig else "discounted_only_available",
        "currency": currency,
        "asset_class": asset_class,
    }

    # Optional columns (custom table or futures-specific)
    dd_type = _cell_text(cells, col_map, "drawdown_type")
    if dd_type:
        challenge["drawdown_type"] = dd_type

    platforms = _cell_text(cells, col_map, "platforms")
    if platforms:
        challenge["platforms"] = platforms

    # Futures-specific columns
    act_fee = _cell_text(cells, col_map, "activation_fee")
    if act_fee:
        challenge["activation_fee"] = act_fee

    contract = _cell_text(cells, col_map, "max_contract_size")
    if contract:
        challenge["max_contract_size"] = _parse_contract_size(contract)

    loss_type = _cell_text(cells, col_map, "max_loss_type")
    if loss_type:
        challenge["max_loss_type"] = loss_type

    max_payout = _cell_text(cells, col_map, "max_payout")
    if max_payout:
        challenge["max_payout_amount"] = max_payout

    min_payout = _cell_text(cells, col_map, "min_payout_threshold")
    if min_payout:
        challenge["min_payout_threshold"] = min_payout

    consistency = _cell_text(cells, col_map, "consistency_rule")
    if consistency:
        challenge["consistency_rule"] = _parse_consistency(consistency)

    loyalty = _cell_text(cells, col_map, "loyalty_pts")
    if loyalty:
        challenge["loyalty_pts"] = _pi(loyalty)

    return challenge


# ──────────────────────────────────────────────
# Paginated table scraper (generic)
# ──────────────────────────────────────────────

def _scrape_table_pages(page, base_url: str, max_pages: int, asset_class: str = "forex",
                         reapply_discounts: bool = False) -> list[dict]:
    """Extract all rows using direct URL navigation for pagination."""
    all_rows = []
    seen_page_signatures = set()

    for page_num in range(1, max_pages + 1):
        # Page 1 is already loaded; pages 2+ navigate directly via URL
        if page_num > 1:
            sep = "&" if "?" in base_url else "?"
            page_url = f"{base_url}{sep}page={page_num}"
            try:
                _goto(page, page_url)
            except Exception as e:
                print(f"    Page {page_num}: navigation failed ({e}), stopping")
                break
            if reapply_discounts:
                _disable_discounts(page)

        table_el, headers, col_map = _detect_columns(page)
        if not table_el or not col_map:
            if page_num == 1:
                print("    ⚠ No table headers detected")
            else:
                print(f"    Page {page_num}: no table found, stopping")
            break

        row_els = table_el.query_selector_all("tbody tr")
        if not row_els:
            break

        # Duplicate page detection
        signature_parts = []
        for row_el in row_els[:3]:
            try:
                signature_parts.append(" | ".join(
                    td.inner_text().strip()[:40] for td in row_el.query_selector_all("td")[:4]
                ))
            except:
                pass
        page_signature = "\n".join(signature_parts)
        if page_signature and page_signature in seen_page_signatures:
            print(f"    Page {page_num}: duplicate of prior page, stopping")
            break
        if page_signature:
            seen_page_signatures.add(page_signature)

        count = 0
        for row_el in row_els:
            cells = row_el.query_selector_all("td")
            if len(cells) < 5:
                continue
            parsed = _parse_table_row(cells, col_map, asset_class)
            if parsed and parsed.get("firm"):
                all_rows.append(parsed)
                count += 1

        print(f"    Page {page_num}: {count} challenges")

        if count < 10 or page_num >= max_pages:
            break

    return all_rows


# ──────────────────────────────────────────────
# FX Challenge Scraper
# ──────────────────────────────────────────────

def _scrape_fx_challenges(page, max_pages: int, login: bool) -> list[dict]:
    """Scrape FX challenges across all step types with pagination."""
    print(f"\n{'─' * 50}")
    print(f"  📊 FX CHALLENGE SCRAPER")
    print(f"{'─' * 50}")

    # Navigate to challenges page
    _goto(page, CHALLENGES_URL)

    # Handle login
    logged_in = _is_logged_in(page)
    if login:
        logged_in = _prompt_login(page)
        if logged_in:
            _goto(page, CHALLENGES_URL)

    # Enable custom columns if logged in
    if logged_in:
        print("  Logged in — enabling custom columns ...")
        _setup_custom_columns(page)
        _disable_discounts(page)
        _wait_table(page)
    else:
        print("  Not logged in — using default columns (no Drawdown Type)")

    all_challenges = []

    for step_type in STEP_TYPES:
        step_label = step_type.replace("_", " ")
        print(f"\n  ── {step_label} ──")

        # Navigate with filter
        filters = {"program": [step_type]}
        filter_json = json.dumps(filters, separators=(',', ':'))
        url = f"{CHALLENGES_URL}?filters={quote(filter_json)}"

        try:
            _goto(page, url)
            if logged_in:
                _disable_discounts(page)
        except Exception as e:
            print(f"    ⚠ Failed to load {step_label}: {e}")
            continue

        rows = _scrape_table_pages(page, url, max_pages, "forex",
                                   reapply_discounts=logged_in)
        print(f"    → {len(rows)} challenges for {step_label}")
        all_challenges.extend(rows)

    # Deduplicate: (firm, steps_label, account_size)
    seen = set()
    unique = []
    for c in all_challenges:
        key = (c["firm"], c.get("steps_label", ""), c.get("account_size", 0))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    deduped = len(all_challenges) - len(unique)
    if deduped:
        print(f"\n  Removed {deduped} duplicates")

    print(f"\n  ✅ Total FX challenges: {len(unique)}")
    return unique


# ──────────────────────────────────────────────
# Futures Scraper
# ──────────────────────────────────────────────

def _scrape_futures(page, max_pages: int) -> list[dict]:
    """Scrape futures challenge table across all account sizes."""
    print(f"\n{'─' * 50}")
    print(f"  📊 FUTURES CHALLENGE SCRAPER")
    print(f"{'─' * 50}")

    _goto(page, FUTURES_URL)
    _disable_discounts(page)

    all_challenges = []

    for size in FUTURES_ACCOUNT_SIZES:
        size_label = f"${size // 1000}K"
        print(f"\n  ── {size_label} ──")

        filters = {"accountSize": [size]}
        filter_json = json.dumps(filters, separators=(',', ':'))
        url = f"{FUTURES_URL}?filters={quote(filter_json)}"

        try:
            _goto(page, url)
            _disable_discounts(page)
        except Exception as e:
            print(f"    ⚠ Failed to load {size_label}: {e}")
            continue

        rows = _scrape_table_pages(page, url, max_pages, "futures",
                                   reapply_discounts=True)
        print(f"    → {len(rows)} challenges for {size_label}")
        all_challenges.extend(rows)

    # Deduplicate
    seen = set()
    unique = []
    for c in all_challenges:
        key = (c["firm"], c.get("steps_label", ""), c.get("account_size", 0))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    deduped = len(all_challenges) - len(unique)
    if deduped:
        print(f"\n  Removed {deduped} duplicates")

    print(f"\n  ✅ Total Futures challenges: {len(unique)}")
    return unique


# ──────────────────────────────────────────────
# Firm Detail Scraper
# ──────────────────────────────────────────────

def _scrape_firm_page(page, slug: str) -> dict | None:
    """Visit a firm detail page and extract structured data."""
    url = f"{BASE_URL}/prop-firms/{slug}"
    try:
        _goto(page, url)
    except:
        return None

    body = page.query_selector("body")
    if not body:
        return None

    full_text = body.inner_text()

    result = {"slug": slug, "url": url}

    # ── Leverage table ──
    leverage = {}
    tables = page.query_selector_all("table")
    for table in tables:
        headers = [th.inner_text().strip() for th in table.query_selector_all("th")]
        if "Assets" in headers or "assets" in [h.lower() for h in headers]:
            rows = table.query_selector_all("tbody tr")
            for row in rows:
                cells = [td.inner_text().strip() for td in row.query_selector_all("td")]
                if cells and len(cells) >= 2:
                    asset = cells[0]
                    lev_by_program = {}
                    for i, h in enumerate(headers[1:], 1):
                        if i < len(cells):
                            lev_by_program[h] = cells[i] if cells[i] != "n/a" else None
                    leverage[asset] = lev_by_program
            break
    result["leverage"] = leverage

    # ── Challenge variants ──
    variants = []
    # Look for challenge entries: "Firm - Program - Steps Size $price $orig_price"
    pattern = re.compile(
        r'^(.+?)\s*[-–]\s*(.+?)\s*[-–]\s*(\d+[-\s]?Step[s]?|Instant)\s+'
        r'(?:\*?\s*)?(\d+K?)\s+'
        r'\$?([\d,.]+)\s+\$?([\d,.]+)',
        re.MULTILINE
    )
    for m in pattern.finditer(full_text):
        variants.append({
            "firm": m.group(1).strip(),
            "program": m.group(2).strip(),
            "steps_label": m.group(3).strip(),
            "size_label": m.group(4).strip(),
            "price_discounted": float(m.group(5).replace(',', '')),
            "price_original": float(m.group(6).replace(',', '')),
        })
    result["challenge_variants"] = variants

    # ── Key text sections ──
    sections = {}
    for section_name in [
        "Consistency Rules", "Firm Rules", "Payout Policy",
        "Commissions", "Restricted Countries",
    ]:
        idx = full_text.find(section_name)
        if idx != -1:
            # Extract text from section header to next major section
            chunk = full_text[idx:idx + 2000]
            # Trim at next section header
            for next_section in ["Consistency Rules", "Firm Rules", "Payout Policy",
                                 "Commissions", "Restricted Countries", "Challenges",
                                 "Announcements", "Reviews"]:
                if next_section != section_name:
                    cut = chunk.find(next_section, len(section_name) + 1)
                    if cut > 0:
                        chunk = chunk[:cut]
            sections[section_name.lower().replace(' ', '_')] = chunk.strip()[:1500]

    result["sections"] = sections
    return result


def _scrape_firms(page, slugs: list[str]) -> list[dict]:
    """Scrape firm detail pages for a list of slugs."""
    print(f"\n{'─' * 50}")
    print(f"  🏢 FIRM DETAIL SCRAPER ({len(slugs)} firms)")
    print(f"{'─' * 50}")

    firms = []
    for i, slug in enumerate(slugs, 1):
        print(f"  [{i}/{len(slugs)}] {slug} ...", end=" ", flush=True)
        data = _scrape_firm_page(page, slug)
        if data:
            firms.append(data)
            n_vars = len(data.get("challenge_variants", []))
            n_lev = len(data.get("leverage", {}))
            print(f"✓ ({n_vars} variants, {n_lev} leverage rows)")
        else:
            print("✗")
        time.sleep(1)

    print(f"\n  ✅ Scraped {len(firms)} firm detail pages")
    return firms


# ──────────────────────────────────────────────
# Rules Scraper
# ──────────────────────────────────────────────

def _scrape_rules(page, max_pages: int = 4) -> list[dict]:
    """Scrape prop firm rules pages."""
    print(f"\n{'─' * 50}")
    print(f"  📜 RULES SCRAPER")
    print(f"{'─' * 50}")

    all_rules = []

    for page_num in range(1, max_pages + 1):
        url = f"{RULES_URL}?page={page_num}#table-scroll-target"
        try:
            _goto(page, url)
        except:
            break

        # Click all "Read More" buttons to expand cards
        read_more_btns = page.query_selector_all('button:has-text("Read More")')
        for btn in read_more_btns:
            try:
                btn.click()
                time.sleep(0.3)
            except:
                pass

        # Parse each firm card
        # Rules page uses cards/divs, not a table. Look for firm entries.
        body_text = page.query_selector("body").inner_text()

        # Split by firm names — look for patterns like "FirmName\n4.3\n956\n20% OFF"
        # For now, store raw page text keyed by page number
        all_rules.append({
            "page": page_num,
            "text": body_text[:10000],
        })
        print(f"  Page {page_num}: scraped")

    print(f"\n  ✅ Scraped {len(all_rules)} rules pages")
    return all_rules


# ──────────────────────────────────────────────
# Save helpers
# ──────────────────────────────────────────────

def _save_json(data, prefix: str, ts: str) -> str:
    """Save data as JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{prefix}_{ts}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def _save_csv(challenges: list[dict], prefix: str, ts: str) -> str:
    """Save challenges as flat CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{prefix}_{ts}.csv")
    if not challenges:
        return path

    flat = []
    for c in challenges:
        row = dict(c)
        row["profit_targets"] = " / ".join(
            f"{t}%" if t < 100 else f"${t:,.0f}" for t in (c.get("profit_targets") or [])
        )
        # Flatten nested dicts
        for k, v in list(row.items()):
            if isinstance(v, dict):
                row[k] = json.dumps(v)
        flat.append(row)

    fieldnames = list(flat[0].keys())
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat)
    return path


def _enrich_challenges(challenges: list[dict], firms: list[dict]) -> list[dict]:
    """Enrich challenge records with firm detail data (leverage, rules)."""
    firm_by_slug = {f["slug"]: f for f in firms}

    for c in challenges:
        slug = c.get("firm_slug")
        if not slug or slug not in firm_by_slug:
            continue

        firm = firm_by_slug[slug]

        # Add leverage for FX (use the matching step program)
        lev = firm.get("leverage", {})
        if lev and "FX" in lev:
            fx_lev = lev["FX"]
            # Try to match by steps label
            steps_label = c.get("steps_label", "")
            for prog_name, lev_val in fx_lev.items():
                if prog_name.lower().replace("-", " ") in steps_label.lower().replace("-", " "):
                    c["leverage"] = lev_val
                    break
            else:
                # Use first available leverage
                vals = [v for v in fx_lev.values() if v]
                if vals:
                    c["leverage"] = vals[0]

        # Add consistency rule from firm sections
        sections = firm.get("sections", {})
        cr = sections.get("consistency_rules", "")
        if cr:
            c["consistency_rule_text"] = cr[:200]

    return challenges


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_scrape_challenges(args):
    """Scrape FX challenge data."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx, page = _launch_browser(pw)
        challenges = _scrape_fx_challenges(page, args.max_pages, args.login)
        ctx.close()

    if not challenges:
        print("\n  ⚠ No challenges scraped.")
        log_task(AGENT, "propmatch-scrape-challenges", "Failed", "P2", "No FX challenges extracted")
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com",
        "type": "fx_challenges",
        "total_challenges": len(challenges),
        "challenges": challenges,
    }
    json_path = _save_json(payload, "propmatch_challenges", ts)
    csv_path = _save_csv(challenges, "propmatch_challenges", ts)

    sizes = sorted(set(c.get("account_size", 0) for c in challenges if c.get("account_size")))
    steps = sorted(set(c.get("steps_label", "") for c in challenges))
    has_dd = any(c.get("drawdown_type") for c in challenges)

    print(f"\n{'=' * 60}")
    print(f"  ✅ FX Challenges Scraped")
    print(f"     Count:         {len(challenges)}")
    print(f"     Sizes:         {sizes}")
    print(f"     Steps:         {steps}")
    print(f"     Drawdown Type: {'✓' if has_dd else '✗ (login required)'}")
    print(f"     JSON:          {os.path.basename(json_path)}")
    print(f"     CSV:           {os.path.basename(csv_path)}")
    print(f"{'=' * 60}")
    log_task(AGENT, "propmatch-scrape-challenges", "Complete", "P2",
             f"{len(challenges)} FX challenges → {os.path.basename(json_path)}")


def action_scrape_futures(args):
    """Scrape Futures challenge data."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx, page = _launch_browser(pw)
        futures = _scrape_futures(page, args.max_pages)
        ctx.close()

    if not futures:
        print("\n  ⚠ No futures challenges scraped.")
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com",
        "type": "futures_challenges",
        "total_challenges": len(futures),
        "challenges": futures,
    }
    json_path = _save_json(payload, "propmatch_futures", ts)
    csv_path = _save_csv(futures, "propmatch_futures", ts)

    print(f"\n{'=' * 60}")
    print(f"  ✅ Futures Challenges: {len(futures)}")
    print(f"     JSON: {os.path.basename(json_path)}")
    print(f"     CSV:  {os.path.basename(csv_path)}")
    print(f"{'=' * 60}")
    log_task(AGENT, "propmatch-scrape-futures", "Complete", "P2",
             f"{len(futures)} futures challenges → {os.path.basename(json_path)}")


def action_scrape_firms(args):
    """Scrape firm detail pages. Requires prior challenge data for slugs."""
    # Get slugs from most recent challenge data
    pattern = os.path.join(DATA_DIR, "propmatch_challenges_*.json")
    files = glob.glob(pattern)
    if args.input:
        src = args.input
    elif files:
        src = max(files, key=os.path.getmtime)
    else:
        print("  ⚠ No challenge data found. Run scrape-challenges first.")
        return

    with open(src, 'r', encoding='utf-8') as f:
        data = json.load(f)
    challenges = data.get("challenges", [])
    slugs = list(set(c.get("firm_slug") for c in challenges if c.get("firm_slug")))
    slugs.sort()

    if not slugs:
        print("  ⚠ No firm slugs in challenge data.")
        return

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx, page = _launch_browser(pw)
        firms = _scrape_firms(page, slugs)
        ctx.close()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com",
        "type": "firm_details",
        "total_firms": len(firms),
        "firms": firms,
    }
    json_path = _save_json(payload, "propmatch_firms", ts)

    print(f"\n{'=' * 60}")
    print(f"  ✅ Firm Details: {len(firms)}")
    print(f"     JSON: {os.path.basename(json_path)}")
    print(f"{'=' * 60}")
    log_task(AGENT, "propmatch-scrape-firms", "Complete", "P3",
             f"{len(firms)} firm details → {os.path.basename(json_path)}")


def action_scrape_rules(args):
    """Scrape prop firm rules."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx, page = _launch_browser(pw)
        rules = _scrape_rules(page, max_pages=4)
        ctx.close()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com/prop-firm-rules",
        "type": "rules",
        "rules": rules,
    }
    json_path = _save_json(payload, "propmatch_rules", ts)

    print(f"\n  ✅ Rules scraped → {os.path.basename(json_path)}")
    log_task(AGENT, "propmatch-scrape-rules", "Complete", "P3",
             f"Rules scraped → {os.path.basename(json_path)}")


def action_scrape_all(args):
    """Run all scrapers and produce enriched output."""
    from playwright.sync_api import sync_playwright
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    with sync_playwright() as pw:
        ctx, page = _launch_browser(pw)

        # 1. FX Challenges
        fx = _scrape_fx_challenges(page, args.max_pages, args.login)

        # 2. Futures
        futures = _scrape_futures(page, args.max_pages)

        # 3. Firm details (using slugs from FX challenges)
        slugs = list(set(c.get("firm_slug") for c in fx if c.get("firm_slug")))
        # Also add futures slugs
        slugs += [c.get("firm_slug") for c in futures if c.get("firm_slug") and c.get("firm_slug") not in slugs]
        slugs = sorted(set(s for s in slugs if s))

        firms = _scrape_firms(page, slugs) if slugs else []

        # 4. Rules
        rules = _scrape_rules(page)

        ctx.close()

    # Enrich FX challenges with firm data
    if firms:
        fx = _enrich_challenges(fx, firms)

    # Save FX challenges
    fx_payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com",
        "type": "fx_challenges",
        "total_challenges": len(fx),
        "challenges": fx,
    }
    fx_json = _save_json(fx_payload, "propmatch_challenges", ts)
    fx_csv = _save_csv(fx, "propmatch_challenges", ts)

    # Save Futures
    fut_payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "propfirmmatch.com",
        "type": "futures_challenges",
        "total_challenges": len(futures),
        "challenges": futures,
    }
    fut_json = _save_json(fut_payload, "propmatch_futures", ts)
    _save_csv(futures, "propmatch_futures", ts)

    # Save Firms
    firms_payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "type": "firm_details",
        "total_firms": len(firms),
        "firms": firms,
    }
    _save_json(firms_payload, "propmatch_firms", ts)

    # Save Rules
    _save_json({
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "type": "rules",
        "rules": rules,
    }, "propmatch_rules", ts)

    # Summary
    has_dd = any(c.get("drawdown_type") for c in fx)
    has_lev = any(c.get("leverage") for c in fx)

    print(f"\n{'=' * 60}")
    print(f"  ✅ FULL SCRAPE COMPLETE")
    print(f"     FX Challenges:   {len(fx)}")
    print(f"     Futures:         {len(futures)}")
    print(f"     Firm Details:    {len(firms)}")
    print(f"     Rules Pages:     {len(rules)}")
    print(f"     Drawdown Type:   {'✓' if has_dd else '✗'}")
    print(f"     Leverage:        {'✓' if has_lev else '✗'}")
    print(f"     Output:          {os.path.basename(fx_json)}")
    print(f"{'=' * 60}")

    log_task(AGENT, "propmatch-scrape-all", "Complete", "P2",
             f"Full scrape: {len(fx)} FX + {len(futures)} futures + {len(firms)} firms")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

ACTIONS = {
    "scrape-challenges": action_scrape_challenges,
    "scrape-futures": action_scrape_futures,
    "scrape-firms": action_scrape_firms,
    "scrape-rules": action_scrape_rules,
    "scrape-all": action_scrape_all,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PropMatch Scraper v2 — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--login", action="store_true",
                        help="Pause for manual Google login")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES_DEFAULT,
                        help=f"Max pages per filter combo (default: {MAX_PAGES_DEFAULT})")
    parser.add_argument("--input", default=None,
                        help="Input JSON file (for scrape-firms)")
    args = parser.parse_args()
    ACTIONS[args.action](args)
