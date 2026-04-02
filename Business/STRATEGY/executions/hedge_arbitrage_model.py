#!/usr/bin/env python3
"""
Hedge Arbitrage Model — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deterministic hedge economics for prop firm challenges.

The hedge guarantees you pass every challenge phase. This model calculates
the cost of that guarantee and how much you need to earn once funded to profit.

  EV = (profit_split × funded_target) − (challenge_fee + total_hedge_losses)
  Break-even payout = total_cost / profit_split

Actions:
  --action model     Compute hedge economics for all challenges in a JSON file
  --action compare   Generate a ranked comparison matrix
  --action full      End-to-end: scrape → model → compare → report

Usage:
  python hedge_arbitrage_model.py --action model --input propmatch_challenges_20260323.json
  python hedge_arbitrage_model.py --action model --input propmatch_challenges_20260323.json --funded-target 0.10
  python hedge_arbitrage_model.py --action compare --input propmatch_challenges_20260323.json --size 100000
  python hedge_arbitrage_model.py --action full --sizes 100000
"""

import sys, os, json, argparse, math, glob, sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.notion_client import log_task

AGENT = "Strategy"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'resources', 'PropFirmData')

# ── Default assumptions ──────────────────────
DEFAULT_FUNDED_TARGET_PCT = 0.08  # 8% of funded account — user-adjustable
DEFAULT_SPREAD_COST_PCT = 0.0003  # ~3 pips per side as fraction of position
DEFAULT_LEVERAGE = 100            # 1:100 default leverage on personal broker
DEFAULT_REVIEW_PRIOR_RATING = 4.274
DEFAULT_REVIEW_PRIOR_WEIGHT = 100
DEFAULT_REVIEW_FACTOR_FLOOR = 0.70
DEFAULT_REVIEW_FACTOR_CEILING = 1.00
DEFAULT_REVIEW_MISSING_CAP = 0.82
DEFAULT_REVIEW_COUNT_REFERENCE = 2000
DEFAULT_REVIEW_COUNT_WEIGHT = 0.65


# ──────────────────────────────────────────────
# Math engine
# ──────────────────────────────────────────────

def _parse_leverage_ratio(lev_str: str | None) -> float:
    """Convert '1:100' or '1:0.77' to the numeric part after the colon."""
    if not lev_str:
        return DEFAULT_LEVERAGE
    parts = lev_str.split(':')
    if len(parts) == 2:
        try:
            return float(parts[1])
        except ValueError:
            pass
    return DEFAULT_LEVERAGE


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def compute_review_adjustment(challenge: dict) -> dict:
    """Convert firm review data into a funded-payout reliability haircut."""
    rating = challenge.get("rating")
    reviews = challenge.get("reviews")

    try:
        rating = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None

    try:
        reviews = int(reviews) if reviews is not None else None
    except (TypeError, ValueError):
        reviews = None

    prior_rating = float(challenge.get("_review_prior_rating", DEFAULT_REVIEW_PRIOR_RATING))
    prior_weight = float(challenge.get("_review_prior_weight", DEFAULT_REVIEW_PRIOR_WEIGHT))
    count_reference = float(challenge.get("_review_count_reference", DEFAULT_REVIEW_COUNT_REFERENCE))
    count_weight = float(challenge.get("_review_count_weight", DEFAULT_REVIEW_COUNT_WEIGHT))
    count_weight = _clamp(count_weight, 0.0, 1.0)

    if rating is None or reviews is None or reviews <= 0:
        bayesian_rating = prior_rating
        confidence = 0.0
        count_score = 0.0
        source = "prior_only"
    else:
        bayesian_rating = ((reviews * rating) + (prior_weight * prior_rating)) / (reviews + prior_weight)
        confidence = reviews / (reviews + prior_weight)
        count_score = _clamp(math.log1p(reviews) / math.log1p(max(count_reference, 1.0)), 0.0, 1.0)
        source = "rating_and_reviews"

    normalized_rating = _clamp((bayesian_rating - 3.8) / (4.6 - 3.8), 0.0, 1.0)
    composite_score = ((1.0 - count_weight) * normalized_rating) + (count_weight * count_score)
    review_factor = DEFAULT_REVIEW_FACTOR_FLOOR + (
        (DEFAULT_REVIEW_FACTOR_CEILING - DEFAULT_REVIEW_FACTOR_FLOOR) * composite_score
    )
    if source == "prior_only":
        review_factor = min(review_factor, DEFAULT_REVIEW_MISSING_CAP)

    return {
        "review_rating": rating,
        "review_count": reviews,
        "review_bayesian_rating": round(bayesian_rating, 4),
        "review_rating_score": round(normalized_rating, 4),
        "review_count_score": round(count_score, 4),
        "review_composite_score": round(composite_score, 4),
        "review_confidence": round(confidence, 4),
        "review_factor": round(review_factor, 4),
        "review_factor_source": source,
    }


