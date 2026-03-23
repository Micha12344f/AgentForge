# Finance Env Reference

Primary runtime file: `resources/.env`

| Key | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | `revenue_tracker.py`, `expense_manager.py`, `financial_reporter.py`, `invoice_generator.py` | finance records and task logs |
| `SUPABASE_URL` | finance execution scripts | subscription and IB data source |
| `SUPABASE_ANON_KEY` | shared Supabase client fallback | non-service reads |
| `SUPABASE_SERVICE_ROLE_KEY` | finance reporting and reconciliation flows | privileged database reads |
| `CREEM_LIVE_*` | `revenue_tracker.py` | live subscription revenue |
| `CREEM_TEST_*` | finance sandbox checks | test subscription flows |
| `DISCORD_BOT_TOKEN` | shared alerting | finance alerts |
| `DISCORD_ALERTS_CHANNEL_ID` | shared alerting | alert destination |
