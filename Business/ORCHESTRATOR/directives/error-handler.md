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

## Preferred Entry Point

For hedge-vps incidents, start with the unified monitor instead of ad hoc SSH commands:

```powershell
python Business/ORCHESTRATOR/executions/vps_monitor.py --action status
python Business/ORCHESTRATOR/executions/vps_monitor.py --action errors --lines 60
```

## Health Check Scripts

| Script | What It Monitors |
|--------|-----------------|
| `vps_monitor.py --action status` | hedge-vps reachability, WSL Docker state, latest lifecycle log |
| `vps_monitor.py --action cron` | Active WSL cron schedule and legacy Windows task state |
| `vps_monitor.py --action logs --target lifecycle` | Twitter bot lifecycle start/stop log |
| `vps_monitor.py --action logs --target main` | Main Twitter reply bot Docker logs |
| `vps_monitor.py --action logs --target mention` | Mention bot Docker logs |
| `vps_monitor.py --action logs --target alerts` | Discord bot-alerts history |
| `read_bot_alerts.py` | Discord bot alerts |
| `vps_monitor.py --action errors` | Combined bot logs and alert triage view |
