# Error Handler

> Incident detection, triage, and resolution procedures.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P0 — Critical | Service down, revenue impact | Immediate | Cron scheduler crash, checkout broken |
| P1 — High | Feature degraded, user-facing | <1 hour | Email sends failing, VPS unreachable |
| P2 — Medium | Non-critical issue | <4 hours | Analytics sync delayed, dashboard stale |
| P3 — Low | Cosmetic or minor | Next business day | Log noise, non-blocking warnings |

## Triage Process

1. **Detect**: Via health checks, cron monitors, or user reports
2. **Classify**: Apply severity level based on impact
3. **Diagnose**: Check logs, health endpoints, recent deploys
4. **Resolve**: Apply fix or rollback
5. **Document**: Log in `resources/incident_log.md`

## Health Check Scripts

| Script | What It Monitors |
|--------|-----------------|
| `tw_health_check.py` | Twitter bot container |
| `tw_log_analyzer.py` | Twitter bot logs |
| `tw_cron_inspector.py` | Twitter cron jobs |
| `read_bot_alerts.py` | Discord bot alerts |
| `vps_health.py` | VPS system health |
