# Revenue Tracking

> MRR waterfall, subscription lifecycle, and Creem.io revenue pipeline.

## Data Source

- **Creem.io API** via `shared/creem_client.py`
- **Supabase** `subscriptions` table for user→plan mapping
- **Notion** `mrr_tracker` database for waterfall records

## MRR Waterfall Components

| Component | Definition |
|-----------|-----------|
| New MRR | Revenue from first-time subscribers |
| Expansion MRR | Revenue increase from plan upgrades |
| Contraction MRR | Revenue decrease from plan downgrades |
| Churned MRR | Revenue lost from cancellations |
| Reactivation MRR | Revenue from re-subscribing users |
| Net New MRR | New + Expansion + Reactivation − Contraction − Churned |

## Subscription States

```
Trial → Active → (Upgrade/Downgrade) → Cancelled → (Reactivated)
                                      → Expired
```

## Sync Schedule

- `hourly_metrics_sync.py` (ANALYTICS) pulls Creem.io events hourly
- `revenue_tracker.py` (FINANCE) calculates MRR waterfall daily
