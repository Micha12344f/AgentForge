#!/usr/bin/env python3
"""
Email Send Service — Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APScheduler runs email_send at 07:00 and 19:00 GMT/UTC.
HTTP health check on $PORT for Railway probes.
"""

import os
import sys
import logging
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("email-send-service")

SCHEDULE_HOURS_UTC = "7,19"


# ──────────────────────────────────────────────
# Health check server
# ──────────────────────────────────────────────
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args):
        pass  # suppress access logs


def _start_health_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log.info("Health server listening on :%d", port)


# ──────────────────────────────────────────────
# Email send job
# ──────────────────────────────────────────────
def _run_email_send():
    """Execute the email send workflow with alerting."""
    start = datetime.now(timezone.utc)
    log.info("[%s] Email Send — Starting", start.strftime("%Y-%m-%d %H:%M UTC"))

    required = ["RESEND_API_KEY", "NOTION_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        log.error("Missing env vars: %s — skipping run", ", ".join(missing))
        return

    try:
        from email_send import run_email_send

        summary = run_email_send(dry_run=False)
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()

        try:
            from shared.alerting import send_cron_success
            desc = (
                f"Sent {summary['sent']} emails, {summary['errors']} errors.\n"
                f"Campaigns: {summary.get('per_campaign', {})}"
            )
            send_cron_success("Email Send", desc, elapsed)
        except Exception as e2:
            log.warning("Alert failed: %s", e2)

        log.info("Done — Sent=%d Errors=%d in %.1fs", summary["sent"], summary["errors"], elapsed)
    except Exception as e:
        log.error("Email Send failed: %s", e)
        traceback.print_exc()

        try:
            from shared.alerting import send_cron_failure
            send_cron_failure("Email Send", e)
        except Exception:
            try:
                from shared.resend_client import send_email

                send_email(
                    to="hedgeedge@outlook.com",
                    subject="[Email Send FAILED] Railway cron error",
                    text=f"Email Send cron failed at {datetime.now(timezone.utc).isoformat()}\n\nError: {e}",
                    from_addr="Hedge Edge Alerts <alerts@hedgedge.info>",
                    tags=[{"name": "type", "value": "error-alert"}],
                    include_unsubscribe=True,
                    respect_notion_unsubscribe=False,
                )
            except Exception:
                pass


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("Email Send Service starting")
    log.info("Schedule: 07:00 + 19:00 GMT daily")
    log.info("=" * 55)

    _start_health_server()

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        _run_email_send,
        trigger=CronTrigger(hour=SCHEDULE_HOURS_UTC, minute=0),
        id="email-send",
        name="Email Send → daily 07:00 + 19:00 GMT",
        misfire_grace_time=600,
    )

    log.info("Scheduler started — waiting for next trigger...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
