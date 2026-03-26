---
name: vps-monitoring
description: Use when checking hedge-vps health, reading Twitter or mention bot logs, inspecting WSL cron schedules, or triaging VPS bot errors and alerts.
---

# VPS Monitoring

Use this skill for Hedge Edge infrastructure work on hedge-vps, especially when the task involves Twitter bots, mention bots, WSL cron, remote logs, or error monitoring.

## Preferred Workflow

1. Use the Orchestrator monitor first:

```powershell
python Business/ORCHESTRATOR/executions/vps_monitor.py --action status
```

2. If you need schedule details or want to distinguish the live WSL cron from legacy Windows tasks:

```powershell
python Business/ORCHESTRATOR/executions/vps_monitor.py --action cron
python Business/ORCHESTRATOR/executions/vps_monitor.py --action tasks
```

3. For logs:

```powershell
python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target lifecycle --lines 80
python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target main --lines 60
python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target mention --lines 60
python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target alerts --lines 30
```

4. For incident triage:

```powershell
python Business/ORCHESTRATOR/executions/vps_monitor.py --action errors --lines 60
```

## Rules

- Always connect via `ssh hedge-vps` through the Cloudflare tunnel.
- Never use Tailscale.
- Prefer the monitor script over ad hoc SSH quoting, because hedge-vps is a Windows host with WSL-based bot scheduling.
- Treat Windows Task Scheduler entries for the Twitter bot as legacy unless the WSL cron and lifecycle logs disagree.

## Architecture Notes

- hedge-vps is a Windows host.
- The active Twitter bot cadence runs through WSL Ubuntu cron and WSL Docker.
- The mention bot runs as a separate Docker container.
- Discord alert inspection is local via `read_bot_alerts.py`.