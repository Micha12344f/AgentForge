# Data Pipeline Architecture

> Scheduled data sync pipelines — how data flows between systems.

## Pipeline Schedule

| Pipeline | Script | Frequency | Source → Destination |
|----------|--------|-----------|---------------------|
| Metrics sync | `hourly_metrics_sync.py` | Hourly | GA4, Resend, Creem → Notion |
| Daily snapshot | `daily_analytics.py` | Daily 06:00 UTC | All sources → Notion `kpi_snapshots` |
| Attribution audit | `attribution_audit.py` | Daily 07:00 UTC | Supabase → validation report |
| Conversion events | `conversion_tracker.py` | Real-time (webhook) | Resend/Creem webhooks → Supabase |

## System Dependencies

```
GA4 Data API ──┐
Resend API ────┤
Creem.io API ──┼──→ Analytics Scripts ──→ Notion Databases
Supabase ──────┤                      ──→ Supabase Tables
Notion API ────┘
```

## Error Handling

- Failures alert via `shared/alerting.py` to Discord.
- Dispatcher-initiated runs use `shared/retry_executor.py` for subprocess and function retries.
- Runtime readiness is checked via `shared/api_registry.py` before orchestration status reporting.
- Pipelines should degrade gracefully when a single upstream is unavailable, returning partial reports rather than failing the entire analytics run.
- On Windows terminals, scripts should reconfigure stdout/stderr to UTF-8 when the active encoding is a `cp*` code page, preventing `UnicodeEncodeError` during warning output.
