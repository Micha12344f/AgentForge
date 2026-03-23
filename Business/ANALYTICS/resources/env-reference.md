# Analytics Env Reference

Primary runtime file: `resources/.env`

| Key | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | `daily_analytics.py`, `hourly_metrics_sync.py`, `ab_test_manager.py` | KPI snapshots, funnel rows, reporting writes |
| `SUPABASE_URL` | all Supabase-backed analytics scripts | page views, users, subscriptions |
| `SUPABASE_ANON_KEY` | shared Supabase client | non-service reads if needed |
| `SUPABASE_SERVICE_ROLE_KEY` | `attribution_audit.py`, `conversion_tracker.py`, `license_tracking_report.py` | privileged analytics queries |
| `RESEND_API_KEY` | `beta_email_parser.py`, `daily_analytics.py`, `hourly_metrics_sync.py` | email delivery and unsubscribe stats |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | shared GA4 client | GA4 reporting auth |
| `GA4_PROPERTY_ID` | shared GA4 client | selects GA4 property |
| `CREEM_*` | `hourly_metrics_sync.py` | subscription/MRR rollups |
| `SHORTIO_*` | `hourly_metrics_sync.py`, `pdf_link_stats.py` | link analytics |
