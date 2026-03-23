# VPS Connectivity

> SSH/Cloudflare tunnel access to hedge-vps.

## Connection Details

| Parameter | Value |
|-----------|-------|
| SSH Host | `hedge-vps` (alias in SSH config) |
| Hostname | `ssh.hedgedge.info` |
| User | `hedgebot` |
| Key | `~/.ssh/id_ed25519` |
| Proxy | Cloudflare tunnel via `cloudflared access ssh` |

## IMPORTANT

- **NEVER use Tailscale** — always use Cloudflare tunnel
- SSH config uses `ProxyCommand` with cloudflared

## SSH Config Entry

```
Host hedge-vps
    HostName ssh.hedgedge.info
    User hedgebot
    IdentityFile ~/.ssh/id_ed25519
    ProxyCommand "C:\Program Files (x86)\cloudflared\cloudflared.exe" access ssh --hostname %h
```

## Health Checks

```bash
# Test connectivity
ssh hedge-vps "echo ok"

# Check disk/memory/load
ssh hedge-vps "df -h && free -m && uptime"

# Check running services
ssh hedge-vps "docker ps"
```
