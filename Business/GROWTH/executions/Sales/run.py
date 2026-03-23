#!/usr/bin/env python3
"""
Sales Agent — Task Dispatcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Routes sales tasks to execution scripts.

Usage:
    python "Sales Agent/run.py" --list-tasks
    python "Sales Agent/run.py" --status
    python "Sales Agent/run.py" --task crm-sync --action pipeline-report
    python "Sales Agent/run.py" --task demo-track --action upcoming
    python "Sales Agent/run.py" --task proposal --action list
"""

import sys
import os
import subprocess
import argparse
import re

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Ensure workspace root is on sys.path ──────────────────────
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, '..', '..', '..', '..'))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import log_task
from shared.api_registry import get_agent_apis
from shared.retry_executor import retry_subprocess, retry_call

AGENT_NAME = "Sales"
AGENT_KEY = "sales"

# ──────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────
TASKS: dict[str, dict] = {
    "crm-sync": {
        "script": os.path.join(_AGENT_DIR, "crm_sync.py"),
        "description": "Manage the Leads CRM — add leads, update stages, pipeline reports",
    },
    "demo-track": {
        "script": os.path.join(_AGENT_DIR, "demo_tracker.py"),
        "description": "Track demo bookings, outcomes, and follow-ups",
    },
    "proposal": {
        "script": os.path.join(_AGENT_DIR, "proposal_manager.py"),
        "description": "Generate proposals with AI pitch + Creem checkout links",
    },
    "call-schedule": {
        "script": os.path.join(_AGENT_DIR, "call_scheduler.py"),
        "description": "Schedule calls, sync Cal.com bookings, manage follow-ups",
    },
    "lead-qualify": {
        "script": os.path.join(_AGENT_DIR, "lead_qualifier.py"),
        "description": "Qualify leads with BANT keywords + Groq AI analysis",
    },
    "pipeline": {
        "script": os.path.join(_AGENT_DIR, "sales_pipeline.py"),
        "description": "Full sales pipeline — stage tracking, velocity, forecasting",
    },
    "call-transcribe": {
        "script": os.path.join(_AGENT_DIR, "call_transcriber.py"),
        "description": "Transcribe sales calls (Groq Whisper) + AI summary → Notion",
    },
    "link-track": {
        "script": os.path.join(_AGENT_DIR, "..", "Marketing", "link_tracker.py"),
        "description": "Generate UTM-tracked Short.io links — see agents/TRACKED_LINKS.md",
    },
    "beta-email-parse": {
        "script": os.path.normpath(os.path.join(
            _AGENT_DIR, "..", "..", "..", "ANALYTICS", "executions", "beta_email_parser.py")),
        "description": "Parse Resend beta key emails — hot leads, engagement tiers, sanity check",
    },
}


# ──────────────────────────────────────────────
# Task Resolution — free-text → registered task
# ──────────────────────────────────────────────
_TASK_KEYWORDS: dict[str, list[str]] = {
    "crm-sync":          ["crm", "pipeline report", "update stage", "add lead", "sync",
                          "update", "stage", "lead stage"],
    "demo-track":        ["demo", "booking", "demo track", "scheduled demo"],
    "proposal":          ["proposal", "pitch", "quote", "offer", "contract"],
    "call-schedule":     ["schedule call", "cal.com", "book call", "follow-up call", "call schedule",
                          "schedule", "book"],
    "lead-qualify":      ["qualify", "bant", "score", "lead quality", "qualify lead",
                          "best lead", "find lead", "top lead"],
    "pipeline":          ["pipeline", "stage track", "velocity", "forecast", "deal"],
    "call-transcribe":   ["transcri", "whisper", "recording", "call summary", "call note"],
    "link-track":        ["utm", "short link", "link track", "track link", "shortio", "link"],
    "beta-email-parse": ["beta email", "resend beta", "beta key email", "hot lead", "interested lead"],
}