def _ranking_key(result: dict) -> tuple[float, float, float, float]:
    return (
        result.get("EV_review_adj", float("-inf")),
        result.get("EV", float("-inf")),
        result.get("review_factor", 0.0),
        result.get("capital_efficiency_review_adj", float("-inf")),
    )


def compute_phase_economics(
    challenge: dict,
    funded_target_pct: float = DEFAULT_FUNDED_TARGET_PCT,
    spread_cost_pct: float = DEFAULT_SPREAD_COST_PCT,
) -> dict:
    """Compute deterministic hedge economics for a prop firm challenge.

    The hedge guarantees you pass every phase (it's arbitrage).
    When you pass, the hedge loses money — that's the cost of the guarantee.
    Once funded, you need to earn enough to cover all accumulated costs.

    Walk Phase 1 → Phase 2 → Funded:
      - Each phase, the hedge is sized so a drawdown recovers your insured base
      - You always pass → hedge loss accumulates into the cost stack
      - EV = profit_split × funded_target - total_cost
      - Break-even = total_cost / profit_split
    """
    S = challenge.get("account_size", 0)
    fee = (
        challenge.get("fee_assumed")
        or challenge.get("fee_original")
        or challenge.get("fee_discounted")
        or 0
    )
    targets = challenge.get("profit_targets") or []
    steps = challenge.get("steps") or len(targets) or 2
    dd_max_pct = (challenge.get("max_drawdown_pct") or 10.0) / 100.0
    split = (challenge.get("profit_split_pct") or 80.0) / 100.0
    leverage = _parse_leverage_ratio(challenge.get("leverage"))

    trades_per_phase = 20

    # Per-phase profit targets
    if targets:
        phase_targets = [t / 100.0 for t in targets]
    else:
        phase_targets = [0.08 / steps] * steps

    # ── Walk through each phase (you always pass) ──
    # L = cumulative cost stack (insured base)
    # Starts at the challenge fee
    L = fee
    phases = []

    for phase_idx in range(steps):
        phase_target = phase_targets[phase_idx] if phase_idx < len(phase_targets) else phase_targets[-1]

        # Hedge sizing: sized so drawdown recovers insured base
        #   hedge_size × dd_max_pct = L  →  hedge_size = L / dd_max_pct
        hedge_size = L / dd_max_pct if dd_max_pct > 0 else 0

        # Spread/friction cost
        c_phase = hedge_size * spread_cost_pct * 2 * trades_per_phase

        # You PASS (always) → hedge loses money
        hedge_loss = hedge_size * phase_target + c_phase

        # Cost stack grows
        L_after_pass = L + hedge_loss

        # Fail recovery (safety net — what you'd get back if drawdown hit)
        fail_recovery = L - c_phase

        # Capital required for this phase's hedge
        margin = hedge_size / leverage
        buffer = hedge_size * dd_max_pct * 1.5
        capital_for_phase = margin + buffer

        phases.append({
            "phase": phase_idx + 1,
            "phase_target_pct": round(phase_target * 100, 2),
            "insured_base": round(L, 2),
            "hedge_size": round(hedge_size, 2),
            "spread_cost": round(c_phase, 2),
            "hedge_loss_if_pass": round(hedge_loss, 2),
            "fail_recovery": round(fail_recovery, 2),
            "loss_stack_after_pass": round(L_after_pass, 2),
            "capital_required": round(capital_for_phase, 2),
        })

        L = L_after_pass

    # ── After all phases: FUNDED ──
    total_cost = L  # fee + all accumulated hedge losses
    funded_payout = S * funded_target_pct * split
    EV = funded_payout - total_cost
    review_adjustment = compute_review_adjustment(challenge)
    funded_payout_review_adj = funded_payout * review_adjustment["review_factor"]
    EV_review_adj = funded_payout_review_adj - total_cost

    # Break-even: profit_split × X = total_cost  →  X = total_cost / profit_split
    breakeven_payout = total_cost / split if split > 0 else 0
    breakeven_pct = (breakeven_payout / S) * 100 if S > 0 else 0
    breakeven_payout_review_adj = total_cost / (split * review_adjustment["review_factor"]) if split > 0 and review_adjustment["review_factor"] > 0 else 0
    breakeven_pct_review_adj = (breakeven_payout_review_adj / S) * 100 if S > 0 else 0

    # Capital
    capital_required = max(ph["capital_required"] for ph in phases) if phases else 0
    max_hedge_size = max(ph["hedge_size"] for ph in phases) if phases else 0

    # Efficiency
    capital_efficiency = EV / capital_required if capital_required > 0 else 0
    cost_efficiency = EV / fee if fee > 0 else 0
    capital_efficiency_review_adj = EV_review_adj / capital_required if capital_required > 0 else 0
    cost_efficiency_review_adj = EV_review_adj / fee if fee > 0 else 0

    return {
        "firm": challenge.get("firm"),
        "account_size": S,
        "fee": round(fee, 2),
        "steps": steps,
        "profit_split_pct": round(split * 100, 1),
        "max_drawdown_pct": round(dd_max_pct * 100, 2),
        "leverage": leverage,
        "funded_target_pct": round(funded_target_pct * 100, 2),
        "phases": phases,
        "total_cost": round(total_cost, 2),
        "funded_payout": round(funded_payout, 2),
        "funded_payout_review_adj": round(funded_payout_review_adj, 2),
        "EV": round(EV, 2),
        "EV_review_adj": round(EV_review_adj, 2),
        "breakeven_payout": round(breakeven_payout, 2),
        "breakeven_pct": round(breakeven_pct, 2),
        "breakeven_payout_review_adj": round(breakeven_payout_review_adj, 2),
        "breakeven_pct_review_adj": round(breakeven_pct_review_adj, 2),
        "max_hedge_size": round(max_hedge_size, 2),
        "capital_required": round(capital_required, 2),
        "capital_efficiency": round(capital_efficiency, 4),
        "cost_efficiency": round(cost_efficiency, 4),
        "capital_efficiency_review_adj": round(capital_efficiency_review_adj, 4),
        "cost_efficiency_review_adj": round(cost_efficiency_review_adj, 4),
        **review_adjustment,
    }


