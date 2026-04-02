# Lead Qualification

> BANT scoring, MQL→SQL criteria for Hedge Edge leads.

## Qualification Framework (BANT)

| Criterion | Weight | Signals |
|-----------|--------|---------|
| **B**udget | 25% | Active trader, mentions prop firm fees |
| **A**uthority | 25% | Decision maker, not just browsing |
| **N**eed | 25% | Mentions hedging, risk management, prop firm challenge |
| **T**imeline | 25% | Currently trading, immediate need |

## Lead Scoring

| Action | Points |
|--------|--------|
| Sign-up | +10 |
| Beta key claimed | +20 |
| Email opened | +1 each |
| Email clicked | +3 each |
| Email replied | +5 each |
| Demo booked | +30 |
| Visited pricing page | +10 |
| Downloaded guide | +15 |
| Desktop app opened (validation with `platform = desktop`) | +10 |
| **Platform Activated (mt5/mt4/ctrader validation + device)** | **+50 — ULTIMATE CONVERSION** |

> **Platform Activation** is the highest-value single scoring action. It proves the user connected an Expert Advisor to a live trading platform — not just opened the desktop app. A `desktop` or `unknown` validation earns only +10. Only `mt5`, `mt4`, or `ctrader` platform validations with a persistent device row qualify for +50. See `ANALYTICS/directives/platform-activation-indicator.md` for the full definition and confidence tiers.

## MQL Threshold: 30 points
## SQL Threshold: 60 points + BANT ≥ 2/4

> A user with confirmed Platform Activation automatically qualifies as MQL (≥50 points from activation alone + 20 from beta claim = 70).
