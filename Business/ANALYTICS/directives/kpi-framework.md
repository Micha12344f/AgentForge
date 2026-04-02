# KPI Framework

> Canonical KPI definitions, targets, and alert thresholds for Hedge Edge.

## Source Hierarchy

- **Traffic and engagement**: GA4 first, Supabase `page_views` only as fallback when GA4 is unavailable
- **Signups and attribution**: Supabase `user_attribution`
- **Activation and license health**: Supabase `license_validation_logs` + `license_devices`
- **Email delivery and audience health**: Resend
- **Revenue and subscriptions**: Creem
- **Notion**: mirror/dashboard store only; do not default to Notion snapshots for analytical reports unless the user explicitly asks for mirrored dashboard state

## Core Metrics

| KPI | Definition | Target | Alert Threshold |
|-----|-----------|--------|-----------------|
| MRR | Monthly Recurring Revenue from active subscriptions | Growth ≥10% MoM | Decline >5% |
| CAC | Customer Acquisition Cost | <£50 | >£80 |
| LTV | Lifetime Value per customer | >£500 | <£200 |
| Churn Rate | % subscribers cancelling per month | <5% | >8% |
| Email Open Rate | % delivered emails opened | >25% | <15% |
| Email Click Rate | % delivered emails clicked | >3% | <1% |
| GA4 Sessions | Daily website sessions | >100/day | <30/day |
| Conversion Rate | Visitors → Sign-ups | >3% | <1% |
| **Platform Activation Rate** | **ACTIVATED users / total license holders (see platform-activation-indicator.md)** | **≥60%** | **<30%** |
| **Time-to-Activation** | **Median days from key issuance to first platform (mt5/mt4/ctrader) validation** | **≤3 days** | **>7 days** |
| IB Referrals | New IB-referred accounts per month | Growth trend | Decline 2 months |

## Reporting Cadence

- **Hourly**: `hourly_metrics_sync.py` syncs live data into Notion mirrors for dashboard maintenance
- **Daily**: `daily_analytics.py` updates Notion mirror rows and operational snapshots
- **Daily/Weekly/Monthly analytical reports**: use `executions/strategic_report.py` from direct sources first
- **Weekly dashboard review**: Notion mirrors are acceptable only when the user explicitly wants dashboard-state verification
- **Monthly board-ready narrative**: STRATEGY consumes Analytics direct-source outputs

## Ultimate Conversion Indicator

**Platform Activation** is the single most important conversion metric. A user is only considered converted when they have a confirmed platform validation (`mt5`, `mt4`, or `ctrader`) with a persistent device row — not just a desktop app open or beta key claim. See `directives/platform-activation-indicator.md` for the full definition, confidence tiers, and verification checklist. All KPI reports must include Platform Activation Rate alongside traditional conversion rate.
