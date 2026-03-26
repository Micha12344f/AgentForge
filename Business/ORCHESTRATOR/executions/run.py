#!/usr/bin/env python3
"""
Hedge Edge — Orchestrator Dispatcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Master entry point. Routes tasks to the correct agent's run.py.

Usage:
    python "Orchestrator Agent/run.py" --agent sales --task crm-sync --action list
    python "Orchestrator Agent/run.py" --agent analytics --task kpi-snapshot --action latest
    python "Orchestrator Agent/run.py" --list-agents
    python "Orchestrator Agent/run.py" --list-tasks sales
"""

import sys
import os
import subprocess
import argparse
import re
from datetime import datetime

# Ensure Unicode output works on Windows (cp1252 doesn't support emojis)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Ensure workspace root is on sys.path ──────────────────────
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import log_task
from shared.api_registry import get_agent_apis, can_access
from shared.retry_executor import retry_subprocess, retry_call

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────────
# Internal Task Registry (Orchestrator's own skills)
# ──────────────────────────────────────────────
INTERNAL_TASKS: dict[str, dict] = {
    "route": {
        "script": os.path.join(_AGENT_DIR, "agent_router.py"),
        "description": "Classify intent and route requests to the correct agent",
    },
    "coordinate": {
        "script": os.path.join(_AGENT_DIR, "cross_agent_coordinator.py"),
        "description": "Run multi-agent workflows and coordinate cross-agent tasks",
    },
    "decompose": {
        "script": os.path.join(_AGENT_DIR, "task_decomposer.py"),
        "description": "Break complex requests into atomic sub-tasks with dependency DAG",
    },
    "status": {
        "script": os.path.join(_AGENT_DIR, "status_aggregator.py"),
        "description": "Aggregate status across all agents and Notion databases",
    },
    "vps-monitor": {
        "script": os.path.join(_AGENT_DIR, "vps_monitor.py"),
        "description": "Check hedge-vps status, WSL cron, remote logs, and bot alerts",
    },
    "link-track": {
        "script": os.path.join(_AGENT_DIR, "..", "..", "GROWTH", "executions", "Marketing", "link_tracker.py"),
        "description": "Generate UTM-tracked Short.io links — delegated from Marketing Agent",
    },
}

# ──────────────────────────────────────────────
# Agent Registry
# ──────────────────────────────────────────────
AGENTS: dict[str, dict] = {
    "analytics": {
        "folder": os.path.join("Business", "ANALYTICS", "executions"),
        "key": "analytics",
        "description": "KPI dashboards, funnel analytics, and performance metrics",
    },
    "business-strategist": {
        "folder": os.path.join("Business", "STRATEGY", "executions"),
        "key": "business_strategist",
        "description": "Competitive intelligence, growth strategy, partnerships, revenue",
    },
    "community-manager": {
        "folder": os.path.join("Business", "GROWTH", "executions", "Marketing"),
        "key": "community_manager",
        "description": "Feedback collection, support triage, community events",
    },
    "content-engine": {
        "folder": os.path.join("Business", "GROWTH", "executions", "Marketing"),
        "key": "content_engine",
        "description": "Content scheduling, video production pipeline",
    },
    "finance": {
        "folder": os.path.join("Business", "FINANCE", "executions"),
        "key": "finance",
        "description": "IB commissions, MRR tracking, P&L, expenses",
    },
    "marketing": {
        "folder": os.path.join("Business", "GROWTH", "executions", "Marketing"),
        "key": "marketing",
        "description": "Ad campaigns, email marketing, SEO strategy, UTM link tracking",
    },
    "product": {
        "folder": os.path.join("Business", "STRATEGY", "executions", "Product"),
        "key": "product",
        "description": "Bug triage, feature roadmap, release management",
    },
    "sales": {
        "folder": os.path.join("Business", "GROWTH", "executions", "Sales"),
        "key": "sales",
        "description": "CRM management, demo tracking, proposal generation",
    },
    "orchestrator": {
        "folder": os.path.join("Business", "ORCHESTRATOR", "executions"),
        "key": "orchestrator",
        "description": "Master dispatcher and status reporting",
    },
}


