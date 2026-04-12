# Remote Server Access Directive

## Purpose
Reach the configured server safely before any MCP deployment or diagnostics.

## When To Use

- Inspect the server that will host a custom MCP container
- Confirm Cloudflare-backed SSH access works from this machine
- Determine whether the host is pure Linux, pure Windows, or Windows with WSL2 Ubuntu before planning deployment steps
- Verify Docker engine health before attempting any MCP container rollout

## Source Of Truth

- Root `.env`: `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_KEY_PATH`
- Local `~/.ssh/config`: check for a host alias that uses `ProxyCommand ... cloudflared access ssh --hostname %h`
- `Business/ORCHESTRATOR/resources/connection-reference.md`: verification order and safe command sequencing

## Workflow

1. Read the workspace `.env` if it exists and confirm the SSH values. Do not echo secret values. If the file is missing, the values are incomplete, or the direct path is stale, do not block on `.env`.
2. Inspect the local `~/.ssh/config` file for a Cloudflare Access alias. If present, prefer the alias over raw host fields.
3. Verify local prerequisites:
   - `ssh` exists
   - `cloudflared` exists if the alias uses it
   - the configured key path exists locally when using the direct path
4. If the alias uses Cloudflare Access and the session may be expired, run `cloudflared access login --quiet --auto-close https://<ssh-app-host>` before retrying SSH.
5. Start with a non-interactive probe:
   - Alias path: `ssh -o BatchMode=yes -o ConnectTimeout=15 <alias> "whoami"`
   - Direct path: `ssh -o BatchMode=yes -o ConnectTimeout=15 -i "<key-path>" -p <port> <user>@<host> "hostname"`
6. If the alias probe opens a browser or returns little output, finish browser auth and rerun `whoami` or `hostname` before treating the connection as failed.
7. Identify the remote platform:
   - Cross-platform: `whoami`, `hostname`
   - Windows hints: `cd`, `sc query`, `docker context ls`, `docker version`, `wsl --status`, `wsl -l -v`
   - WSL hints: `wsl -e cat /etc/os-release`, `wsl -e uname -a`, `wsl -e docker version`, `wsl -e docker ps`
   - Linux hints: `pwd`, `uname -a`, `docker ps`, `systemctl status`
8. Snapshot runtime state before any change:
   - Docker availability and engine health
   - running containers or services relevant to the MCP deployment
   - current deploy path or working directory
   - recent logs for the target service if it already exists
9. Hand broad infrastructure changes to Delivery unless the user explicitly asks Engineering to execute the narrow MCP deployment itself.

## Windows Host With WSL2 Ubuntu Runtime (Primary)

- The SSH entrypoint lands in a Windows shell, but the Linux workload runtime is Ubuntu 24.04 inside WSL2.
- Inspect Docker through WSL: `wsl -e docker ps`, `wsl -e docker compose ps`, `wsl -e docker version`.
- Inspect Linux runtime details through WSL: `wsl -e cat /etc/os-release`, `wsl -e uname -a`, `wsl -e python3 --version`.
- `wsl -l -v` can be less informative over non-interactive SSH on this host shape; prefer `wsl -e uname -a` or `wsl -e cat /etc/os-release` to prove the Linux side is reachable.
- The Cloudflare tunnel may remain a Windows service even when containers run in WSL2: `sc query cloudflared`.
- Prefer Linux containers for Python MCP servers; on this host they run inside the WSL2 Ubuntu runtime.

## Pure Linux Host Notes

- If the target is a native Linux host, use `docker ps`, `docker compose ps`, and service-specific logs before any restart.
- Check service health with `systemctl status docker` and `systemctl status cloudflared` when applicable.

## Windows Host Without WSL2 (Legacy — for reference only)

- `pwd` is not reliable on a cmd-backed SSH shell. Prefer `cd`.
- Docker Desktop being installed is not enough; `docker version` must reach the engine successfully.
- Check `sc query com.docker.service` and `docker context ls` before planning a deployment.

## Rules

- Never assume the direct IP in `.env` is the active access path; check for a Cloudflare-backed alias first.
- Never treat a browser-opening first SSH attempt as a hard failure; Cloudflare Access may only be priming the local session token.
- Never assume Cloudflare and Docker live in the same runtime; on this host the tunnel is Windows-side and Docker runs in WSL2 Ubuntu.
- Never restart Docker or services before capturing current state.
- Never expose live hostnames, IPs, usernames, or secret values in tracked files.