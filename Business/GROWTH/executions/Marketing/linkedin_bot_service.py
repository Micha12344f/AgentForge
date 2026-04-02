#!/usr/bin/env python3
"""
linkedin_bot_service.py

Always-on scheduler container for the LinkedIn -> Notion workflow.
Runs both Ryan and Mahmud accounts every 24 hours by default.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
import uvicorn


def _find_ws_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / "Business").is_dir() and (candidate / "shared").is_dir():
            return candidate
    raise RuntimeError("Cannot locate workspace root")


WS_ROOT = _find_ws_root()
sys.path.insert(0, str(WS_ROOT))

from shared.env_loader import load_env_for_source  # noqa: E402

load_env_for_source(__file__)

from shared.alerting import send_cron_failure, send_cron_success  # noqa: E402
from Business.GROWTH.executions.Marketing.linkedin_leads_workflow import (  # noqa: E402
    DEFAULT_ACCOUNTS,
    run_workflow,
)


UTC = timezone.utc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_accounts() -> list[str]:
    raw = os.getenv("LINKEDIN_BOT_ACCOUNTS", ",".join(DEFAULT_ACCOUNTS))
    accounts = [part.strip().lower() for part in raw.split(",") if part.strip()]
    return accounts or DEFAULT_ACCOUNTS.copy()


def _summary_text(result: dict[str, Any]) -> str:
    totals = result["totals"]
    lines = [
        f"Accounts: {', '.join(result['accounts'])}",
        f"Lookback: {result['days']} day(s)",
        (
            "Totals: "
            f"scraped={totals['scraped']} | added={totals['added']} | duplicates={totals['duplicates']} "
            f"| no_email={totals['no_email']} | failed={totals['failed']}"
        ),
    ]
    for item in result["per_account"]:
        lines.append(
            f"{item['label']}: scraped={item['scraped']} | added={item['added']} | "
            f"duplicates={item['duplicates']} | no_email={item['no_email']} | failed={item['failed']}"
        )
    lines.append(f"Elapsed: {result['elapsed_seconds']}s")
    return "\n".join(lines)


CONFIG = {
    "accounts": _env_accounts(),
    "days": int(os.getenv("LINKEDIN_BOT_LOOKBACK_DAYS", "7")),
    "interval_hours": int(os.getenv("LINKEDIN_BOT_INTERVAL_HOURS", "24")),
    "run_on_start": _env_bool("LINKEDIN_BOT_RUN_ON_START", True),
    "port": int(os.getenv("PORT", "8091")),
}

STATE: dict[str, Any] = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "last_success_at": None,
    "last_error": None,
    "last_result": None,
}

app = FastAPI()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": STATE["status"],
        "time": datetime.now(timezone.utc).isoformat(),
        "config": CONFIG,
        "state": STATE,
    }


def run_linkedin_cycle() -> None:
    started = datetime.now(timezone.utc)
    STATE.update(
        {
            "status": "running",
            "started_at": started.isoformat(),
            "finished_at": None,
            "last_error": None,
        }
    )
    print(f"[linkedin-bot] Cycle starting at {STATE['started_at']}", flush=True)

    try:
        result = run_workflow(
            accounts=CONFIG["accounts"],
            days=CONFIG["days"],
            headless=True,
        )
        summary = _summary_text(result)
        finished = datetime.now(timezone.utc)
        STATE.update(
            {
                "status": "ok",
                "finished_at": finished.isoformat(),
                "last_success_at": finished.isoformat(),
                "last_result": result,
            }
        )
        print(f"[linkedin-bot] Cycle complete\n{summary}", flush=True)
        try:
            send_cron_success("LinkedIn Leads Bot", summary, result["elapsed_seconds"])
        except Exception as alert_exc:
            print(f"[linkedin-bot] Success alert failed: {alert_exc}", flush=True)
    except Exception as exc:
        finished = datetime.now(timezone.utc)
        STATE.update(
            {
                "status": "failed",
                "finished_at": finished.isoformat(),
                "last_error": str(exc),
            }
        )
        print(f"[linkedin-bot] Cycle failed: {exc}", flush=True)
        try:
            send_cron_failure("LinkedIn Leads Bot", exc)
        except Exception as alert_exc:
            print(f"[linkedin-bot] Failure alert failed: {alert_exc}", flush=True)
        raise


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=UTC)
    next_run = datetime.now(timezone.utc) if CONFIG["run_on_start"] else None
    scheduler.add_job(
        run_linkedin_cycle,
        IntervalTrigger(hours=CONFIG["interval_hours"], timezone=UTC),
        id="linkedin_leads_cycle",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        next_run_time=next_run,
    )
    scheduler.start()
    print(
        "[linkedin-bot] Scheduler started "
        f"(accounts={CONFIG['accounts']}, days={CONFIG['days']}, interval={CONFIG['interval_hours']}h)",
        flush=True,
    )
    for job in scheduler.get_jobs():
        print(f"  {job.id}: next run = {job.next_run_time}", flush=True)
    return scheduler


if __name__ == "__main__":
    scheduler = start_scheduler()
    print(f"[linkedin-bot] Health endpoint on :{CONFIG['port']}/health", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=CONFIG["port"], log_level="warning")