def compute_funded_target_sensitivity(
    challenge: dict,
    spread_cost_pct: float = DEFAULT_SPREAD_COST_PCT,
) -> dict:
    """Sweep funded_target_pct from 1% to 20% to show EV sensitivity.

    The model is deterministic (you always pass). The key question:
    how much do you need to earn funded to make it worthwhile?
    """
    sweep = []
    breakeven_target = None

    for pct_int in range(1, 21):  # 1% to 20%
        target = pct_int / 100.0
        result = compute_phase_economics(
            challenge, funded_target_pct=target,
            spread_cost_pct=spread_cost_pct)
        ev_raw = result["EV"]
        ev_review_adj = result["EV_review_adj"]
        sweep.append({
            "funded_target_pct": pct_int,
            "EV": round(ev_raw, 2),
            "EV_review_adj": round(ev_review_adj, 2),
        })
        if breakeven_target is None and ev_review_adj >= 0:
            breakeven_target = pct_int

    baseline = compute_phase_economics(challenge, spread_cost_pct=spread_cost_pct)

    return {
        "firm": challenge.get("firm"),
        "account_size": challenge.get("account_size"),
        "baseline_ev": round(baseline["EV"], 2),
        "baseline_ev_review_adj": round(baseline["EV_review_adj"], 2),
        "breakeven_target_pct": breakeven_target,
        "sweep": sweep,
    }


