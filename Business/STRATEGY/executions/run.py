#!/usr/bin/env python3
"""
Business Strategist Agent — Task Dispatcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Routes strategy tasks to execution scripts.

Usage:
    python "Business Strategist Agent/run.py" --list-tasks
    python "Business Strategist Agent/run.py" --status
    python "Business Strategist Agent/run.py" --task competitor-track --action scan
    python "Business Strategist Agent/run.py" --task growth-model --action forecast
"""

import sys
import os
import subprocess
import argparse

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Ensure workspace root is on sys.path ──────────────────────
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(_AGENT_DIR)))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import log_task
from shared.api_registry import get_agent_apis
from shared.retry_executor import retry_subprocess, retry_call

AGENT_NAME = "Business Strategist"
AGENT_KEY = "business_strategist"

# ──────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────
TASKS: dict[str, dict] = {
    "competitor-track": {
        "script": os.path.join(_AGENT_DIR, "competitor_tracker.py"),
        "description": "Track and analyze competitors in the prop firm space",
    },
    "growth-model": {
        "script": os.path.join(_AGENT_DIR, "growth_model.py"),
        "description": "Run growth forecasting models and scenario analysis",
    },
    "retention-analyze": {
        "script": os.path.join(_AGENT_DIR, "retention_analyzer.py"),
        "description": "Analyze user retention, churn cohorts, and LTV",
    },
    "partnership-eval": {
        "script": os.path.join(_AGENT_DIR, "partnership_evaluator.py"),
        "description": "Evaluate and score potential IB/partnership opportunities",
    },
    "scrape-ib-pdfs": {
        "script": os.path.join(_AGENT_DIR, "scrape_ib_pdfs.py"),
        "description": "Scrape and parse IB agreement PDFs for terms extraction",
    },
    "market-sizing": {
        "script": os.path.join(_AGENT_DIR, "market_sizing_calculator.py"),
        "description": "Calculate TAM/SAM/SOM for prop firm market segments",
    },
    "market-scrape": {
        "script": os.path.join(_AGENT_DIR, "market_research_scraper.py"),
        "description": "Scrape prop firm market data and pricing intelligence",
    },
    "pricing-optimize": {
        "script": os.path.join(_AGENT_DIR, "pricing_optimizer.py"),
        "description": "Optimize pricing tiers and analyze price sensitivity",
    },
    "ib-revenue": {
        "script": os.path.join(_AGENT_DIR, "ib_revenue_model.py"),
        "description": "Model IB revenue projections and commission structures",
    },
    "scorecard": {
        "script": os.path.join(_AGENT_DIR, "strategic_scorecard.py"),
        "description": "Generate strategic scorecard with OKR progress and health metrics",
    },
    "link-track": {
        "script": os.path.join(
            _AGENT_DIR, "..", "..", "GROWTH", "executions", "Marketing", "link_tracker.py"),
        "description": "Generate UTM-tracked Short.io links — see agents/TRACKED_LINKS.md",
    },
    "legal-query": {
        "script": os.path.join(_AGENT_DIR, "legal_query_engine.py"),
        "description": "RAG-powered legal Q&A via NotebookLM (GDPR, FCA, IB, compliance)",
    },
    "gdpr-audit": {
        "script": os.path.join(_AGENT_DIR, "gdpr_compliance_checker.py"),
        "description": "Run UK GDPR compliance audit with scorecard and action items",
    },
    "fca-scan": {
        "script": os.path.join(_AGENT_DIR, "financial_promotions_auditor.py"),
        "description": "Scan marketing copy for FCA financial promotions violations",
    },
    "legal-setup": {
        "script": os.path.join(_AGENT_DIR, "setup_legal_notebook.py"),
        "description": "Set up the Hedge Edge Legal NotebookLM notebook with all legal sources",
    },
    # ── New Strategy Powerhouse Scripts ───────────
    "deep-research": {
        "script": os.path.join(_AGENT_DIR, "deep_researcher.py"),
        "description": "Multi-source deep research engine — research, briefs, analyses",
    },
    "competitor-intel": {
        "script": os.path.join(_AGENT_DIR, "competitor_intel.py"),
        "description": "Deep competitive intelligence — scans, deep-dives, feature matrix, moat",
    },
    "buffett-letters": {
        "script": os.path.join(_AGENT_DIR, "buffett_letters.py"),
        "description": "Download Buffett shareholder letters + extract business wisdom",
    },
    "trend-scan": {
        "script": os.path.join(_AGENT_DIR, "trend_scanner.py"),
        "description": "Industry, fintech, regulatory, and macro trend scanning",
    },
    "swot": {
        "script": os.path.join(_AGENT_DIR, "swot_analyzer.py"),
        "description": "SWOT, PESTEL, Porter's 5 Forces, Blue Ocean frameworks",
    },
    "investor-wisdom": {
        "script": os.path.join(_AGENT_DIR, "investor_wisdom.py"),
        "description": "Channel Buffett/Munger/Dalio/Thiel/Bezos wisdom on any topic",
    },
    # ── Product Sub-Department ────────────────────
    "product-roadmap": {
        "script": os.path.join(_AGENT_DIR, "Product", "roadmap_sync.py"),
        "description": "Sync Notion roadmap with GitHub Issues",
    },
    "product-bugs": {
        "script": os.path.join(_AGENT_DIR, "Product", "bug_triage_sync.py"),
        "description": "Triage GitHub Issues and sync to Notion bug tracker",
    },
    "product-qa": {
        "script": os.path.join(_AGENT_DIR, "Product", "qa_automator.py"),
        "description": "Run automated tests and report results",
    },
    "product-releases": {
        "script": os.path.join(_AGENT_DIR, "Product", "release_tracker.py"),
        "description": "Track releases through staging → QA → production",
    },
    "product-platforms": {
        "script": os.path.join(_AGENT_DIR, "Product", "platform_integrator.py"),
        "description": "Track MT4/cTrader integration progress",
    },
    "product-feedback": {
        "script": os.path.join(_AGENT_DIR, "Product", "user_feedback_sync.py"),
        "description": "Aggregate user feedback from Discord/email → Notion",
    },
    "app-deploy": {
        "script": os.path.join(_AGENT_DIR, "Product", "app_deployer.py"),
        "description": "Hedge Edge Electron app deploy pipeline — bump, build, release, verify",
    },
}


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def cmd_list_tasks() -> None:
    print("=" * 60)
    print(f"  🧠 {AGENT_NAME} Agent — Available Tasks")
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
    print(f"  🧠 {AGENT_NAME} Agent — Status")
    print("=" * 60)
    print(f"\n  Tasks: {ready}/{len(TASKS)} ready")
    print(f"  APIs:  {', '.join(f'{k} ({v})' for k, v in sorted(apis.items()))}")
    for name, info in sorted(TASKS.items()):
        exists = "✅" if os.path.isfile(info["script"]) else "❌"
        print(f"  {exists} {name}")
    print()


def cmd_run(task: str, action: str, extra: list[str]) -> None:
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
                        help="Task to run (e.g., competitor-track)")
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
