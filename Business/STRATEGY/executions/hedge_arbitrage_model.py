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

import sys, os, json, argparse, math, glob
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

    # Break-even: profit_split × X = total_cost  →  X = total_cost / profit_split
    breakeven_payout = total_cost / split if split > 0 else 0
    breakeven_pct = (breakeven_payout / S) * 100 if S > 0 else 0

    # Capital
    capital_required = max(ph["capital_required"] for ph in phases) if phases else 0
    max_hedge_size = max(ph["hedge_size"] for ph in phases) if phases else 0

    # Efficiency
    capital_efficiency = EV / capital_required if capital_required > 0 else 0
    cost_efficiency = EV / fee if fee > 0 else 0

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
        "EV": round(EV, 2),
        "breakeven_payout": round(breakeven_payout, 2),
        "breakeven_pct": round(breakeven_pct, 2),
        "max_hedge_size": round(max_hedge_size, 2),
        "capital_required": round(capital_required, 2),
        "capital_efficiency": round(capital_efficiency, 4),
        "cost_efficiency": round(cost_efficiency, 4),
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
        ev = result["EV"]
        sweep.append({"funded_target_pct": pct_int, "EV": round(ev, 2)})
        if breakeven_target is None and ev >= 0:
            breakeven_target = pct_int

    baseline = compute_phase_economics(challenge, spread_cost_pct=spread_cost_pct)

    return {
        "firm": challenge.get("firm"),
        "account_size": challenge.get("account_size"),
        "baseline_ev": round(baseline["EV"], 2),
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


def _load_challenges(path: str) -> list[dict]:
    """Load challenges from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("challenges", data if isinstance(data, list) else [])


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
        "",
        "## Summary",
        "",
        f"| # | Firm | Fee | Split | DD | Total Cost | Funded Payout | EV | Break-Even | Capital |",
        f"|---|------|-----|-------|-----|------------|---------------|-----|------------|---------|",
    ]

    for i, r in enumerate(sorted(results, key=lambda x: x["EV"], reverse=True), 1):
        lines.append(
            f"| {i} | {r['firm']} | ${r['fee']:,.0f} | {r['profit_split_pct']}% "
            f"| {r['max_drawdown_pct']}% | ${r['total_cost']:,.2f} "
            f"| ${r['funded_payout']:,.2f} | **${r['EV']:,.2f}** "
            f"| {r['breakeven_pct']:.1f}% | ${r['capital_required']:,.0f} |"
        )

    lines.extend(["", "## Per-Challenge Detail", ""])

    for r in sorted(results, key=lambda x: x["EV"], reverse=True):
        lines.extend([
            f"### {r['firm']} — ${r['account_size']:,}",
            "",
            f"- **Fee**: ${r['fee']:,.2f}",
            f"- **Phases**: {r.get('steps', 'N/A')}",
            f"- **Max drawdown**: {r['max_drawdown_pct']}%",
            f"- **Profit split**: {r['profit_split_pct']}%",
            f"- **Funded target**: {r['funded_target_pct']}% of account",
            f"- **Total cost (fee + hedge losses)**: ${r['total_cost']:,.2f}",
            f"- **Funded payout (after split)**: ${r['funded_payout']:,.2f}",
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
            f"| EV | **${r['EV']:,.2f}** |",
            f"| Total cost | ${r['total_cost']:,.2f} |",
            f"| Funded payout | ${r['funded_payout']:,.2f} |",
            f"| Break-even payout | ${r['breakeven_payout']:,.2f} ({r['breakeven_pct']:.1f}% of account) |",
            f"| Capital required | ${r['capital_required']:,.2f} |",
            f"| Capital efficiency | {r['capital_efficiency']:.4f} |",
            f"| Cost efficiency | {r['cost_efficiency']:.4f} |",
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
        "",
    ]

    for size in sorted(by_size.keys()):
        items = sorted(by_size[size], key=lambda x: x["EV"], reverse=True)
        lines.extend([
            f"## ${size:,} Challenges",
            "",
            "| Rank | Firm | Fee | Total Cost | EV | Break-Even % | Capital | Efficiency |",
            "|------|------|-----|------------|-----|-------------|---------|------------|",
        ])
        for i, r in enumerate(items, 1):
            lines.append(
                f"| {i} | {r['firm']} | ${r['fee']:,.0f} "
                f"| ${r['total_cost']:,.2f} | **${r['EV']:,.2f}** "
                f"| {r['breakeven_pct']:.1f}% "
                f"| ${r['capital_required']:,.0f} | {r['capital_efficiency']:.4f} |"
            )
        lines.append("")

    overall = sorted(all_results, key=lambda x: x["capital_efficiency"], reverse=True)[:10]
    lines.extend([
        "## Top 10 Overall — By Capital Efficiency",
        "",
        "| Rank | Firm | Size | Fee | EV | Capital | Efficiency |",
        "|------|------|------|-----|-----|---------|------------|",
    ])
    for i, r in enumerate(overall, 1):
        lines.append(
            f"| {i} | {r['firm']} | ${r['account_size']:,} | ${r['fee']:,.0f} "
            f"| ${r['EV']:,.2f} | ${r['capital_required']:,.0f} "
            f"| **{r['capital_efficiency']:.4f}** |"
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
    """Compute hedge economics for all challenges in a JSON file."""
    input_path = _resolve_input(args)
    if not input_path:
        return

    challenges = _load_challenges(input_path)
    if args.size:
        challenges = [c for c in challenges if c.get("account_size") == int(args.size)]

    print(f"\n{'=' * 60}")
    print(f"  📐 HEDGE ARBITRAGE MODEL (Deterministic)")
    print(f"{'=' * 60}")
    print(f"  Input:          {os.path.basename(input_path)}")
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
    print(f"\n  Results:")
    print(f"    Positive EV: {len(positive_ev)}/{len(results)} challenges")
    if positive_ev:
        best = max(positive_ev, key=lambda x: x["EV"])
        print(f"    Best EV:     {best['firm']} → ${best['EV']:,.2f}")
    print(f"    JSON:        {os.path.basename(json_path)}")
    print(f"    Report:      {os.path.basename(md_path)}")
    print(f"{'=' * 60}")

    log_task(AGENT, "hedge-model", "Complete", "P2",
             f"Modelled {len(results)} challenges, {len(positive_ev)} positive EV → {os.path.basename(md_path)}")


def action_compare(args) -> None:
    """Generate a ranked comparison matrix."""
    input_path = _resolve_input(args)
    if not input_path:
        return

    challenges = _load_challenges(input_path)

    print(f"\n{'=' * 60}")
    print(f"  📊 COMPARISON MATRIX")
    print(f"{'=' * 60}")
    print(f"  Input:      {os.path.basename(input_path)}")
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
        positive = sum(1 for r in size_results if r["EV"] > 0)
        print(f"  ${size:>7,}: {len(size_results)} challenges, {positive} positive EV")

    # Phase 3: Compare
    print("\n─── Phase 3: Comparison Matrix ───")
    md_path, json_path = _save_comparison_matrix(results, ts)

    # Phase 4: Funded target sensitivity for top 5
    print("\n─── Phase 4: Funded Target Sensitivity (top 5 by EV) ───")
    top5 = sorted(results, key=lambda x: x["EV"], reverse=True)[:5]
    for r in top5:
        orig = next((c for c in challenges
                     if c["firm"] == r["firm"] and c["account_size"] == r["account_size"]), None)
        if orig:
            sens = compute_funded_target_sensitivity(orig, spread_cost_pct=args.spread_cost)
            be_str = f"{sens['breakeven_target_pct']}%" if sens['breakeven_target_pct'] else "N/A"
            print(f"  {sens['firm']} ${sens['account_size']:,}: "
                  f"EV=${sens['baseline_ev']:,.2f}, break-even target={be_str}")

    print(f"\n{'=' * 60}")
    print(f"  ✅ Full pipeline complete")
    print(f"     Challenges modelled: {len(results)}")
    print(f"     Matrix: {os.path.basename(md_path)}")
    print(f"{'=' * 60}")

    log_task(AGENT, "hedge-arbitrage-full", "Complete", "P1",
             f"Full pipeline: {len(results)} challenges, {len(sizes)} sizes → {os.path.basename(md_path)}")


def _resolve_input(args) -> str | None:
    """Resolve input path: explicit arg or latest JSON."""
    if args.input:
        path = args.input
        if not os.path.isabs(path):
            path = os.path.join(DATA_DIR, path)
        if not os.path.isfile(path):
            print(f"  ✘ Input file not found: {path}")
            return None
        return path

    latest = _find_latest_json()
    if not latest:
        print("  ✘ No challenge JSON found in resources/PropFirmData/")
        print("    Run: python propmatch_scraper.py --action scrape")
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
