# Connection Reference

> SSH hosts, ports, and tunnel IDs for Hedge Edge infrastructure.

## SSH Hosts

| Alias | Hostname | User | Key | Proxy |
|-------|----------|------|-----|-------|
| `hedge-vps` | `ssh.hedgedge.info` | `hedgebot` | `~/.ssh/id_ed25519` | cloudflared |

## Services

| Service | Platform | URL |
|---------|----------|-----|
| Landing page | Vercel | hedgedge.info |
| Cron scheduler | Railway | (internal) |
| Email sends | Railway | (internal) |
| Support bot | VPS | ssh.hedgedge.info |
| Twitter bot | VPS Windows host + WSL Docker | ssh.hedgedge.info |
| Mention bot | VPS WSL Docker | ssh.hedgedge.info |

## Operational Notes

- Prefer `Business/ORCHESTRATOR/executions/vps_monitor.py` for status, cron, log, and alert checks.
- `ssh hedge-vps` lands on a Windows host; the active Twitter bot schedule runs inside WSL Ubuntu.
- Windows Task Scheduler entries exist for the Twitter bot, but the WSL cron files and lifecycle logs are the primary source of truth.

## Cloudflare

| Resource | Zone |
|----------|------|
| DNS | hedgedge.info |
| Tunnel | SSH access tunnel |
| Security | WAF, DDoS protection |