def _resolve_task(raw: str) -> str:
    """Resolve free-text to a registered task name via keyword scoring."""
    lower = raw.lower().strip()
    if lower in TASKS:
        return lower
    scores: dict[str, float] = {}
    for task_name, keywords in _TASK_KEYWORDS.items():
        score = sum(len(kw.split()) for kw in keywords if kw in lower)
        scores[task_name] = score
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] > 0:
        print(f"  [resolve] \"{raw[:60]}\" -> {best} (score {scores[best]:.0f})")
        return best
    return raw


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def cmd_list_tasks() -> None:
    print("=" * 60)
    print(f"  💼 {AGENT_NAME} Agent — Available Tasks")
    print("=" * 60)
    for name, info in sorted(TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"\n  {exists} {name}")
        print(f"     {info['description']}")
    print(f"\n{'─' * 60}")
    print(f"  {len(TASKS)} tasks registered")


def cmd_status() -> None:
    apis = get_agent_apis(AGENT_KEY)
    ready = sum(1 for t in TASKS.values() if os.path.isfile(t["script"]))
    print("=" * 60)
    print(f"  💼 {AGENT_NAME} Agent — Status")
    print("=" * 60)
    print(f"\n  Tasks: {ready}/{len(TASKS)} ready")
    print(f"  APIs:  {', '.join(f'{k} ({v})' for k, v in sorted(apis.items()))}")
    for name, info in sorted(TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"  {exists} {name}")
    print()


# Default action for each task when Discord sends generic "run"
_DEFAULT_ACTIONS: dict[str, str] = {
    "crm-sync":         "pipeline-report",
    "demo-track":       "demo-report",
    "proposal":         "track-proposals",
    "call-schedule":    "upcoming",
    "lead-qualify":     "qualification-report",
    "pipeline":         "pipeline-view",
    "call-transcribe":  "transcribe",
    "link-track":       "list-links",
    "beta-email-parse": "hot-leads",
}


def cmd_run(task: str, action: str, extra: list[str]) -> None:
    task = _resolve_task(task)
    if action == "run" and task in _DEFAULT_ACTIONS:
        action = _DEFAULT_ACTIONS[task]
        print(f"  [action] defaulting to --action {action} for {task}")
    info = TASKS.get(task)
    if not info:
        print(f"❌ Unknown task: {task}")
        print(f"   Available: {', '.join(sorted(TASKS.keys()))}")
        sys.exit(1)

    script = info["script"]
    if not os.path.isfile(script):
        print(f"❌ Script not found: {script}")
        sys.exit(1)

    cmd = [sys.executable, script, "--action", action, *extra]
    result = retry_subprocess(
        cmd,
        max_retries=2,
        task_label=f"{AGENT_NAME}/{task}/{action}",
    )

    status = "Complete" if result.returncode == 0 else "Error"
    retry_call(
        log_task,
        agent=AGENT_NAME,
        task=f"{task}/{action}",
        status=status,
        priority="P2",
        output_summary=f"Ran {task} --action {action}",
        error=f"exit code {result.returncode}" if result.returncode != 0 else "",
        max_retries=2,
        task_label=f"Notion log: {AGENT_NAME}/{task}",
    )

    if result.returncode != 0:
        sys.exit(result.returncode)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{AGENT_NAME} Agent — Task Dispatcher",
    )
    parser.add_argument("--list-tasks", action="store_true",
                        help="Show available tasks")
    parser.add_argument("--status", action="store_true",
                        help="Show agent status summary")
    parser.add_argument("--task", metavar="TASK",
                        help="Task to run (e.g., crm-sync, demo-track, proposal)")
    parser.add_argument("--action", metavar="ACTION",
                        help="Action within the task")

    args, extra = parser.parse_known_args()

    if args.list_tasks:
        cmd_list_tasks()
    elif args.status:
        cmd_status()
    elif args.task and args.action:
        cmd_run(args.task, args.action, extra)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
