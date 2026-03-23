"""
config.py — Shared constants and setup for the email-marketing execution layer.

Provides Notion client imports, database handles, and field-access rules
consumed by campaigns.py, templates.py, and leads.py.
"""

import os
import sys

# ── Workspace root — ensures shared.* is importable ──────────────────────────
def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(_WS_ROOT, ".env"))

from shared.notion_client import query_db, add_row, update_row, DATABASES, get_notion
from shared.alerting import send_alert

# ── Constants ─────────────────────────────────────────────────────────────────

# Score → segment mapping  (Cold 0-2, Warm 3-9, Hot 10+)
SEGMENTS = {"Cold": (0, 2), "Warm": (3, 9), "Hot": (10, float("inf"))}

# ── Read-only field lists (agents must NEVER write to these) ──────────────────
CAMPAIGNS_READ_ONLY = {
    "Sequence Count",
    "Open Rate", "Click Rate", "Bounce Rate", "Reply Rate",
}

TEMPLATES_READ_ONLY = {
    "Audience",
    "Open Rate", "Click Rate", "Unsubscribe Rate",
    "Total Sent", "Bounce Rate", "Reply Rate",
}

LEADS_READ_ONLY = {
    "Email", "First Name", "Last Name", "Source",
    "Unsubscribed", "Engagement Score", "Pipeline stage",
    "Last send", "Total Bounced", "Total Clicks",
    "Total Emails", "Total Opens", "Total Replies",
}
