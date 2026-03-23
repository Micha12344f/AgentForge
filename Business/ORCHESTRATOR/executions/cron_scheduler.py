"""
cron_scheduler.py — Hedge Edge Unified Cron Scheduler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Single always-on container running ALL Railway cron jobs via APScheduler.
Runs one service instead of three separate Railway cron deployments.

Jobs (all times UTC):
  1. Email Send            → daily 09:00 + 21:00
  2. Daily Analytics       → daily 09:05
  3. Hourly Metrics Sync   → every hour :10

Health check: GET /health on $PORT
"""

import os
import sys
import importlib.util
import threading
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
import uvicorn

_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _WS)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS, ".env"), override=True)

from shared.alerting import send_alert

EMAIL_SEND_SCRIPT = os.path.join(_WS, "shared", "Email-Send-Service", "email_send.py")
DAILY_ANALYTICS_SCRIPT = os.path.join(_WS, "Business", "ANALYTICS", "executions", "daily_analytics.py")
HOURLY_METRICS_SCRIPT = os.path.join(_WS, "Business", "ANALYTICS", "executions", "hourly_metrics_sync.py")
# ── Health check API ──────────────────────────────────────────
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# ── Job runners ───────────────────────────────────────────────
def run_email_system():
    print(f"[CRON] Email Send starting — {datetime.now(timezone.utc).isoformat()}", flush=True)
    start = datetime.now(timezone.utc)
    try:
        spec = importlib.util.spec_from_file_location("email_send", EMAIL_SEND_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        summary = mod.run_email_send(dry_run=False)
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()

        desc = (
            f"Sent **{summary['sent']}** emails, **{summary['errors']}** errors in {elapsed:.1f}s\n"
            f"Campaigns: {summary.get('per_campaign', {})}"
        )
        send_alert("✅ Email Send Complete", desc, level="info")
        print(f"[CRON] Email Send done — Sent={summary['sent']} Errors={summary['errors']} in {elapsed:.1f}s", flush=True)
    except Exception as e:
        msg = f"Email Send FAILED: {e}"
        print(f"[CRON ERROR] {msg}", flush=True)
        try:
            send_alert("Cron Scheduler", msg, level="error")
        except Exception:
            pass


def run_daily_analytics():
    print(f"[CRON] Daily Analytics starting — {datetime.now(timezone.utc).isoformat()}", flush=True)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("daily_analytics", DAILY_ANALYTICS_SCRIPT)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run_daily_analytics(None)
    except Exception as e:
        msg = f"Daily analytics cron FAILED: {e}"
        print(f"[CRON ERROR] {msg}", flush=True)
        try:
            send_alert("Cron Scheduler", msg, level="error")
        except Exception:
            pass


def run_hourly_metrics():
    print(f"[CRON] Hourly Metrics Sync starting — {datetime.now(timezone.utc).isoformat()}", flush=True)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("hourly_metrics_sync", HOURLY_METRICS_SCRIPT)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run_hourly_sync()
    except Exception as e:
        msg = f"Hourly metrics sync FAILED: {e}"
        print(f"[CRON ERROR] {msg}", flush=True)
        try:
            send_alert("Cron Scheduler", msg, level="error")
        except Exception:
            pass


# ── Scheduler setup ───────────────────────────────────────────
def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")

    # Email sends: 09:00 and 21:00 UTC daily
    scheduler.add_job(run_email_system, CronTrigger(hour=9,  minute=0), id="email_am")
    scheduler.add_job(run_email_system, CronTrigger(hour=21, minute=0), id="email_pm")

    # Daily analytics: 09:05 UTC (after email send)
    scheduler.add_job(run_daily_analytics, CronTrigger(hour=9, minute=5), id="daily_analytics")

    # Hourly metrics sync: every hour at :10
    scheduler.add_job(run_hourly_metrics, CronTrigger(minute=10), id="hourly_metrics")

    scheduler.start()
    print("[CRON] Scheduler started — 4 jobs registered", flush=True)
    for job in scheduler.get_jobs():
        print(f"  {job.id}: next run = {job.next_run_time}", flush=True)
    return scheduler


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    scheduler = start_scheduler()

    print(f"[CRON] Health endpoint on :{port}/health", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