# ── Legacy compatibility wrapper ──
def compute_challenge_economics(
    challenge: dict,
    funded_target_pct: float = DEFAULT_FUNDED_TARGET_PCT,
    spread_cost_pct: float = DEFAULT_SPREAD_COST_PCT,
    **kwargs,
) -> dict:
    """Wrapper that calls the core model and maps output for report compatibility."""
    result = compute_phase_economics(
        challenge, funded_target_pct=funded_target_pct,
        spread_cost_pct=spread_cost_pct)

    result["spread_cost_total"] = round(sum(ph["spread_cost"] for ph in result["phases"]), 2)
    return result


# ──────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────

def _find_latest_json(pattern: str = "propmatch_challenges_*.json") -> str | None:
    """Find the most recent challenges JSON in DATA_DIR."""
    files = glob.glob(os.path.join(DATA_DIR, pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def _load_challenges(path: str, view: str = "v_model_inputs", where: str | None = None) -> list[dict]:
    """Load challenges from a JSON file or SQLite database."""
    if path.endswith('.db'):
        return _load_challenges_from_db(path, view=view, where=where)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("challenges", data if isinstance(data, list) else [])


def _load_challenges_from_db(
    db_path: str,
    view: str = "v_model_inputs",
    where: str | None = None,
) -> list[dict]:
    """Load challenges from a SQLite model-input database.

    Reads rows as dicts and JSON-decodes the profit_targets column
    so the result is directly compatible with compute_phase_economics().
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = f"SELECT * FROM {view}"
    if where:
        query += f" WHERE {where}"
    rows = conn.execute(query).fetchall()
    conn.close()

    challenges = []
    for row in rows:
        d = dict(row)
        # JSON-decode profit_targets from text → list[float]
        pt_json = d.pop("profit_targets_json", None) or d.pop("profit_targets", None)
        if isinstance(pt_json, str):
            try:
                d["profit_targets"] = json.loads(pt_json)
            except (json.JSONDecodeError, TypeError):
                d["profit_targets"] = []
        elif isinstance(pt_json, list):
            d["profit_targets"] = pt_json
        else:
            d["profit_targets"] = []
        challenges.append(d)
    return challenges


def _find_latest_db(pattern: str = "propmatch_model_input*.db") -> str | None:
    """Find the most recent model-input DB in DATA_DIR."""
    files = glob.glob(os.path.join(DATA_DIR, pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def _save_model_json(results: list[dict], size: int | None, ts: str) -> str:
    """Save model results as JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    size_tag = f"_{size}" if size else "_all"
    path = os.path.join(DATA_DIR, f"hedge_model{size_tag}_{ts}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "results": results}, f, indent=2)
    return path


def _save_model_report(results: list[dict], size: int | None, ts: str,
                       funded_target_pct: float) -> str:
    """Save model results as markdown report."""
    os.makedirs(DATA_DIR, exist_ok=True)
    size_tag = f"_{size}" if size else "_all"
    path = os.path.join(DATA_DIR, f"hedge_model{size_tag}_{ts}.md")

    size_label = f"${size:,}" if size else "All Sizes"
    lines = [
        f"# Hedge Arbitrage Model — {size_label} Challenges",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"> Funded target: {funded_target_pct*100:.0f}% | Model: deterministic (always pass)",
        "> Ranking: sorted by review-adjusted EV; raw EV retained for reference",
        "",
        "## Summary",
        "",
        f"| # | Firm | Rating | Reviews | Fee | Total Cost | Raw EV | Review Factor | Adj EV | Break-Even Adj | Capital |",
        f"|---|------|--------|---------|-----|------------|--------|---------------|--------|----------------|---------|",
    ]

    for i, r in enumerate(sorted(results, key=_ranking_key, reverse=True), 1):
        lines.append(
            f"| {i} | {r['firm']} | {r['review_rating'] if r['review_rating'] is not None else 'N/A'} "
            f"| {r['review_count'] if r['review_count'] is not None else 'N/A'} "
            f"| ${r['fee']:,.0f} | ${r['total_cost']:,.2f} "
            f"| ${r['EV']:,.2f} | {r['review_factor']:.3f} "
            f"| **${r['EV_review_adj']:,.2f}** | {r['breakeven_pct_review_adj']:.1f}% | ${r['capital_required']:,.0f} |"
        )

    lines.extend(["", "## Per-Challenge Detail", ""])

    for r in sorted(results, key=_ranking_key, reverse=True):
        lines.extend([
            f"### {r['firm']} — ${r['account_size']:,}",
            "",
            f"- **Fee**: ${r['fee']:,.2f}",
            f"- **Phases**: {r.get('steps', 'N/A')}",
            f"- **Max drawdown**: {r['max_drawdown_pct']}%",
            f"- **Profit split**: {r['profit_split_pct']}%",
            f"- **Reviews**: {r['review_rating'] if r['review_rating'] is not None else 'N/A'} stars across {r['review_count'] if r['review_count'] is not None else 'N/A'} reviews",
            f"- **Review factor**: {r['review_factor']:.3f} (Bayesian {r['review_bayesian_rating']:.3f}, confidence {r['review_confidence']:.3f})",
            f"- **Funded target**: {r['funded_target_pct']}% of account",
            f"- **Total cost (fee + hedge losses)**: ${r['total_cost']:,.2f}",
            f"- **Funded payout (after split)**: ${r['funded_payout']:,.2f}",
            f"- **Review-adjusted funded payout**: ${r['funded_payout_review_adj']:,.2f}",
            "",
            "#### Phase-by-Phase Hedge Breakdown",
            "",
            "| Phase | Target | Insured Base | Hedge Size | Friction | Hedge Loss | Stack After |",
            "|-------|--------|-------------|------------|----------|------------|-------------|",
        ])

        for ph in r.get("phases", []):
            lines.append(
                f"| {ph['phase']} | {ph['phase_target_pct']}% "
                f"| ${ph['insured_base']:,.2f} | ${ph['hedge_size']:,.2f} "
                f"| ${ph['spread_cost']:,.2f} | ${ph['hedge_loss_if_pass']:,.2f} "
                f"| ${ph['loss_stack_after_pass']:,.2f} |"
            )

        lines.extend([
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Raw EV | ${r['EV']:,.2f} |",
            f"| Review-adjusted EV | **${r['EV_review_adj']:,.2f}** |",
            f"| Review factor | {r['review_factor']:.4f} ({r['review_factor_source']}) |",
            f"| Total cost | ${r['total_cost']:,.2f} |",
            f"| Funded payout | ${r['funded_payout']:,.2f} |",
            f"| Review-adjusted funded payout | ${r['funded_payout_review_adj']:,.2f} |",
            f"| Break-even payout | ${r['breakeven_payout']:,.2f} ({r['breakeven_pct']:.1f}% of account) |",
            f"| Break-even payout (review-adjusted) | ${r['breakeven_payout_review_adj']:,.2f} ({r['breakeven_pct_review_adj']:.1f}% of account) |",
            f"| Capital required | ${r['capital_required']:,.2f} |",
            f"| Capital efficiency | {r['capital_efficiency']:.4f} |",
            f"| Capital efficiency (review-adjusted) | {r['capital_efficiency_review_adj']:.4f} |",
            f"| Cost efficiency | {r['cost_efficiency']:.4f} |",
            f"| Cost efficiency (review-adjusted) | {r['cost_efficiency_review_adj']:.4f} |",
            "",
        ])

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return path


def _save_comparison_matrix(all_results: list[dict], ts: str) -> tuple[str, str]:
    """Save a combined comparison matrix across all sizes."""
    os.makedirs(DATA_DIR, exist_ok=True)

    md_path = os.path.join(DATA_DIR, f"comparison_matrix_{ts}.md")
    json_path = os.path.join(DATA_DIR, f"comparison_matrix_{ts}.json")

    by_size: dict[int, list[dict]] = {}
    for r in all_results:
        by_size.setdefault(r["account_size"], []).append(r)

    lines = [
        "# Hedge Arbitrage — Comparison Matrix",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "> Ranking: sorted by review-adjusted EV; raw EV retained for reference",
        "",
    ]

    for size in sorted(by_size.keys()):
        items = sorted(by_size[size], key=_ranking_key, reverse=True)
        lines.extend([
            f"## ${size:,} Challenges",
            "",
            "| Rank | Firm | Rating | Reviews | Fee | Total Cost | Raw EV | Review Factor | Adj EV | Break-Even Adj % | Capital | Adj Efficiency |",
            "|------|------|--------|---------|-----|------------|--------|---------------|--------|------------------|---------|----------------|",
        ])
        for i, r in enumerate(items, 1):
            lines.append(
                f"| {i} | {r['firm']} | {r['review_rating'] if r['review_rating'] is not None else 'N/A'} "
                f"| {r['review_count'] if r['review_count'] is not None else 'N/A'} "
                f"| ${r['fee']:,.0f} | ${r['total_cost']:,.2f} | ${r['EV']:,.2f} "
                f"| {r['review_factor']:.3f} | **${r['EV_review_adj']:,.2f}** "
                f"| {r['breakeven_pct_review_adj']:.1f}% "
                f"| ${r['capital_required']:,.0f} | {r['capital_efficiency_review_adj']:.4f} |"
            )
        lines.append("")

    overall = sorted(all_results, key=lambda x: x["capital_efficiency_review_adj"], reverse=True)[:10]
    lines.extend([
        "## Top 10 Overall — By Review-Adjusted Capital Efficiency",
        "",
        "| Rank | Firm | Size | Fee | Raw EV | Adj EV | Capital | Adj Efficiency |",
        "|------|------|------|-----|--------|--------|---------|----------------|",
    ])
    for i, r in enumerate(overall, 1):
        lines.append(
            f"| {i} | {r['firm']} | ${r['account_size']:,} | ${r['fee']:,.0f} "
            f"| ${r['EV']:,.2f} | ${r['EV_review_adj']:,.2f} | ${r['capital_required']:,.0f} "
            f"| **{r['capital_efficiency_review_adj']:.4f}** |"
        )

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "matrix": all_results}, f, indent=2)

    return md_path, json_path


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_model(args) -> None:
    """Compute hedge economics for all challenges."""
    input_path = _resolve_input(args)
    if not input_path:
        return

    db_view = getattr(args, 'db_view', 'v_model_inputs')
    db_where = getattr(args, 'db_where', None)
    if getattr(args, 'include_quarantined', False):
        db_view = 'model_challenges'
    challenges = _load_challenges(input_path, view=db_view, where=db_where)
    if args.size:
        challenges = [c for c in challenges if c.get("account_size") == int(args.size)]

    print(f"\n{'=' * 60}")
    print(f"  📐 HEDGE ARBITRAGE MODEL (Deterministic)")
    print(f"{'=' * 60}")
    print(f"  Input:          {os.path.basename(input_path)}")
    if input_path.endswith('.db'):
        print(f"  Source:         SQLite ({db_view})")
        if db_where:
            print(f"  Filter:         {db_where}")
        if getattr(args, 'include_quarantined', False):
            print(f"  Quarantine:     INCLUDED (all rows)")
        else:
            print(f"  Quarantine:     Active (strict eligibility)")
    print(f"  Challenges:     {len(challenges)}")
    print(f"  Funded target:  {args.funded_target * 100:.0f}%")
    print(f"  Spread:         {args.spread_cost * 100:.2f}% per trade")

    results = []
    for c in challenges:
        econ = compute_challenge_economics(
            c,
            funded_target_pct=args.funded_target,
            spread_cost_pct=args.spread_cost,
        )
        results.append(econ)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    size_val = int(args.size) if args.size else None
    json_path = _save_model_json(results, size_val, ts)
    md_path = _save_model_report(results, size_val, ts, args.funded_target)

    positive_ev = [r for r in results if r["EV"] > 0]
    positive_ev_review_adj = [r for r in results if r["EV_review_adj"] > 0]
    print(f"\n  Results:")
    print(f"    Positive EV (raw):          {len(positive_ev)}/{len(results)} challenges")
    print(f"    Positive EV (review-adj):   {len(positive_ev_review_adj)}/{len(results)} challenges")
    if results:
        best = max(results, key=_ranking_key)
        print(f"    Best adj EV:                {best['firm']} → ${best['EV_review_adj']:,.2f} (raw ${best['EV']:,.2f})")
    print(f"    JSON:        {os.path.basename(json_path)}")
    print(f"    Report:      {os.path.basename(md_path)}")
    print(f"{'=' * 60}")

    log_task(AGENT, "hedge-model", "Complete", "P2",
             f"Modelled {len(results)} challenges, {len(positive_ev_review_adj)} positive review-adjusted EV → {os.path.basename(md_path)}")


def action_compare(args) -> None:
    """Generate a ranked comparison matrix."""
    input_path = _resolve_input(args)
    if not input_path:
        return

    db_view = getattr(args, 'db_view', 'v_model_inputs')
    db_where = getattr(args, 'db_where', None)
    if getattr(args, 'include_quarantined', False):
        db_view = 'model_challenges'
    challenges = _load_challenges(input_path, view=db_view, where=db_where)

    print(f"\n{'=' * 60}")
    print(f"  📊 COMPARISON MATRIX")
    print(f"{'=' * 60}")
    print(f"  Input:      {os.path.basename(input_path)}")
    if input_path.endswith('.db'):
        print(f"  Source:     SQLite ({db_view})")
        if db_where:
            print(f"  Filter:     {db_where}")
    print(f"  Challenges: {len(challenges)}")

    results = []
    for c in challenges:
        econ = compute_challenge_economics(
            c,
            funded_target_pct=args.funded_target,
            spread_cost_pct=args.spread_cost,
        )
        results.append(econ)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    md_path, json_path = _save_comparison_matrix(results, ts)

    sizes_found = sorted(set(r["account_size"] for r in results))
    print(f"\n  ✅ Matrix generated")
    print(f"     Sizes:    {', '.join(f'${s:,}' for s in sizes_found)}")
    print(f"     Markdown: {os.path.basename(md_path)}")
    print(f"     JSON:     {os.path.basename(json_path)}")
    print(f"{'=' * 60}")


def action_full(args) -> None:
    """End-to-end: scrape → model → compare → report."""
    print(f"\n{'=' * 60}")
    print(f"  🚀 FULL PIPELINE: Scrape → Model → Compare")
    print(f"{'=' * 60}")

    # Phase 1: Scrape
    print("\n─── Phase 1: Scraping PropMatch ───")
    from propmatch_scraper import action_scrape as do_scrape

    class ScrapeArgs:
        sizes = args.sizes
        include_rules = args.include_rules

    do_scrape(ScrapeArgs())

    input_path = _find_latest_json()
    if not input_path:
        print("  ✘ Scrape produced no output. Aborting.")
        return

    challenges = _load_challenges(input_path)
    print(f"\n  Loaded {len(challenges)} challenges from {os.path.basename(input_path)}")

    # Phase 2: Model
    print("\n─── Phase 2: Modelling ───")
    results = []
    for c in challenges:
        econ = compute_challenge_economics(
            c,
            funded_target_pct=args.funded_target,
            spread_cost_pct=args.spread_cost,
        )
        results.append(econ)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    sizes = sorted(set(r["account_size"] for r in results))
    for size in sizes:
        size_results = [r for r in results if r["account_size"] == size]
        _save_model_json(size_results, size, ts)
        _save_model_report(size_results, size, ts, args.funded_target)
        positive_review_adj = sum(1 for r in size_results if r["EV_review_adj"] > 0)
        print(f"  ${size:>7,}: {len(size_results)} challenges, {positive_review_adj} positive review-adjusted EV")

    # Phase 3: Compare
    print("\n─── Phase 3: Comparison Matrix ───")
    md_path, json_path = _save_comparison_matrix(results, ts)

    # Phase 4: Funded target sensitivity for top 5
    print("\n─── Phase 4: Funded Target Sensitivity (top 5 by review-adjusted EV) ───")
    top5 = sorted(results, key=_ranking_key, reverse=True)[:5]
    for r in top5:
        orig = next((c for c in challenges
                     if c["firm"] == r["firm"] and c["account_size"] == r["account_size"]), None)
        if orig:
            sens = compute_funded_target_sensitivity(orig, spread_cost_pct=args.spread_cost)
            be_str = f"{sens['breakeven_target_pct']}%" if sens['breakeven_target_pct'] else "N/A"
            print(f"  {sens['firm']} ${sens['account_size']:,}: "
                  f"Adj EV=${sens['baseline_ev_review_adj']:,.2f} (raw ${sens['baseline_ev']:,.2f}), break-even target={be_str}")

    print(f"\n{'=' * 60}")
    print(f"  ✅ Full pipeline complete")
    print(f"     Challenges modelled: {len(results)}")
    print(f"     Matrix: {os.path.basename(md_path)}")
    print(f"{'=' * 60}")

    log_task(AGENT, "hedge-arbitrage-full", "Complete", "P1",
             f"Full pipeline: {len(results)} challenges, {len(sizes)} sizes → {os.path.basename(md_path)}")


def _resolve_input(args) -> str | None:
    """Resolve input path: explicit --db, explicit --input, or auto-detect.

    Priority order:
      1. --db path  (SQLite model-input database)
      2. --input path  (JSON challenges file)
      3. Latest .db in DATA_DIR
      4. Latest .json in DATA_DIR
    """
    # Explicit --db flag
    db_path = getattr(args, 'db', None)
    if db_path:
        # Try as-is first, then resolve relative to DATA_DIR
        if not os.path.isfile(db_path):
            db_path = os.path.join(DATA_DIR, os.path.basename(db_path))
        if not os.path.isfile(db_path):
            print(f"  ✘ DB file not found: {getattr(args, 'db', '')}")
            return None
        return os.path.abspath(db_path)

    # Explicit --input flag
    if args.input:
        path = args.input
        if not os.path.isfile(path):
            path = os.path.join(DATA_DIR, os.path.basename(path))
        if not os.path.isfile(path):
            print(f"  ✘ Input file not found: {path}")
            return None
        return path

    # Auto-detect: prefer DB, fall back to JSON
    latest_db = _find_latest_db()
    if latest_db:
        return latest_db

    latest = _find_latest_json()
    if not latest:
        print("  ✘ No challenge data found in resources/PropFirmData/")
        print("    Run: python propmatch_scraper.py --action scrape")
        print("    Or:  python build_model_input_db.py")
        return None
    return latest


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

ACTIONS = {
    "model": action_model,
    "compare": action_compare,
    "full": action_full,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hedge Arbitrage Model — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys(),
                        help="Action to perform")
    parser.add_argument("--input", default=None,
                        help="Path to propmatch_challenges JSON (default: latest in PropFirmData/)")
    parser.add_argument("--db", default=None,
                        help="Path to propmatch_model_input.db SQLite database (preferred over --input)")
    parser.add_argument("--db-view", default="v_model_inputs", dest="db_view",
                        help="SQLite view/table to query (default: v_model_inputs)")
    parser.add_argument("--db-where", default=None, dest="db_where",
                        help="Optional SQL WHERE clause for DB queries (e.g. \"account_size=100000\")")
    parser.add_argument("--include-quarantined", action="store_true", dest="include_quarantined",
                        help="Include quarantined rows (unknown drawdown type, missing fields)")
    parser.add_argument("--size", default=None,
                        help="Filter to a specific account size (e.g., 100000)")
    parser.add_argument("--sizes", default="10000,25000,50000,100000,200000",
                        help="Account sizes for full pipeline scrape")
    parser.add_argument("--funded-target", type=float, default=DEFAULT_FUNDED_TARGET_PCT,
                        dest="funded_target",
                        help=f"Funded profit target as decimal (default: {DEFAULT_FUNDED_TARGET_PCT})")
    parser.add_argument("--spread-cost", type=float, default=DEFAULT_SPREAD_COST_PCT,
                        dest="spread_cost",
                        help=f"Spread cost per trade as decimal (default: {DEFAULT_SPREAD_COST_PCT})")
    parser.add_argument("--include-rules", action="store_true", dest="include_rules",
                        help="Include rules scrape in full pipeline")

    args = parser.parse_args()
    ACTIONS[args.action](args)
