#!/usr/bin/env python3
"""
Analytics Agent — Task Dispatcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Routes analytics tasks to execution scripts.

Usage:
    python "Analytics Agent/run.py" --list-tasks
    python "Analytics Agent/run.py" --status
    python "Analytics Agent/run.py" --task report --action weekly
    python "Analytics Agent/run.py" --task notion-report --action weekly
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
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(_AGENT_DIR)))


def _workspace_python() -> str | None:
    candidates = [
        os.path.join(_WORKSPACE, ".venv", "Scripts", "python.exe"),
        os.path.join(_WORKSPACE, ".venv", "bin", "python"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _bootstrap_workspace_python() -> None:
    preferred = _workspace_python()
    if not preferred:
        return
    current = os.path.abspath(sys.executable).lower()
    target = os.path.abspath(preferred).lower()
    if current == target:
        return
    result = subprocess.run(
        [preferred, os.path.abspath(__file__), *sys.argv[1:]],
        check=False,
    )
    sys.exit(result.returncode)


_bootstrap_workspace_python()
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import log_task
from shared.api_registry import get_agent_apis
from shared.retry_executor import retry_subprocess, retry_call

AGENT_NAME = "Analytics"
AGENT_KEY = "analytics"

# ──────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────
TASKS: dict[str, dict] = {
    "email-template-audit": {
        "script": os.path.join(_AGENT_DIR, "email_template_audit.py"),
        "description": "Pull full email template bodies plus per-template metrics for audit and refurbishment planning",
    },
    "kpi-snapshot": {
        "script": os.path.join(_AGENT_DIR, "kpi_snapshot.py"),
        "description": "Read or write mirrored KPI snapshot tables in Notion for dashboard maintenance",
    },
    "license-track": {
        "script": os.path.join(_AGENT_DIR, "license_tracking_report.py"),
        "description": "Track license activation, usage cadence, device fleet, errors, and customer health",
    },
    "funnel-calc": {
        "script": os.path.join(_AGENT_DIR, "funnel_calculator.py"),
        "description": "Calculate conversion funnels and cohort metrics",
    },
    "ab-test": {
        "script": os.path.join(_AGENT_DIR, "ab_test_manager.py"),
        "description": "Design, monitor, and analyze A/B tests with statistical rigor",
    },
    "attribution": {
        "script": os.path.join(_AGENT_DIR, "attribution_modeler.py"),
        "description": "Multi-model marketing attribution analysis (first/last/linear)",
    },
    "conversion-track": {
        "script": os.path.join(_AGENT_DIR, "conversion_tracker.py"),
        "description": "Beta & paid conversion analytics from Supabase user_attribution",
    },
    "cohort": {
        "script": os.path.join(_AGENT_DIR, "cohort_analyzer.py"),
        "description": "Cohort retention analysis, LTV estimation, churn patterns",
    },
    "report": {
        "script": os.path.join(_AGENT_DIR, "strategic_report.py"),
        "description": "Strategic direct-source analytics reports from GA4, Supabase, Resend, and Creem",
    },
    "notion-report": {
        "script": os.path.join(_AGENT_DIR, "report_automator.py"),
        "description": "Legacy Notion-backed daily/weekly/monthly reports from mirrored dashboard data",
    },
    "beta-email-parse": {
        "script": os.path.join(_AGENT_DIR, "beta_email_parser.py"),
        "description": "Parse Resend beta key emails — extract names, cross-check Supabase, find hot leads",
    },
    "link-track": {
        "script": os.path.join(
            _AGENT_DIR, "..", "..", "GROWTH", "executions", "Marketing", "link_tracker.py"),
        "description": "Generate UTM-tracked Short.io links — see agents/TRACKED_LINKS.md",
    },
}


# ──────────────────────────────────────────────
# Task Resolution — free-text → registered task
# ──────────────────────────────────────────────
_TASK_KEYWORDS: dict[str, list[str]] = {
    "email-template-audit": ["template audit", "email template", "full template", "template content", "email body", "subject line audit", "template metrics"],
    "kpi-snapshot":  ["kpi snapshot", "notion snapshot", "dashboard mirror", "mirrored kpi", "notion kpi"],
    "license-track": ["license", "customer health", "activation", "device fleet", "validation error"],
    "funnel-calc":   ["funnel", "conversion rate", "drop-off", "cohort metric"],
    "ab-test":       ["a/b", "ab test", "experiment", "variant"],
    "attribution":   ["attribution", "first touch", "last touch", "marketing channel"],
    "conversion-track": ["conversion", "signup", "beta signup", "new user", "user_attribution"],
    "beta-email-parse": ["beta email", "resend beta", "beta key email", "hot lead", "cross-check", "sanity check"],
    "cohort":        ["cohort", "retention", "ltv", "churn", "lifetime"],
    "report":        ["report", "analytical report", "weekly report", "7 day report", "7-day report", "executive briefing", "business report", "strategic report"],
    "notion-report": ["notion report", "notion weekly report", "legacy report", "dashboard report"],
    "link-track":    ["utm", "short link", "link track"],
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
    print(f"  📊 {AGENT_NAME} Agent — Available Tasks")
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
    print(f"  📊 {AGENT_NAME} Agent — Status")
    print("=" * 60)
    print(f"\n  Tasks: {ready}/{len(TASKS)} ready")
    print(f"  APIs:  {', '.join(f'{k} ({v})' for k, v in sorted(apis.items()))}")
    for name, info in sorted(TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"  {exists} {name}")
    print()


# Default action for each task when Discord sends generic "run"
_DEFAULT_ACTIONS: dict[str, str] = {
    "email-template-audit": "summary",
    "kpi-snapshot":  "latest",
    "license-track": "dashboard",
    "funnel-calc":   "snapshot",
    "ab-test":       "list",
    "attribution":   "summary",
    "conversion-track": "recent",
    "beta-email-parse": "scan",
    "cohort":        "summary",
    "report":        "weekly",
    "notion-report": "weekly",
    "link-track":    "list-links",
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
        non_retry_exit_codes={2},
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
                        help="Task to run (e.g., kpi-snapshot)")
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
