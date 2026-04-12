# Connection Reference

> SSH access patterns and verification commands for AgentForge VPS work.

## Required Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `SSH_HOST` | root `.env` | VPS hostname or IP |
| `SSH_USER` | root `.env` | Remote SSH user |
| `SSH_PORT` | root `.env` | SSH port |
| `SSH_KEY_PATH` | root `.env` | Local private key path |

## Notes

- `SSH_KEY_PATH` may use `~`; expand it to the local home directory before passing it to `ssh`.
- Keep hostnames, IPs, and keys in `.env`, not in tracked docs.
- A local SSH alias is recommended for convenience and should live only in the user's `~/.ssh/config`.
- If the SSH path is fronted by Cloudflare Access, the alias in `~/.ssh/config` is the operational entrypoint even when `.env` does not contain a directly reachable host.
- A first SSH attempt through Cloudflare Access may open a browser and appear stalled; finish browser auth, then rerun the same probe.
- Successful Cloudflare Access login writes session artifacts under `~/.cloudflared`.

## Optional Local Alias

```sshconfig
Host agentforge-vps
    HostName <SSH_HOST>
    User <SSH_USER>
    Port <SSH_PORT>
    IdentityFile <expanded SSH_KEY_PATH>
    ProxyCommand <path-to-cloudflared> access ssh --hostname %h
```

## Command Templates

### Cloudflare Access Preflight

```powershell
cloudflared access login --quiet --auto-close https://<ssh-app-host>
```

### Connectivity Probe

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=15 <alias> "whoami"
ssh -o BatchMode=yes -o ConnectTimeout=15 -i "<key-path>" -p <port> <user>@<host> "hostname"
```

### Interactive Session

```powershell
ssh <alias>
ssh -i "<key-path>" -p <port> <user>@<host>
```

### Basic Read-Only Inspection

```powershell
ssh <alias> "whoami"
ssh <alias> "hostname"
ssh <alias> "wsl -e uname -a"
ssh <alias> "wsl -e docker ps"
```

## Verification Order

1. If the path uses Cloudflare Access, run the preflight login when the session may be expired.
2. Run the connectivity probe. If a browser opens or the session returns little output, finish auth and rerun the same probe.
3. Confirm remote identity: `whoami`, `hostname`, and current working directory when relevant.
4. Identify the runtime manager in use: Docker, Docker Compose, systemd, PM2, or plain process supervision.
5. On the Windows plus WSL2 host shape, validate the Linux runtime with `wsl -e uname -a` and `wsl -e docker ps`.
6. Check only the service relevant to the request.
7. If a change is required, capture current state before restarting anything.
8. Verify health again before ending the session.

## Deploy Notes

- Prefer service-level restarts over host-level restarts.
- Validate logs and health immediately after a deploy or restart.
- Escalate ambiguous infrastructure changes to DELIVERY when the blast radius is unclear.