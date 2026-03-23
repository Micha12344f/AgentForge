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
| Twitter bot | VPS Docker | ssh.hedgedge.info |

## Cloudflare

| Resource | Zone |
|----------|------|
| DNS | hedgedge.info |
| Tunnel | SSH access tunnel |
| Security | WAF, DDoS protection |
