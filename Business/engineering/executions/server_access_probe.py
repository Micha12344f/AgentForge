from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class SshTarget:
    alias: str | None = None
    host: str | None = None
    user: str | None = None
    port: int = 22
    key_path: str | None = None

    def connection_target(self) -> str:
        if self.alias:
            return self.alias
        if self.host and self.user:
            return f"{self.user}@{self.host}"
        raise ValueError("Either alias or host+user must be provided.")

    def identity_args(self) -> str:
        if self.alias or not self.key_path:
            return ""
        expanded_key_path = str(Path(self.key_path).expanduser())
        return f'-i "{expanded_key_path}" -p {self.port}'


def read_target_from_env(env: Mapping[str, str] | None = None) -> SshTarget:
    environment = env or os.environ
    host = environment.get("SSH_HOST")
    user = environment.get("SSH_USER")
    port_text = environment.get("SSH_PORT", "22")
    key_path = environment.get("SSH_KEY_PATH")
    port = int(port_text)
    return SshTarget(host=host, user=user, port=port, key_path=key_path)


def render_ssh_command(target: SshTarget, remote_command: str) -> str:
    connection_target = target.connection_target()
    identity_args = target.identity_args()
    identity_prefix = f"{identity_args} " if identity_args else ""
    return (
        f'ssh -o BatchMode=yes -o ConnectTimeout=15 {identity_prefix}'
        f'{connection_target} "{remote_command}"'
    )


def render_probe_bundle(target: SshTarget, operating_system: str) -> list[str]:
    commands = [render_ssh_command(target, "whoami"), render_ssh_command(target, "hostname")]

    if operating_system == "windows":
        commands.extend(
            [
                render_ssh_command(target, "cd"),
                render_ssh_command(target, "sc query com.docker.service"),
                render_ssh_command(target, "docker context ls"),
                render_ssh_command(target, "docker version"),
            ]
        )
        return commands

    if operating_system == "wsl":
        commands.extend(
            [
                render_ssh_command(target, "cd"),
                render_ssh_command(target, "wsl --status"),
                render_ssh_command(target, "wsl -l -v"),
                render_ssh_command(target, "wsl -e cat /etc/os-release"),
                render_ssh_command(target, "wsl -e uname -a"),
                render_ssh_command(target, "wsl -e docker version"),
                render_ssh_command(target, "wsl -e docker ps --no-trunc"),
            ]
        )
        return commands

    if operating_system == "linux":
        commands.extend(
            [
                render_ssh_command(target, "pwd"),
                render_ssh_command(target, "uname -a"),
                render_ssh_command(target, "command -v docker"),
                render_ssh_command(target, "docker ps --no-trunc"),
            ]
        )
        return commands

    commands.extend(
        [
            render_ssh_command(target, "cd"),
            render_ssh_command(target, "pwd"),
            render_ssh_command(target, "wsl --status"),
            render_ssh_command(target, "docker version"),
            render_ssh_command(target, "wsl -e docker version"),
        ]
    )
    return commands


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render safe SSH probe commands for direct or Cloudflare-backed server access."
    )
    parser.add_argument("--alias", help="SSH alias from ~/.ssh/config to prefer over direct host access.")
    parser.add_argument(
        "--os",
        choices=["auto", "windows", "linux", "wsl"],
        default="auto",
        help="Target operating system. Use 'wsl' for Windows hosts that run Docker inside WSL2, or 'auto' for a cross-platform starter bundle.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = read_target_from_env()
    if args.alias:
        target = SshTarget(alias=args.alias)

    commands = render_probe_bundle(target, args.os)
    print("# SSH Probe Bundle")
    for command in commands:
        print(command)


if __name__ == "__main__":
    main()