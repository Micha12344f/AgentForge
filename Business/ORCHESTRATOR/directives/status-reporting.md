# Status Reporting

> Cross-department status aggregation rules.

## Status Aggregation

`status_aggregator.py` polls each department and builds a unified dashboard.

## Health States

| State | Meaning | Icon |
|-------|---------|------|
| `healthy` | All systems nominal | ✅ |
| `degraded` | Partial issues, non-critical | ⚠️ |
| `down` | Critical failure | ❌ |
| `unknown` | Cannot reach agent/service | ❓ |

## Per-Department Checks

| Department | Health Check | Data Source |
|------------|-------------|-------------|
| ANALYTICS | Last sync timestamp < 2h ago | Notion `kpi_snapshots` |
| FINANCE | MRR tracker updated today | Notion `mrr_tracker` |
| GROWTH | Email sends executing on schedule | Supabase + Resend |
| STRATEGY | No overdue roadmap items | Notion roadmap |
| ORCHESTRATOR | Cron scheduler alive, VPS reachable | Railway + SSH |

## Reporting Cadence

- On-demand via `/status` command
- Daily automated summary at 09:00 UTC
- Immediate alert on any `down` state
