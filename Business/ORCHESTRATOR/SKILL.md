# ORCHESTRATOR — Skill Command Sheet

> **Adopt this department to gain**: Task routing, multi-agent coordination, deployment automation, VPS management, error handling, and system monitoring skills. This is the central nervous system of the entire business OS.

---

## Skills You Gain

The Orchestrator does not perform domain work — it routes, decomposes, coordinates, monitors, and deploys. Every inbound request passes through here first.

## Governance

- **DOE owner**: Orchestrator is the only department allowed to reorganise files across `Business/` so the Directives, Executions, Resources, and `SKILL.md` pattern stays coherent.
- **SKILL.md owner**: Orchestrator is the only department allowed to rewrite department `SKILL.md` files when folder structure changes, responsibilities move, or comments need to explain what each folder now does.
- **Department boundary**: Other department agents may update domain content inside their lane, but they do not own cross-department structure, folder mapping, or department skill-governance docs.

### Skill 1 — Agent Routing & Intent Classification
- **Directive**: `directives/agent-routing.md` — routing decision matrix, intent classification rules
- **Execution**: `executions/agent_router.py` — classifies user intent and selects target department

### Skill 2 — Cross-Agent Coordination
- **Directive**: `directives/cross-agent-coordination.md` — multi-agent workflow patterns and handoff protocols

### Skill 3 — Task Decomposition
- **Directive**: `directives/task-decomposition.md` — how to break complex requests into dependency DAGs

### Skill 4 — Status Reporting
- **Directive**: `directives/status-reporting.md` — cross-department status aggregation rules

### Skill 5 — Error Handling & Incident Response
- **Directive**: `directives/error-handler.md` — incident detection, triage, and resolution
- **Execution**: `executions/read_bot_alerts.py` — Discord bot alert log reader
- **Resource**: `resources/incident-log.md` — historical incident records

### Skill 6 — VPS Connectivity & SSH
- **Directive**: `directives/vps-connectivity.md` — SSH/Cloudflare tunnel access to hedge-vps
- **Resource**: `resources/connection-reference.md` — SSH hosts, ports, tunnel configs
- **Note**: Always use Cloudflare tunnel (`ssh.hedgedge.info`), NEVER Tailscale

### Skill 7 — Cron Scheduling
- **Execution**: `executions/cron_scheduler.py` — APScheduler Railway always-on cron container

### Skill 8 — App Deployment Pipeline
- **Directive**: `directives/landing-page-deploy.md` — landing page deploy to Vercel
- **Executions**: `executions/deploy.py` (deployment automation), `executions/build_installer.py` (Electron NSIS installer), `executions/bump_version.py` (semantic versioning), `executions/create_release.py` (GitHub Release with artifacts)
- **Resources**: `resources/deployment-workflow.md` (step-by-step deploy checklist), `resources/release-checklist.md` (pre-release QA), `resources/troubleshooting.md` (common issues and fixes)

---

## Dispatcher

`executions/run.py` — master dispatcher, routes `--agent` and `--task` flags. Entry point for ALL business operations.

## Resources

| File | Purpose |
|------|---------|
| `resources/.env` | Orchestrator-specific env vars |
| `resources/connection-reference.md` | SSH hosts, ports, tunnel IDs |
| `resources/deployment-workflow.md` | Step-by-step deploy checklist |
| `resources/incident-log.md` | Historical incident records |
| `resources/release-checklist.md` | Pre-release QA checklist |
| `resources/troubleshooting.md` | Common issues and resolutions |

## Shared Dependencies

Imports from workspace-root `shared/`: `alerting.py`, `discord_client.py`, `notion_client.py`, `supabase_client.py`, `llm_router.py`.

## Cross-Department Links

| Department | Orchestrator Provides | Orchestrator Needs |
|------------|----------------------|-------------------|
| ALL | Task routing, status aggregation, error handling | Task definitions |
| ANALYTICS | Cron scheduling for metric syncs | Pipeline health data |
| GROWTH | Deploy automation for landing page | Campaign status |
| STRATEGY | Release pipeline for app deploys | Roadmap priorities |
| FINANCE | Revenue alert routing | Alert thresholds |

## Structural Maintenance Authority

- Update any department file when the change preserves or improves the DOE framework.
- Add, move, or document folders when responsibilities shift between departments.
- Rewrite comments and skill summaries so the workspace stays aligned with the actual folder structure.
