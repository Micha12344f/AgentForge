# Monitoring & Alerting Directive

## Purpose
Know when agents fail before users do. Every deployed system must have monitoring and alerting.

## Monitoring Layers

### 1. Health Checks
- HTTP health endpoint: `/health`
- Returns: `{ "status": "ok", "uptime": "...", "last_run": "..." }`
- Checked every 5 minutes

### 2. Agent Run Monitoring
- Success rate per workflow type (target: >95%)
- Cost per run (target: <$0.50 for standard workflows)
- Latency per run (target: <30s for standard workflows)
- Error rate by category

### 3. Alert Rules
| Condition | Channel | Urgency |
|-----------|---------|---------|
| Health check fails 2x | Discord + Email | Critical |
| Success rate <90% (1h window) | Discord | High |
| Cost per run >$2.00 | Discord | Warning |
| No runs in 24h (for scheduled workflows) | Discord | Warning |

### 4. Incident Response
1. Alert fires → check logs → identify root cause
2. If service down → restart or rollback
3. If data issue → pause workflow, investigate
4. Log incident in `resources/incident-log.md`
5. Post-mortem within 24h