def _agent_run_py(agent_slug: str) -> str:
    """Return the absolute path to an agent's run.py."""
    info = AGENTS[agent_slug]
    return os.path.join(_WORKSPACE, info["folder"], "run.py")


# ──────────────────────────────────────────────
# Task Resolution — map free-text to registered tasks
# ──────────────────────────────────────────────

# Keyword → task mappings per agent (lowercase).
# Each entry: keywords that, when found in user text, indicate this task.
_TASK_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "marketing": {
        "campaign-track":    ["campaign", "ad ", "ads ", "spend", "roi", "ad campaign", "facebook", "google ads", "performance"],
        "email-sequences":   ["sequence", "email sequence", "automate email", "nurture email",
                              "manage sequence", "list sequence", "drip campaign", "manage drip"],
        "waitlist-nurture":  ["waitlist", "nurture", "welcome", "onboard", "good morning", "beta launch",
                              "send email", "hype", "email", "morning email", "blast", "announce",
                              "beta", "launch email", "drip", "email drip"],
        "seo-track":         ["seo", "keyword", "ranking", "backlink", "search engine", "organic"],
        "landing-page":      ["landing page", "a/b test", "conversion", "cro", "page optimiz"],
        "lead-gen":          ["lead gen", "lead generation", "find lead", "best lead", "top lead",
                              "score lead", "segment", "ingest lead", "leads", "generate"],
        "newsletter":        ["newsletter", "digest", "bi-weekly", "roundup"],
        "link-track":        ["utm", "short link", "link track", "track link", "shortio", "short.io",
                              "tracking link", "generate link", "tracking"],
    },
    "sales": {
        "crm-sync":          ["crm", "pipeline report", "update stage", "add lead", "sync",
                              "update", "stage", "lead stage"],
        "demo-track":        ["demo", "booking", "demo track", "scheduled demo"],
        "proposal":          ["proposal", "pitch", "quote", "offer", "contract"],
        "call-schedule":     ["schedule call", "cal.com", "book call", "follow-up call", "call schedule",
                              "schedule", "book"],
        "lead-qualify":      ["qualify", "bant", "score", "lead quality", "qualify lead"],
        "pipeline":          ["pipeline", "stage track", "velocity", "forecast", "deal"],
        "call-transcribe":   ["transcri", "whisper", "recording", "call summary", "call note"],
        "link-track":        ["utm", "short link", "link track", "track link", "shortio", "link"],
    },
    "analytics": {
        "kpi-snapshot":      ["kpi", "snapshot", "metric", "weekly report", "dashboard"],
        "funnel-calc":       ["funnel", "conversion rate", "drop-off", "cohort metric"],
        "ab-test":           ["a/b", "ab test", "experiment", "variant"],
        "attribution":       ["attribution", "first touch", "last touch", "marketing channel"],
        "cohort":            ["cohort", "retention", "ltv", "churn", "lifetime"],
        "report":            ["report", "daily report", "monthly report", "business report"],
        "link-track":        ["utm", "short link", "link track", "track link", "link"],
    },
}

_WORD_SPLIT = re.compile(r"[^a-z0-9]+")


