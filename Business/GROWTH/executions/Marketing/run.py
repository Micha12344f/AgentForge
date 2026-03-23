#!/usr/bin/env python3
"""
Marketing Agent — Task Dispatcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Routes marketing tasks to execution scripts.

Usage:
    python "Marketing Agent/run.py" --list-tasks
    python "Marketing Agent/run.py" --status
    python "Marketing Agent/run.py" --task campaign-track --action report
    python "Marketing Agent/run.py" --task seo-track --action audit
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

AGENT_NAME = "Marketing"
AGENT_KEY = "marketing"

# ──────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────
TASKS: dict[str, dict] = {
    "campaign-track": {
        "script": os.path.join(_AGENT_DIR, "campaign_tracker.py"),
        "description": "Track ad campaign performance, spend, and ROI",
    },
    "email-sequences": {
        "script": os.path.join(_AGENT_DIR, "email_marketing", "email_sequence_manager.py"),
        "description": "Manage email sequences — create, schedule, analyze, and sanity-check due sends",
    },
    "waitlist-nurture": {
        "script": os.path.join(_AGENT_DIR, "email_marketing", "email_system.py"),
        "description": "Unified email system: Supabase sync → welcome → drip → enrich → Notion",
    },
    "seo-track": {
        "script": os.path.join(_AGENT_DIR, "seo_tracker.py"),
        "description": "Track keyword rankings, site audits, and SEO metrics",
    },
    "landing-page": {
        "script": os.path.join(_AGENT_DIR, "landing_page_optimizer.py"),
        "description": "Manage landing page A/B tests and conversion optimization",
    },
    "lead-gen": {
        "script": os.path.join(_AGENT_DIR, "lead_generator.py"),
        "description": "Ingest, score, segment, and route leads from all channels",
    },
    "newsletter": {
        "script": os.path.join(_AGENT_DIR, "newsletter_manager.py"),
        "description": "Plan, send, and analyze bi-weekly newsletters via Resend",
    },
    "link-track": {
        "script": os.path.join(_AGENT_DIR, "link_tracker.py"),
        "description": "Create UTM-tracked links, pull campaign performance & conversion rates",
    },
    "discord-manage": {
        "script": os.path.join(_AGENT_DIR, "discord_manager.py"),
        "description": "Discord server health, moderation, growth reports, channel activity",
    },
    "community-events": {
        "script": os.path.join(_AGENT_DIR, "community_events_manager.py"),
        "description": "Plan AMAs, workshops, webinars — schedule and track attendance",
    },
    "content-calendar": {
        "script": os.path.join(_AGENT_DIR, "content_calendar_sync.py"),
        "description": "Manage Notion content calendar — add, track, schedule content",
    },
    "content-create": {
        "script": os.path.join(_AGENT_DIR, "content_creator.py"),
        "description": "Create blog/video/social content, idea bank, and performance stats",
    },
    "feedback": {
        "script": os.path.join(_AGENT_DIR, "feedback_collector.py"),
        "description": "Collect and categorize community feedback — top requests and trends",
    },
    "instagram": {
        "script": os.path.join(_AGENT_DIR, "instagram_manager.py"),
        "description": "Instagram content scheduling, engagement tracking, hashtag research",
    },
    "linkedin": {
        "script": os.path.join(_AGENT_DIR, "linkedin_manager.py"),
        "description": "LinkedIn thought leadership, content planning, performance tracking",
    },
    "retention": {
        "script": os.path.join(_AGENT_DIR, "retention_engagement.py"),
        "description": "Community retention — at-risk members, re-engagement campaigns",
    },
    "onboarding": {
        "script": os.path.join(_AGENT_DIR, "user_onboarding.py"),
        "description": "Track signups, onboarding completion, stuck users",
    },
    "video-pipeline": {
        "script": os.path.join(_AGENT_DIR, "video_pipeline_manager.py"),
        "description": "Video production pipeline: script → film → edit → publish",
    },
    "x-post": {
        "script": os.path.join(_AGENT_DIR, "x_manager.py"),
        "description": "Post to X/Twitter with pre-send validation and scheduling",
    },
    "ticket-triage": {
        "script": os.path.join(_AGENT_DIR, "ticket_manager.py"),
        "description": "Support ticket triage, resolution tracking, overdue alerts",
    },
    "beta-email-parse": {
        "script": os.path.normpath(os.path.join(
            _AGENT_DIR, "..", "..", "..", "ANALYTICS", "executions", "beta_email_parser.py")),
        "description": "Parse Resend beta key emails — hot leads, name+email extraction, sanity check",
    },
}


# ──────────────────────────────────────────────
# Task Resolution — free-text → registered task
# ──────────────────────────────────────────────
_TASK_KEYWORDS: dict[str, list[str]] = {
    "campaign-track":    ["campaign", "ad ", "ads ", "spend", "roi", "ad campaign", "facebook", "google ads", "performance"],
    "email-sequences":   ["sequence", "email sequence", "automate email", "nurture email",
                          "manage sequence", "list sequence", "drip campaign", "manage drip",
                          "sanity check", "email sanity", "due emails", "should this email send"],
    "waitlist-nurture":  ["waitlist", "nurture", "welcome", "good morning", "beta launch",
                          "send email", "hype", "email", "morning email", "blast", "announce",
                          "beta", "launch email", "drip", "email drip"],
    "seo-track":         ["seo", "keyword", "ranking", "backlink", "search engine", "organic"],
    "landing-page":      ["landing page", "a/b test", "conversion", "cro", "page optimiz"],
    "lead-gen":          ["lead gen", "lead generation", "find lead", "best lead", "top lead",
                          "score lead", "segment", "ingest lead", "leads", "generate"],
    "newsletter":        ["newsletter", "digest", "bi-weekly", "roundup"],
    "link-track":        ["utm", "short link", "link track", "track link", "shortio", "short.io",
                          "tracking link", "generate link", "tracking"],
    "discord-manage":    ["discord", "server health", "moderation", "channel activity", "discord server"],
    "community-events":  ["ama", "workshop", "webinar", "community event", "event"],
    "content-calendar":  ["content calendar", "schedule content", "editorial", "calendar"],
    "content-create":    ["blog", "article", "create content", "idea bank", "content idea"],
    "feedback":          ["feedback", "feature request", "user feedback", "community feedback"],
    "instagram":         ["instagram", "insta", "ig ", "reels", "stories"],
    "linkedin":          ["linkedin", "thought leadership", "professional network"],
    "retention":         ["retention", "churn", "at-risk", "re-engage", "win back"],
    "onboarding":        ["onboarding", "signup", "new user", "stuck user", "activation"],
    "video-pipeline":    ["video", "youtube", "script to film", "production pipeline"],
    "x-post":            ["tweet", "x post", "twitter", "post to x"],
    "ticket-triage":     ["ticket", "support ticket", "triage", "overdue ticket"],    "beta-email-parse": ["beta email", "resend beta", "beta key email", "hot lead", "interested lead"],}


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
    print(f"  📣 {AGENT_NAME} Agent — Available Tasks")
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
    print(f"  📣 {AGENT_NAME} Agent — Status")
    print("=" * 60)
    print(f"\n  Tasks: {ready}/{len(TASKS)} ready")
    print(f"  APIs:  {', '.join(f'{k} ({v})' for k, v in sorted(apis.items()))}")
    for name, info in sorted(TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"  {exists} {name}")
    print()


# Default action for each task when Discord sends generic "run"
_DEFAULT_ACTIONS: dict[str, str] = {
    "campaign-track":   "report",
    "email-sequences":  "list-sequences",
    "waitlist-nurture": "run",
    "seo-track":        "audit",
    "landing-page":     "status",
    "lead-gen":         "pipeline-report",
    "newsletter":       "draft",
    "link-track":       "list-links",
    "discord-manage":   "server-health",
    "community-events": "upcoming",
    "content-calendar": "calendar-report",
    "content-create":   "list-drafts",
    "feedback":         "feedback-report",
    "instagram":        "engagement-report",
    "linkedin":         "performance-report",
    "retention":        "retention-report",
    "onboarding":       "onboarding-status",
    "video-pipeline":   "pipeline-report",
    "x-post":           "dry-run",
    "ticket-triage":    "ticket-report",
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
                        help="Task to run (e.g., campaign-track, seo-track)")
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
