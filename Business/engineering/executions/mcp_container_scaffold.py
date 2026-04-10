from __future__ import annotations

import argparse
from dataclasses import dataclass, field


@dataclass(frozen=True)
class McpContainerSpec:
    service_name: str
    module_path: str = "server"
    app_object: str = "app"
    image_name: str | None = None
    python_version: str = "3.12"
    port: int = 8000
    mount_path: str = "/mcp"
    health_path: str = "/healthz"
    env_file: str = ".env"
    env_vars: tuple[str, ...] = field(default_factory=tuple)

    @property
    def resolved_image_name(self) -> str:
        return self.image_name or f"{self.service_name}:latest"


def render_dockerfile(spec: McpContainerSpec) -> str:
    return f'''FROM python:{spec.python_version}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT={spec.port}

WORKDIR /app

RUN groupadd --system appgroup && useradd --system --gid appgroup --uid 10001 appuser

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

EXPOSE {spec.port}

CMD ["uvicorn", "{spec.module_path}:{spec.app_object}", "--host", "0.0.0.0", "--port", "{spec.port}"]
'''


def render_compose_service(spec: McpContainerSpec) -> str:
    environment_lines = "\n".join(f"      {name}: ${{{name}}}" for name in spec.env_vars)
    if environment_lines:
        environment_block = f"    environment:\n      PORT: \"{spec.port}\"\n{environment_lines}\n"
    else:
        environment_block = f"    environment:\n      PORT: \"{spec.port}\"\n"

    return f'''services:
  {spec.service_name}:
    image: {spec.resolved_image_name}
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - {spec.env_file}
{environment_block}    ports:
      - "{spec.port}:{spec.port}"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    pids_limit: 256
    mem_limit: 512m
    cpus: 1.00
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:{spec.port}{spec.health_path}')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s
'''


def render_operational_notes(spec: McpContainerSpec) -> str:
    return f'''Operational notes:
- Expose the MCP endpoint at {spec.mount_path} and a dedicated health endpoint at {spec.health_path}.
- Prefer a Starlette wrapper so the health route is distinct from the MCP transport route.
- Do not mount the Docker socket into the container.
- Prefer a reverse proxy or private tunnel over exposing the container port directly.
- Linux-first hardening flags such as read-only filesystems, tmpfs, and cap drops work as expected on Linux and WSL2-backed Docker runtimes; revalidate them only for Windows-native containers.
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Docker scaffolds for a custom FastMCP service.")
    parser.add_argument("service_name", help="Compose service name and default image stem.")
    parser.add_argument("--module-path", default="server", help="Python module path for the ASGI app.")
    parser.add_argument("--app-object", default="app", help="ASGI app object name.")
    parser.add_argument("--image-name", help="Override the default image name.")
    parser.add_argument("--python-version", default="3.12", help="Base Python image version.")
    parser.add_argument("--port", type=int, default=8000, help="Container port.")
    parser.add_argument("--mount-path", default="/mcp", help="MCP route mount path.")
    parser.add_argument("--health-path", default="/healthz", help="Health route path.")
    parser.add_argument("--env-file", default=".env", help="Compose env file path.")
    parser.add_argument("--env-var", action="append", default=[], help="Environment variable name to surface in Compose.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = McpContainerSpec(
        service_name=args.service_name,
        module_path=args.module_path,
        app_object=args.app_object,
        image_name=args.image_name,
        python_version=args.python_version,
        port=args.port,
        mount_path=args.mount_path,
        health_path=args.health_path,
        env_file=args.env_file,
        env_vars=tuple(args.env_var),
    )

    print("# Dockerfile")
    print(render_dockerfile(spec))
    print("# docker-compose.yml service")
    print(render_compose_service(spec))
    print("# Notes")
    print(render_operational_notes(spec))


if __name__ == "__main__":
    main()