def resolve_task(agent_slug: str, raw_task: str, registered_tasks: list[str] | None = None) -> str:
    """
    Resolve a free-text task description to a registered task name.

    If raw_task already matches a registered task, return it unchanged.
    Otherwise, use keyword scoring to find the best match.

    Args:
        agent_slug: Agent key (e.g. "marketing", "sales")
        raw_task: The user's raw task text
        registered_tasks: Optional list of valid task names (for agents not in _TASK_KEYWORDS)

    Returns:
        The resolved task name (best match).
    """
    lower = raw_task.lower().strip()

    # Check if registered_tasks were provided, or build from keywords
    if registered_tasks and lower in registered_tasks:
        return lower
    if not registered_tasks:
        kw_map = _TASK_KEYWORDS.get(agent_slug, {})
        registered_tasks = list(kw_map.keys())
        if lower in registered_tasks:
            return lower

    # Keyword scoring
    kw_map = _TASK_KEYWORDS.get(agent_slug, {})
    if not kw_map:
        return raw_task  # no keywords mapped — pass through

    scores: dict[str, float] = {}
    for task_name, keywords in kw_map.items():
        score = 0.0
        for kw in keywords:
            if kw in lower:
                # Longer keywords score higher (more specific)
                score += len(kw.split())
        scores[task_name] = score

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best]

    if best_score > 0:
        print(f"  [resolve] \"{raw_task[:60]}\" -> {best} (score {best_score:.0f})")
        return best

    # Fallback: no keyword match — return raw (will fail at agent level with available-tasks hint)
    return raw_task


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def cmd_list_internal_tasks() -> None:
    """Print all Orchestrator internal tasks."""
    print("=" * 65)
    print("  🏢 ORCHESTRATOR — Internal Tasks")
    print("=" * 65)
    for name, info in sorted(INTERNAL_TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"\n  {exists} {name}")
        print(f"     {info['description']}")
    print(f"\n{'─' * 65}")
    print(f"  {len(INTERNAL_TASKS)} internal tasks registered")


