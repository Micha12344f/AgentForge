---
name: vps-connectivity
description: 'Use when connecting to a VPS over SSH, validating remote access, inspecting remote logs, running safe diagnostics, or coordinating a manual deploy from this AgentForge workspace. Trigger keywords: VPS, SSH, remote server, deploy, Docker, systemd, logs.'
argument-hint: 'Describe the remote task, target service, and whether this is diagnostics or deployment.'
---

# VPS Connectivity

Use this skill when a task mentions VPS access, SSH, remote server diagnostics, remote logs, Docker containers on a VPS, systemd services, or a manual deploy to a remote host.

## Workspace Context

- Connection inputs live in the root `.env`: `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_KEY_PATH`
- Repo-specific operating rules live in `Business/ORCHESTRATOR/directives/vps-connectivity.md`
- Command templates and verification order live in `Business/ORCHESTRATOR/resources/connection-reference.md`

## Procedure

1. Read the workspace `.env` and confirm the SSH values exist. Do not print the full file or expose secrets unnecessarily.
2. Verify local prerequisites: `ssh` is installed, the key path exists, and the port is numeric.
3. Run a non-interactive probe first:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 -i "<key-path>" -p <port> <user>@<host> "hostname"
```

4. If the probe succeeds, continue with the least-privileged command that answers the question:

```powershell
ssh -i "<key-path>" -p <port> <user>@<host> "hostname; pwd; whoami"
```

5. Open an interactive shell only after the probe succeeds:

```powershell
ssh -i "<key-path>" -p <port> <user>@<host>
```

6. Before any restart or deploy, snapshot current state: running services or containers, recent logs, and the currently deployed revision if available.
7. Coordinate production changes with DELIVERY unless the user explicitly asks Orchestrator to execute them directly.
8. After any change, verify runtime health and summarize exactly what changed.

## Safety Rules

- Never commit host credentials, private keys, or full secret values.
- Prefer read-only inspection before restart or redeploy operations.
- Avoid destructive host-wide commands unless the user explicitly approves them.
- If the connection method changes, update the Orchestrator connection reference and env examples in the workspace.