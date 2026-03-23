# Dashboard Layout

> Standard layout for Hedge Edge analytics dashboards.

## Primary Dashboard — Business Overview

| Section | Metrics | Source |
|---------|---------|--------|
| Revenue | MRR, Net New MRR, ARR, Churn Rate | Creem.io via `hourly_metrics_sync.py` |
| Acquisition | New sign-ups, CAC, Conversion Rate | Supabase + GA4 |
| Email | Open Rate, Click Rate, Delivery Rate | Resend → Notion |
| Website | Sessions, Visitors, Bounce Rate, Top Pages | GA4 |
| Funnel | Stage-by-stage conversion rates | All sources |

## Department Dashboards

Each department has a Notion dashboard view filtered to their domain:
- **GROWTH**: Email campaigns, lead pipeline, social metrics
- **FINANCE**: MRR waterfall, IB commissions, P&L summary
- **STRATEGY**: KPI scorecard, competitive intel, roadmap progress
- **ORCHESTRATOR**: System health, cron status, error rates
