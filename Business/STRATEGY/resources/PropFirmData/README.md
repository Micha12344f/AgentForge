# PropFirmData — Scraped Challenge Data & Hedge Models

This folder stores scraped data, analysis notebooks, and consolidated reports for the Hedge Edge prop-firm hedge analysis framework (Skills 15, 16, 17, 18).

## Skills Covered

| Skill | Scope |
|-------|-------|
| **Skill 15** | CFD/Forex — Type A/B/C challenge + funded hedge models |
| **Skill 16** | Futures — Type A/B/C challenge + funded hedge models |
| **Skill 17** | Instant-Funded first-payout model |
| **Skill 18** | Consolidated cross-asset PDF report (all 7 models) |

## Setup

```bash
pip install playwright fpdf2 nbconvert nbclient nbformat
playwright install chromium
```

## Data Files

| File Pattern | Asset Class | Source |
|-------------|-------------|--------|
| `propmatch_challenges_{date}.json` | CFD/Forex + Instant-Funded | `propmatch_scraper.py --action scrape-challenges` |
| `propmatch_challenges_{date}.csv` | CFD/Forex + Instant-Funded | Same |
| `propmatch_futures_{date}.json` | Futures (76 challenges, 8 sizes) | `propmatch_scraper.py --action scrape-futures` |
| `propmatch_futures_{date}.csv` | Futures | Same |
| `instant_funded_hedge_model_{date}.json` | Instant-Funded | `instant_funded_hedge_model.ipynb` cached output |
| `hedge_model_v3_{date}.json` | CFD/Forex legacy | `hedge_arbitrage_model.py` |

## Analysis Notebooks

### CFD/Forex (Skill 15)
| Notebook | Model | Key Outputs |
|----------|-------|-------------|
| `type_a_challenge_insurance.ipynb` | Type A | EV rankings, DD type comparison, sensitivity sweep, capital efficiency |
| `type_b_funded_recovery.ipynb` | Type B | A vs B EV comparison, funded cycle walkthrough, survival sensitivity |
| `type_c_funded_surplus.ipynb` | Type C | Three-way A/B/C comparison, surplus sensitivity, all-types summary table |

### Futures (Skill 16)
| Notebook | Model | Key Outputs |
|----------|-------|-------------|
| `type_a_futures_insurance.ipynb` | Futures Type A | EV rankings, payout cap impact, cycles-to-recover, capital efficiency |
| `type_b_futures_recovery.ipynb` | Futures Type B | A vs B comparison, survival sensitivity |
| `type_c_futures_surplus.ipynb` | Futures Type C | Three-way A/B/C comparison, surplus target sensitivity |
| `futures_hedge_model.ipynb` | General reference | All-in-one futures reference notebook |

### Instant-Funded (Skill 17)
| Notebook | Model | Key Outputs |
|----------|-------|-------------|
| `instant_funded_hedge_model.ipynb` | First-payout | EV rankings, DD type impact, capital efficiency, consistency sensitivity |

## Consolidated Report (Skill 18)

```bash
# From workspace root with venv activated:
python Business/STRATEGY/resources/PropFirmData/consolidated_report.py
```

| Output | Description |
|--------|-------------|
| `HedgeEdge_Consolidated_Report_{date}.pdf` | 27+ page PDF — all 7 models, 12 charts, executive summary, firm heatmap, recommendations |
| `_charts/*.png` | 12 individual chart PNGs (persisted between runs) |

The script auto-detects the latest JSON files — no flags needed.

## Executing Notebooks (re-run after scrape)

```bash
# Re-execute all six Type A/B/C notebooks:
python -m jupyter nbconvert --to notebook --execute --inplace \
  Business/STRATEGY/resources/PropFirmData/type_a_challenge_insurance.ipynb \
  Business/STRATEGY/resources/PropFirmData/type_b_funded_recovery.ipynb \
  Business/STRATEGY/resources/PropFirmData/type_c_funded_surplus.ipynb \
  Business/STRATEGY/resources/PropFirmData/type_a_futures_insurance.ipynb \
  Business/STRATEGY/resources/PropFirmData/type_b_futures_recovery.ipynb \
  Business/STRATEGY/resources/PropFirmData/type_c_futures_surplus.ipynb
```

## Data Sources

- **FX URL**: `https://propfirmmatch.com/prop-firm-challenges`
- **Futures URL**: `https://propfirmmatch.com/futures/prop-firm-challenges`
- **Instant-funded**: Filtered from FX data where `steps_label = "Instant"`
- **Futures account sizes**: $25K, $50K, $75K, $100K, $150K, $200K, $250K, $300K
- **Refresh cadence**: Weekly recommended

## Related

- Exploration data: `resources/PropFirmMatchExploration/`
- Scraper: `executions/propmatch_scraper.py`
- Hedge model: `executions/hedge_arbitrage_model.py`
