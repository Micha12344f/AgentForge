# PropFirm Consolidated Cross-Asset Analysis — Directive

## Purpose

This directive governs the consolidated hedge model analysis that spans all three Hedge Edge asset classes (CFD/Forex challenges, Futures challenges, and Instant-Funded accounts). It defines how to run, interpret, and maintain the unified analysis pipeline.

---

## Scope

Seven hedge model variants are operated in parallel:

| Model | Asset Class | EV Column |
|-------|-------------|-----------|
| Type A — Challenge Insurance | CFD/Forex | `EV` |
| Type B — Funded Recovery | CFD/Forex | `ev_b` |
| Type C — Funded Surplus | CFD/Forex | `ev_c` |
| Type A — Challenge Insurance | Futures | `EV` |
| Type B — Funded Recovery | Futures | `ev_b` |
| Type C — Funded Surplus | Futures | `ev_c` |
| First-Payout Model | Instant-Funded | `EV` |

---

## Data Sources

| File Pattern | Asset Class | How to Refresh |
|-------------|-------------|----------------|
| `propmatch_challenges_{date}.json` | CFD/Forex + Instant-Funded | `propmatch_scraper.py --action scrape-challenges` |
| `propmatch_futures_{date}.json` | Futures | `propmatch_scraper.py --action scrape-futures` |

Always use the **latest file by modification time** — the analysis scripts use `glob + max(mtime)` automatically.

---

## Model Architecture

### Type A — Challenge Insurance (all asset classes)
- Deterministic hedge: insured base = challenge fee
- Hedge sized so account drawdown = hedge profit
- For **trailing** DD: insured base compounds with each daily resize
- For **static** DD: costs are linear
- EV = funded_payout - total_cost
- Best use: single-attempt assessment with no funded continuation

### Type B — Funded Recovery
- Extends Type A into the funded phase
- Funded hedge sized to recover full accumulated cost stack on failure
- Each funded cycle: trader withdraws 4% account x split; hedge drags 1.5% account
- Survival probability: 80% per cycle over 6 cycles
- EV_B = Sum(withdrawals) - Sum(drag)
- Best use: when the funded account will be actively managed

### Type C — Funded Surplus
- Extends Type B with a surplus buffer (default 2% of account)
- Hedge covers cost stack + surplus: on failure recovers both
- Drag scales proportionally by (L+P)/L
- EV_C = Sum(withdrawals) + Sum(expected_surplus) - Sum(drag)
- Best use: when additional downside recovery on funded failure is desired

### Instant-Funded First-Payout
- Single-phase model: no evaluation hedge, trades from day 1
- Target: 5% first payout; consistency rules drive minimum trading days
- Capital: (peak_hedge_notional / 100) x 1.5
- Best use: firms offering instant-funded accounts without evaluation

---

## Parameter Defaults

### CFD/Forex
| Parameter | Default | Notes |
|-----------|---------|-------|
| Funded target | 8% | Type A single-payout |
| Spread cost | 3 pips (0.03%) | Round-trip per trade |
| Trailing resizes | 20 per phase | Daily at even intervals |
| Withdrawal per cycle | 4% | Applied to account x split |
| Funded cycles | 6 | Type B/C horizon |
| Survival rate | 80% | Per funded cycle |
| Hedge drag | 1.5% per cycle | As % of account |
| Surplus target | 2% | Type C only |

### Futures
| Parameter | Default | Notes |
|-----------|---------|-------|
| Funded target | 6% | Lower due to payout caps |
| Spread | $5 round-trip | Per mini contract |
| Consistency threshold | 20% | Default if unspecified |
| Withdrawal / cycle | 4% | Same as FX |
| Funded cycles | 6 | Same as FX |
| Survival rate | 80% | Same as FX |
| Hedge drag | 1.5% | Same as FX |
| Surplus target | 2% | Type C only |

### Instant-Funded
| Parameter | Default | Notes |
|-----------|---------|-------|
| First payout target | 5% | |
| Spread | 3 pips | |
| Base trading days | 5 | Min before payout |
| Leverage | 100x | For capital calc |
| Unspecified DD treatment | Static | Conservative assumption |

---

## Running the Consolidated Report

```bash
# From workspace root with venv activated:
python Business/STRATEGY/resources/PropFirmData/consolidated_report.py
```

Output:
- `HedgeEdge_Consolidated_Report_{date}.pdf` — full multi-section PDF with 12 charts
- `_charts/` — individual PNG charts (persisted for re-use)

The script auto-detects the latest JSON files for each asset class. No flags needed.

---

## Report Structure (27+ pages)

1. Cover page with data summary
2. Table of Contents
3. Executive Summary (key stats, best EV per model)
4. Cross-Asset Overview (EV boxplot, Top 25 table, positive EV rates, firm heatmap)
5. CFD/Forex Deep Dive (Type A/B/C rankings, A vs B vs C comparison)
6. Futures Deep Dive (Type A/B/C rankings, payout cap analysis)
7. Instant-Funded Deep Dive
8. Statistical Analysis (by account size, fee-EV, drawdown type, profit split, capital efficiency)
9. Key Findings & Recommendations
10. Appendices (methodology, parameters)

---

## Key Decision Rules

1. **Prefer Type B** when capital supports the funded phase -- it consistently outperforms Type A
2. **Avoid trailing-DD challenges** unless EV is significantly higher than static alternatives
3. **Filter Futures by payout cap** -- caps below $2,000 severely limit EV
4. **Use Instant-Funded** for capital-light, quick-cycle opportunities
5. **Minimum bar**: only target challenges where EV > $50 (reduces noise)
6. **Always sort by `capital_efficiency`** as a secondary sort for equal EVs

---

## Refresh Cadence

| Action | Frequency |
|--------|-----------|
| Re-scrape FX challenges | Weekly |
| Re-scrape Futures | Weekly |
| Re-run all notebooks | After each scrape |
| Re-generate consolidated PDF | After notebooks complete |
| Archive old JSON files | Monthly |

---

## File Index (resources/PropFirmData/)

| File | Purpose |
|------|---------|
| `type_a_challenge_insurance.ipynb` | FX Type A interactive model |
| `type_b_funded_recovery.ipynb` | FX Type B interactive model |
| `type_c_funded_surplus.ipynb` | FX Type C interactive model |
| `type_a_futures_insurance.ipynb` | Futures Type A interactive model |
| `type_b_futures_recovery.ipynb` | Futures Type B interactive model |
| `type_c_futures_surplus.ipynb` | Futures Type C interactive model |
| `instant_funded_hedge_model.ipynb` | Instant-funded first-payout model |
| `futures_hedge_model.ipynb` | General futures reference notebook |
| `consolidated_report.py` | Script that runs all 7 models and exports PDF |
| `HedgeEdge_Consolidated_Report_*.pdf` | Latest generated PDF report |
| `_charts/*.png` | Individual chart exports from consolidated run |
| `propmatch_challenges_*.json` | Latest scraped FX/CFD challenge data |
| `propmatch_futures_*.json` | Latest scraped futures challenge data |
| `instant_funded_hedge_model_*.json` | Cached instant-funded model outputs |
