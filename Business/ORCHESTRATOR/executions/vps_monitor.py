#!/usr/bin/env python3
"""
Hedge Edge VPS Monitor
━━━━━━━━━━━━━━━━━━━━━━
Single entry point for hedge-vps health checks, Twitter bot status, WSL cron,
remote logs, and Discord bot alerts.

Usage:
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action status
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action cron
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action tasks
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target lifecycle
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target main --lines 60
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target mention
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action logs --target alerts --lines 30
    python Business/ORCHESTRATOR/executions/vps_monitor.py --action errors
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path


if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


WORKSPACE = Path(__file__).resolve().parents[3]
SSH_HOST = "hedge-vps"
READ_BOT_ALERTS = Path(__file__).with_name("read_bot_alerts.py")
WINDOWS_LOG_DIR = r"C:\HedgeEdge\twitter-bot\logs"
ROOT_CRONTAB = r"C:\HedgeEdge\twitter-bot\root_crontab.txt"
CRON_FILE = r"C:\HedgeEdge\twitter-bot\hedgeedge-twitter-bot-cycle.cron"


def _clean_output(text: str) -> str:
    cleaned = text.replace("#< CLIXML", "")
    if "<Objs Version=" in cleaned:
        cleaned = cleaned.split("<Objs Version=", 1)[0]
    return cleaned.strip()


def _run(cmd: list[str], timeout: int = 120, check: bool = True) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        cwd=WORKSPACE,
    )
    stdout = _clean_output(result.stdout)
    stderr = _clean_output(result.stderr)
    output = "\n".join(part for part in (stdout, stderr) if part).strip()
    if check and result.returncode != 0:
        raise RuntimeError(output or f"Command failed with exit code {result.returncode}")
    return output


def _run_remote_ps(script: str, timeout: int = 120, check: bool = True) -> str:
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return _run(
        ["ssh", SSH_HOST, "powershell", "-NoProfile", "-EncodedCommand", encoded],
        timeout=timeout,
        check=check,
    )


def _run_local_python(script: Path, args: list[str], timeout: int = 120) -> str:
    return _run([sys.executable, str(script), *args], timeout=timeout)


def _parse_json(text: str):
    text = text.strip()
    if not text:
        return None
    return json.loads(text)


def _parse_json_lines(text: str) -> list[dict]:
    items: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            items.append(value)
    return items


def _print_section(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body.strip() if body.strip() else "(no output)")


def get_remote_context() -> dict:
    script = r'''
$wsl = (wsl -l -q | Out-String).Trim()
[PSCustomObject]@{
  Computer = $env:COMPUTERNAME
  User = $env:USERNAME
  TimeUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss 'UTC'")
  WorkingDirectory = (Get-Location).Path
  WslDistros = $wsl
} | ConvertTo-Json -Compress
'''
    return _parse_json(_run_remote_ps(script)) or {}


def get_cron_text() -> str:
    script = rf'Get-Content "{ROOT_CRONTAB}" -Raw'
    return _run_remote_ps(script)


def get_cycle_cron_text() -> str:
    script = rf'Get-Content "{CRON_FILE}" -Raw'
    return _run_remote_ps(script)


def get_container_rows() -> list[dict]:
    output = _run_remote_ps('wsl -d Ubuntu -- sudo docker ps -a --format "{{json .}}"', check=False)
    return _parse_json_lines(output)


def get_latest_lifecycle(lines: int) -> str:
    script = rf'''
Get-ChildItem "{WINDOWS_LOG_DIR}\lifecycle_*.log" -File |
Sort-Object LastWriteTime -Descending |
Select-Object -First 1 |
ForEach-Object {{
    [PSCustomObject]@{{
        FullName = $_.FullName
        Length = $_.Length
        LastWriteTimeUtc = $_.LastWriteTimeUtc.ToString("yyyy-MM-dd HH:mm:ss 'UTC'")
        LastWriteTimeLocal = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }} | ConvertTo-Json -Compress
  "`n---TAIL---`n"
  Get-Content $_.FullName -Tail {lines}
}}
'''
    return _run_remote_ps(script)


def get_windows_tasks() -> str:
    script = r'''
$names = @(
  "HedgeEdge-TwitterBot",
  "HedgeEdge-TwitterBot-Daily",
  "HedgeEdge-TwitterBot-OnBoot",
  "HedgeEdge-TwitterWatchdog",
  "HedgeEdgeTwitterBot-Start",
  "HedgeEdgeTwitterBot-Stop"
)

$rows = foreach ($name in $names) {
  $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if ($null -ne $task) {
    $info = Get-ScheduledTaskInfo -TaskName $name
    [PSCustomObject]@{
      TaskName = $name
      State = [string]$task.State
            LastRunTime = $(if ($info.LastRunTime -and $info.LastRunTime.Year -gt 2000) { $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") } elseif ($info.LastRunTime) { $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "N/A" })
            NextRunTime = $(if ($info.NextRunTime) { $info.NextRunTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "N/A" })
      LastTaskResult = $info.LastTaskResult
      Actions = (($task.Actions | ForEach-Object { ($_.Execute + " " + $_.Arguments).Trim() }) -join " || ")
    }
  }
}

$rows | ConvertTo-Json -Depth 4 -Compress
'''
    rows = _parse_json(_run_remote_ps(script))
    if not rows:
        return "No legacy Windows tasks found."
    if isinstance(rows, dict):
        rows = [rows]
    formatted = []
    for row in rows:
        formatted.append(
            "\n".join(
                [
                    f"Task: {row['TaskName']}",
                    f"  State: {row['State']}",
                    f"  Last run: {row['LastRunTime']}",
                    f"  Next run: {row['NextRunTime']}",
                    f"  Result: {row['LastTaskResult']}",
                    f"  Action: {row['Actions']}",
                ]
            )
        )
    return "\n\n".join(formatted)


def get_docker_logs(target: str, lines: int) -> str:
    container = {
        "main": "hedgeedge-twitter-bot",
        "mention": "hedgeedge-mention-bot",
    }[target]
    return _run_remote_ps(
        f"wsl -d Ubuntu -- sudo docker logs --tail {lines} {container}",
        timeout=180,
        check=False,
    )


def get_alert_logs(lines: int) -> str:
    return _run_local_python(READ_BOT_ALERTS, ["--action", "errors", "--limit", str(lines)], timeout=180)


def format_containers(rows: list[dict]) -> str:
    if not rows:
        return "No WSL Docker containers were returned."
    wanted = [
        row for row in rows
        if row.get("Names") in {"hedgeedge-twitter-bot", "hedgeedge-mention-bot", "hedgeedge-twitter-watchdog"}
    ]
    if not wanted:
        wanted = rows
    lines = []
    for row in wanted:
        ports = row.get("Ports", "")
        port_suffix = f" | ports: {ports}" if ports else ""
        lines.append(f"{row.get('Names', '?')}: {row.get('Status', 'unknown')}{port_suffix}")
    return "\n".join(lines)


def action_status(lines: int) -> None:
    remote = get_remote_context()
    containers = get_container_rows()
    lifecycle = get_latest_lifecycle(lines)
    cron = get_cron_text()

    summary = "\n".join(
        [
            f"Host: {remote.get('Computer', 'unknown')}",
            f"User: {remote.get('User', 'unknown')}",
            f"Time: {remote.get('TimeUtc', 'unknown')}",
            f"Working dir: {remote.get('WorkingDirectory', 'unknown')}",
            f"WSL distros: {remote.get('WslDistros', '(none)')}",
        ]
    )
    _print_section("VPS", summary)
    _print_section("WSL Cron", cron)
    _print_section("Containers", format_containers(containers))
    _print_section("Latest Lifecycle Log", lifecycle)


def action_cron() -> None:
    _print_section("Installed Root Crontab", get_cron_text())
    _print_section("Cycle Definition", get_cycle_cron_text())
    _print_section("Legacy Windows Tasks", get_windows_tasks())


def action_logs(target: str, lines: int) -> None:
    if target == "lifecycle":
        _print_section("Lifecycle Log", get_latest_lifecycle(lines))
    elif target in {"main", "mention"}:
        _print_section(f"Docker Logs: {target}", get_docker_logs(target, lines))
    elif target == "alerts":
        _print_section("Discord Bot Alerts", get_alert_logs(lines))
    else:
        raise ValueError(f"Unsupported log target: {target}")


def action_errors(lines: int) -> None:
    containers = get_container_rows()
    _print_section("Containers", format_containers(containers))
    _print_section("Latest Lifecycle Log", get_latest_lifecycle(lines))
    _print_section("Main Bot Logs", get_docker_logs("main", lines))
    _print_section("Mention Bot Logs", get_docker_logs("mention", lines))
    try:
        alerts = get_alert_logs(min(lines, 50))
    except Exception as exc:
        alerts = f"Unable to read Discord bot alerts: {exc}"
    _print_section("Discord Alerts", alerts)


def action_tasks() -> None:
    _print_section("Legacy Windows Tasks", get_windows_tasks())


def main() -> None:
    parser = argparse.ArgumentParser(description="Hedge Edge VPS monitor")
    parser.add_argument(
        "--action",
        choices=["status", "cron", "logs", "errors", "tasks"],
        required=True,
    )
    parser.add_argument(
        "--target",
        choices=["lifecycle", "main", "mention", "alerts"],
        default="lifecycle",
        help="Log source for --action logs",
    )
    parser.add_argument("--lines", type=int, default=40, help="Number of log lines to print")
    args = parser.parse_args()

    try:
        if args.action == "status":
            action_status(args.lines)
        elif args.action == "cron":
            action_cron()
        elif args.action == "logs":
            action_logs(args.target, args.lines)
        elif args.action == "errors":
            action_errors(args.lines)
        elif args.action == "tasks":
            action_tasks()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()