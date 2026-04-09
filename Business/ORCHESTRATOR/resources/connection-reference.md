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
- A local SSH alias is recommended for convenience but should live only in the user's `~/.ssh/config`.

## Optional Local Alias

```sshconfig
Host agentforge-vps
    HostName <SSH_HOST>
    User <SSH_USER>
    Port <SSH_PORT>
    IdentityFile <expanded SSH_KEY_PATH>
```

## Command Templates

### Connectivity Probe

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 -i "<key-path>" -p <port> <user>@<host> "hostname"
```

### Interactive Session

```powershell
ssh -i "<key-path>" -p <port> <user>@<host>
```

### Basic Read-Only Inspection

```powershell
ssh -i "<key-path>" -p <port> <user>@<host> "hostname; pwd; whoami"
```

## Verification Order

1. Run the connectivity probe.
2. Confirm remote identity: host, user, current working directory.
3. Identify the runtime manager in use: Docker, Docker Compose, systemd, PM2, or plain process supervision.
4. Check only the service relevant to the request.
5. If a change is required, capture current state before restarting anything.
6. Verify health again before ending the session.

## Deploy Notes

- Prefer service-level restarts over host-level restarts.
- Validate logs and health immediately after a deploy or restart.
- Escalate ambiguous infrastructure changes to DELIVERY when the blast radius is unclear.