---
name: futures-hedge-model
description: |
  Hedge arbitrage model for futures prop firm challenges. Accounts for trailing
  drawdown, consistency rules, payout caps, minimum payout thresholds, and
  activation fees — the structural differences that make futures challenges
  a separate modelling domain from FX.
---

# Futures Prop Firm Hedge Model

## Objective

Quantify the economic viability of hedging futures prop firm challenges using
a deterministic insurance model. Futures challenges differ from FX in five
structural ways that change hedge economics:

1. **Trailing drawdown** — the drawdown limit follows the equity high-water mark
2. **Consistency rules** — no single day's profit may exceed X% of total profit
3. **Payout caps** — maximum dollar withdrawal per payout cycle
4. **Minimum payout thresholds** — must accumulate $X before requesting a payout
5. **Activation fees** — some firms charge an additional fee at funding

## When to Use This Skill

- When evaluating futures prop firms for hedge-adjusted profitability
- When comparing futures challenges against FX challenges
- When producing content around Hedge Edge value proposition for futures traders
- When updating the model after scraping new PropFirmMatch futures data
- When a user asks about hedging futures-specific rules

## Execution Rule

Run futures workflows from the terminal only.

```bash
python Business/STRATEGY/executions/propmatch_scraper.py --action scrape-futures
```

Do not execute futures notebooks for live analysis. If a futures variant still exists only as notebook logic, port it into a terminal script before running it.

## Input Specification

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| Data file | JSON | Yes | Scraped futures challenges from `propmatch_scraper.py --action scrape-futures` |
| funded_target_pct | float | No | Funded profit target (default: 0.06 — 6% for futures accounts, typically lower than FX) |
| spread_cost_per_contract | float | No | Round-trip cost per contract in $ (default: $5.00 per mini) |
| consistency_threshold | float | No | Max single-day profit as % of total (default: 0.20 — 20%) |

## Futures Data Schema (from PropFirmMatch)

| Field | Type | Example |
|-------|------|---------|
| firm | string | "Tradeify" |
| account_size | int | 50000 |
| steps | int | 1 |
| activation_fee | float | 0.0 |
| max_contracts_minis | int | 4 |
| max_contracts_micros | int | 40 |
| profit_target | float | 3000.0 |
| max_loss_type | string | "EOD Trailing" |
| max_loss | float | 2000.0 |
| pt_dd_ratio | string | "1:0.67" |
| profit_split_pct | float | 90.0 |
| max_payout_amount | float | 1500.0 |
| min_payout_threshold | float | 3000.0 |
| consistency_rule_eval | string | "None" or "50%" |
| consistency_rule_funded | string | "35%" or "None" |
| payout_freq | string | "5 days with Minimum profits of $150" |
| fee_discounted | float | 97.30 |
| fee_original | float | 139.00 |

## Model Framework

### Key Difference from FX: Trailing Drawdown

In FX static drawdown, the max-loss level is fixed from day 1. If the account starts at $100K with 10% max DD, the account blows at $90K — always.

In futures trailing drawdown, the max-loss level rises with the equity high-water mark. If the account peaks at $103K, the blow-up level moves to $101K (with $2K trailing DD). This means:

- The hedge must be resized every time equity moves
- Hedge losses compound geometrically, not linearly
- Cost of insurance is structurally higher than static DD

### Phase-by-Phase Economics (Trailing DD)

For a 1-step futures eval with fee F, profit target T, and trailing DD of D:

**State variable:** L = insured base (starts at F)

Walk N daily increments (target / N per day):

    For each day:
        hedge_size = L / DD
        daily_target_move = T / N
        hedge_loss = hedge_size × (daily_target_move / account_size)
        spread_loss = contracts × cost_per_contract × 2
        L = L + hedge_loss + spread_loss

After all days: total_cost = L

This compounds because each day's loss raises L, which raises the next day's hedge size.

### Consistency Rule Penalty

The consistency rule does not change the hedge cost — it changes when you can withdraw.

If the rule says no single day > 20% of total profit:

    min_trading_days = ceil(1 / consistency_threshold)
    effective_daily_cap = total_target × consistency_threshold

With a 20% consistency rule, you need at least 5 profitable days.
With a 30% rule, you need at least 4.
With a 50% rule, you need at least 2.

This means:

- Hedging must be spread across at least `min_trading_days` days
- You cannot "one-shot" the target with a single large hedge
- The number of hedge resizes is bounded below by `min_trading_days`

The model adjusts `resizes_per_phase` to be at least `min_trading_days`.

### Payout Cap Penalty

Many futures firms cap each payout cycle:

    cycles_to_recover = ceil(total_cost / payout_cap)
    time_to_recover = cycles_to_recover × payout_frequency_days

This doesn't change EV but extends the capital lockup period and reduces capital efficiency.

### Minimum Payout Threshold

Some firms require a minimum profit before any payout:

    If min_threshold > funded_target × account_size:
        → extra trading days needed at funded before first payout

This delays recovery and increases the funded-phase hedge drag.

### EV Calculation

    funded_payout = min(account_size × funded_target_pct × split, max_payout_amount)
    EV = funded_payout - total_cost - activation_fee

### Break-Even Payout

    breakeven = (total_cost + activation_fee) / split

### Capital Requirements

    For futures: capital = contracts × margin_per_contract × 2
    (margin values differ by exchange — ~$1,000/mini for ES, $500/mini for NQ micro)

## Comparison Metrics

Rank futures challenges by:

| Metric | Formula | Purpose |
|--------|---------|---------|
| EV | funded_payout - total_cost - activation_fee | Absolute profitability |
| Capital efficiency | EV / capital_required | Return on deployed capital |
| Cost efficiency | EV / fee | Return per dollar of challenge fee |
| Payout delay | cycles_to_recover × freq_days | How long until capital recovered |
| Consistency burden | min_trading_days | Operational complexity |

## Execution Scripts

- `executions/propmatch_scraper.py --action scrape-futures` — Futures challenge data
- `resources/PropFirmData/futures_hedge_model.ipynb` — Reference notebook with visualisations only; do not run it for live workflows

## Resources

- `resources/PropFirmData/propmatch_futures_*.json` — Scraped futures challenge data
- `resources/PropFirmMatchExploration/futures_structure.json` — Futures table schema
- `resources/Product/hedging-explained.md` — Hedge mechanics reference

## Definition of Done

- [ ] Futures scraper extracts challenges with all schema fields above
- [ ] Model handles trailing DD compounding correctly
- [ ] Consistency rule adjusts minimum trading days
- [ ] Payout cap and threshold are reflected in capital efficiency
- [ ] Terminal workflow produces comparison table, bar chart, sensitivity sweep
- [ ] At least 1 hand-verified example matches (e.g., Tradeify 50K: fee ~$97, target $3K, DD $2K)
- [ ] Outputs saved to `resources/PropFirmData/`
- [ ] No notebook execution is used for live futures analysis
