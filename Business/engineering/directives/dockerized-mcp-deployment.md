# Dockerized MCP Deployment Directive

## Purpose
Package custom FastMCP servers into hardened Docker containers and deploy them to the configured remote server.

## When To Use

- A custom MCP server should be shared across agents
- The MCP server needs a stable remote runtime
- The MCP server touches external systems and needs a tighter execution boundary
- A user explicitly asks for a server-hosted MCP rather than a local stdio-only process

## Research-Backed Defaults

- Build custom servers with `FastMCP`
- For production HTTP deployments, prefer `streamable-http`
- Prefer `stateless_http=True` and `json_response=True`
- Use explicit return type annotations so tools produce structured output cleanly
- If you need `/healthz`, mount the MCP app inside Starlette or another ASGI wrapper instead of relying on the raw MCP path alone

## Decision Gate

1. If the integration can stay as a local tool or stdio-only MCP, do not containerize yet.
2. If the server is shared, remotely hosted, or higher risk, containerize it.
3. If the target host cannot provide a healthy Docker engine, stop and fix the host before deploying.

## Container Baseline

- One MCP service per container
- Run as non-root
- Read-only filesystem when feasible
- No Docker socket mount
- No privileged mode
- Drop all capabilities not explicitly required
- Apply CPU and memory limits
- Inject secrets at runtime, never bake them into the image
- Pin base images and dependency versions

## Runtime Pattern

1. Build the FastMCP server or mount it into a Starlette app.
2. Expose `/mcp` for the protocol and `/healthz` for health checks.
3. Run behind `uvicorn` in the container.
4. Prefer Linux containers for Python MCP servers.

## Remote Deploy Sequence

1. Use the Remote Server Access skill to confirm host access and Docker health.
2. Render the Dockerfile and Compose service with `executions/mcp_container_scaffold.py`.
3. Copy or build only the specific MCP service artifacts.
4. Start the container with `docker compose up -d <service>` or the equivalent host-specific command such as `wsl -e docker compose up -d <service>` on Windows-backed WSL2 hosts.
5. Verify `docker ps`, container logs, and the health endpoint.
6. Confirm the MCP endpoint responds at the expected mount path.
7. Record the outcome and any env or firewall changes.

## Host Readiness Check

- The current primary deployment path is a Windows host with Ubuntu 24.04 running inside WSL2.
- Before deployment, verify: `wsl -e docker version` must connect successfully, `wsl -e docker ps` must return container state, and the target project path must exist inside the WSL filesystem.
- If tunnel maintenance is required, manage the Windows-side `cloudflared` service separately from the WSL runtime.
- If Docker is not healthy inside WSL2, inspect from the WSL runtime first before escalating.

### Native Linux Host Variant

- On a native Linux host, validate `docker version`, `docker ps`, and `systemctl status docker` before rollout.

### Legacy — Windows Host Gate (for reference)

- On a Windows host without WSL2, do not assume Docker is ready because `com.docker.service` is running.
- Prefer Linux containers via a healthy Linux-container backend.

## Rules

- Default to `streamable-http`; use `stdio` only for local development.
- On WSL2-backed hosts, run deployment commands through `wsl -e ...` or `wsl -- bash -lc "..."` so they target the actual Docker runtime.
- Do not expose the Docker daemon over unauthenticated TCP.
- Do not deploy write-capable MCP tools without clear approval boundaries.
- Coordinate broad network, firewall, or daemon changes with Delivery.