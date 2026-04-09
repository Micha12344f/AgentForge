# VPS Connectivity Directive

## Purpose
Establish safe, repeatable VPS access from this workspace for diagnostics, log inspection, and controlled remote operations.

## Source Of Truth

- Root `.env`: `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_KEY_PATH`
- `resources/connection-reference.md`: connection pattern, command templates, verification order
- `.env.example` and `resources/.env.example`: required placeholders only, never live credentials

## Preferred Workflow

1. Read the root `.env` and confirm the SSH values are present.
2. Verify local prerequisites before connecting:
   - `ssh` is available in PowerShell
   - the configured key path exists locally
   - host, user, and port are populated and plausible
3. Start with a non-interactive connectivity probe:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 -i "<key-path>" -p <port> <user>@<host> "hostname"
```

4. Use an interactive SSH session only after the probe succeeds.
5. Prefer read-only inspection first: working directory, host identity, running containers or services, recent logs, and health endpoints.
6. Snapshot current state before any restart or deploy: process or container status, current release or commit if available, and recent logs.
7. Production changes stay coordinated with DELIVERY unless the user explicitly asks Orchestrator to execute them directly.

## Safe Deploy Sequence

1. Confirm the target path and process manager on the VPS.
2. Pull or upload only the required change.
3. Restart only the affected service or container.
4. Verify health immediately after the restart.
5. Record the outcome in the relevant execution log or incident note.

## Rules

- Never store private keys, passwords, or live host details in tracked files.
- Never echo secret env values back into chat or command output unless the user explicitly requests that level of detail.
- Prefer non-interactive verification before opening a shell.
- Avoid destructive commands such as `reboot`, `rm -rf`, `docker system prune`, or `git reset --hard` unless the user explicitly approves them.
- If the connection topology changes, update `resources/connection-reference.md` and the env examples through Orchestrator.