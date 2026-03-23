# Funnel Reporting

> Full-funnel conversion reporting from first visit to paying customer.

## Funnel Stages

```
Visitor → Sign-up → Beta Claim → Active User → Checkout → Subscriber
  (GA4)   (Supabase)  (Supabase)  (App usage)  (Creem.io)  (Creem.io)
```

## Conversion Points

| Stage Transition | Data Source | Metric |
|-----------------|-------------|--------|
| Visitor → Sign-up | GA4 + Supabase | Registration conversion rate |
| Sign-up → Beta Claim | Supabase `beta_keys` | Beta activation rate |
| Beta Claim → Active | Supabase sessions | 7-day activation rate |
| Active → Checkout | Creem.io events | Purchase intent rate |
| Checkout → Subscriber | Creem.io | Checkout completion rate |

## Reporting Cadence

- Daily funnel snapshot in `daily_analytics.py`
- Weekly cohort analysis (by sign-up week)
- Monthly board-ready funnel visualization
