# Funnel Reporting

> Full-funnel conversion reporting from first visit to paying customer.

## Current Operational Funnel Stages

```
Email funnel:   Sent → Delivered → Opened → Clicked → Replied
Signup funnel:  Lead → Demo Booked → Demo Completed → Trial → Paid
```

## Current Data Sources

| Stage Transition | Data Source | Metric |
|-----------------|-------------|--------|
| Sent → Delivered | Notion `email_sends` | Delivery rate |
| Delivered → Opened | Notion `email_sends` | Open rate |
| Opened → Clicked | Notion `email_sends` | Click rate |
| Clicked → Replied | Notion `email_sends` | Reply rate |
| Lead → Demo Booked | Notion `leads_crm` and `demo_log` | Demo-booking rate |
| Demo Booked → Demo Completed | Notion `demo_log` | Show-up rate |
| Demo Completed → Trial | Not yet wired in current execution | Placeholder |
| Trial → Paid | Not yet wired in current execution | Placeholder |

## Current Execution Behavior

- `Business/ANALYTICS/executions/funnel_calculator.py` currently computes the email funnel from `email_sends`.
- The same script computes the signup funnel from `leads_crm` and `demo_log`.
- `trial` and `paid` are placeholders in the current execution and must not be presented as live metrics until Supabase/Creem wiring is added.
- `daily_analytics.py` may include funnel-adjacent rollups, but the visitor-to-paid system is not yet fully automated in code.

## Reporting Cadence

- Daily funnel snapshot in `daily_analytics.py`
- Weekly cohort analysis (by sign-up week)
- Monthly board-ready funnel visualization

## Guardrails

- Do not describe the visitor-to-paid funnel as fully operational unless the `trial` and `paid` stages are actually populated.
- Label placeholder stages clearly in reports.
- Prefer code-truth over desired architecture: document unwired stages as planned, not live.