def cmd_run_internal(task: str, action: str, extra: list[str]) -> None:
    """Run an Orchestrator internal task."""
    info = INTERNAL_TASKS.get(task)
    if not info:
        print(f"❌ Unknown internal task: {task}")
        print(f"   Available: {', '.join(sorted(INTERNAL_TASKS.keys()))}")
        sys.exit(1)
    script = info["script"]
    if not os.path.isfile(script):
        print(f"❌ Script not found: {script}")
        sys.exit(1)
    cmd = [sys.executable, script, "--action", action, *extra]
    result = retry_subprocess(cmd, max_retries=2, task_label=f"Orchestrator/internal:{task}/{action}")
    status = "Complete" if result.returncode == 0 else "Error"
    retry_call(
        log_task,
        "Orchestrator", f"internal:{task}/{action}", status, "P2",
        f"Ran {task} --action {action}",
        max_retries=2,
        task_label=f"Notion log: Orchestrator/internal:{task}",
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


def cmd_list_agents() -> None:
    """Print all registered agents and their API access."""
    print("=" * 65)
    print("  🏢 HEDGE EDGE — AGENT ROSTER")
    print("=" * 65)
    for slug, info in sorted(AGENTS.items()):
        apis = get_agent_apis(info["key"])
        api_list = ", ".join(sorted(apis.keys())) if apis else "(none)"
        print(f"\n  {slug}")
        print(f"    {info['description']}")
        print(f"    APIs: {api_list}")
    print(f"\n{'─' * 65}")
    print(f"  {len(AGENTS)} agents registered")


def cmd_list_tasks(agent_slug: str) -> None:
    """Delegate to the agent's run.py --list-tasks."""
    run_py = _agent_run_py(agent_slug)
    if not os.path.isfile(run_py):
        print(f"❌ No run.py found for agent '{agent_slug}' at {run_py}")
        sys.exit(1)
    subprocess.run([sys.executable, run_py, "--list-tasks"], check=False)


def cmd_dispatch(agent_slug: str, task: str, action: str, extra: list[str]) -> None:
    """Route a task to the target agent's run.py."""
    info = AGENTS.get(agent_slug)
    if not info:
        print(f"❌ Unknown agent: {agent_slug}")
        print(f"   Available: {', '.join(sorted(AGENTS.keys()))}")
        sys.exit(1)

    run_py = _agent_run_py(agent_slug)
    if not os.path.isfile(run_py):
        print(f"❌ No run.py found for agent '{agent_slug}' at {run_py}")
        sys.exit(1)

    # Validate the agent has Notion access (minimum requirement)
    if not can_access(info["key"], "notion", "read"):
        print(f"❌ Agent '{agent_slug}' has no Notion access — cannot execute tasks.")
        sys.exit(1)

    # ── Resolve free-text task to registered task name ──
    task = resolve_task(agent_slug, task)

    # Build the subprocess command
    cmd = [sys.executable, run_py, "--task", task, "--action", action, *extra]

    print(f"🚀 Dispatching: {agent_slug} → {task} → {action}")
    print(f"   Command: {' '.join(cmd)}")
    print("─" * 65)

    started = datetime.now()
    result = retry_subprocess(cmd, max_retries=2, task_label=f"Orchestrator/dispatch:{agent_slug}/{task}")
    elapsed = (datetime.now() - started).total_seconds()

    status = "Complete" if result.returncode == 0 else "Error"
    error_msg = f"exit code {result.returncode}" if result.returncode != 0 else ""

    # Audit to Notion task_log
    retry_call(
        log_task,
        agent="Orchestrator",
        task=f"dispatch:{agent_slug}/{task}/{action}",
        status=status,
        priority="P2",
        output_summary=f"Dispatched to {info['folder']} in {elapsed:.1f}s",
        error=error_msg,
        max_retries=2,
        task_label=f"Notion log: Orchestrator/dispatch:{agent_slug}",
    )

    if result.returncode != 0:
        print(f"\n❌ Agent returned exit code {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"\n✅ Done in {elapsed:.1f}s")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hedge Edge — Orchestrator Dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python "Orchestrator Agent/run.py" --list-agents
  python "Orchestrator Agent/run.py" --list-tasks sales
  python "Orchestrator Agent/run.py" --agent sales --task crm-sync --action pipeline-report
  python "Orchestrator Agent/run.py" --agent analytics --task kpi-snapshot --action weekly-report
        """,
    )
    parser.add_argument("--list-agents", action="store_true",
                        help="Show all registered agents")
    parser.add_argument("--list-internal", action="store_true",
                        help="Show Orchestrator internal tasks")
    parser.add_argument("--internal-task", metavar="TASK",
                        help="Run an Orchestrator internal task (route, coordinate, decompose, status, vps-monitor)")
    parser.add_argument("--list-tasks", metavar="AGENT",
                        help="Show available tasks for an agent")
    parser.add_argument("--agent", metavar="AGENT",
                        help="Target agent slug (e.g., sales, analytics)")
    parser.add_argument("--task", metavar="TASK",
                        help="Task name to run (e.g., crm-sync, kpi-snapshot)")
    parser.add_argument("--action", metavar="ACTION",
                        help="Action within the task (passed to execution script)")

    args, extra = parser.parse_known_args()

    if args.list_agents:
        cmd_list_agents()
    elif args.list_internal:
        cmd_list_internal_tasks()
    elif args.internal_task and args.action:
        cmd_run_internal(args.internal_task, args.action, extra)
    elif args.list_tasks:
        slug = args.list_tasks.lower().replace("_", "-").replace(" ", "-")
        if slug not in AGENTS:
            print(f"❌ Unknown agent: {slug}")
            print(f"   Available: {', '.join(sorted(AGENTS.keys()))}")
            sys.exit(1)
        cmd_list_tasks(slug)
    elif args.agent and args.task and args.action:
        slug = args.agent.lower().replace("_", "-").replace(" ", "-")
        if slug not in AGENTS:
            print(f"❌ Unknown agent: {slug}")
            print(f"   Available: {', '.join(sorted(AGENTS.keys()))}")
            sys.exit(1)
        cmd_dispatch(slug, args.task, args.action, extra)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
