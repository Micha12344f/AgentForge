# KPI Framework

> Canonical KPI definitions, targets, and alert thresholds for Hedge Edge.

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
| IB Referrals | New IB-referred accounts per month | Growth trend | Decline 2 months |

## Reporting Cadence

- **Hourly**: `hourly_metrics_sync.py` syncs live data to Notion
- **Daily**: `daily_analytics.py` generates KPI snapshot
- **Weekly**: Aggregated in Notion dashboards
- **Monthly**: Board-ready reports via STRATEGY
