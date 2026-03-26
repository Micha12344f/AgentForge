"""
campaigns.py — Email marketing campaign management layer.

CRUD for the 'campaigns' Notion database.
Consumed by email_send_sanity.py, Send_Emails.ipynb, and the E2E test.
"""

import os
import sys

# Ensure workspace root is importable
def _find_ws_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "shared")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
_MARKETING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_WS_ROOT, _MARKETING_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from email_marketing.config import query_db, add_row, update_row, CAMPAIGNS_READ_ONLY  # noqa: E402


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_campaign(row: dict) -> dict:
    """Map a raw Notion row to a clean campaign dict."""
    return {
        "id":             row.get("_id", ""),
        "name":           row.get("Name") or "",
        "status":         row.get("Status") or "",
        "send_frequency": int(row.get("Send Frequency") or 48),
        "campaign_score": int(row.get("Campaign Score") or 0),
        "priority":       row.get("Priority") or "Medium",
        "goal":           row.get("Goal") or "",
        "notes":          row.get("Notes") or "",
        "start_date":     row.get("Start Date") or "",
        "open_rate":      row.get("Open Rate") or 0,
        "click_rate":     row.get("Click Rate") or 0,
        "bounce_rate":    row.get("Bounce Rate") or 0,
        "reply_rate":     row.get("Reply Rate") or 0,
        "sequence_count": int(row.get("Sequence Count") or 0),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def read_campaigns(status_filter: str | None = None) -> list[dict]:
    """Return all campaigns, optionally filtered by Status string.

    Args:
        status_filter: e.g. "Active", "In building phase", "Discontinued".
                       Pass None to return all.

    Returns:
        List of campaign dicts with id, name, status, send_frequency,
        campaign_score, open_rate, click_rate, bounce_rate, reply_rate.
    """
    rows = query_db("campaigns")
    camps = [_parse_campaign(r) for r in rows]
    if status_filter:
        camps = [c for c in camps if c["status"] == status_filter]
    return camps


def create_campaign(
    name: str,
    send_frequency: int = 48,
    priority: str = "Medium",
    goal: str = "",
    notes: str = "",
    campaign_score: int = 0,
) -> dict:
    """Create a new campaign (status = 'In building phase').

    Returns:
        Minimal dict with id, name, status.
    """
    page = add_row("campaigns", {
        "Name":           name,
        "Status":         "In building phase",
        "Send Frequency": send_frequency,
        "Priority":       priority,
        "Goal":           goal,
        "Notes":          notes,
    })
    return {"id": page["id"], "name": name, "status": "In building phase"}


def activate_campaign(campaign_id: str, campaign_name: str = "") -> None:
    """Set campaign Status to 'Active'."""
    update_row(campaign_id, "campaigns", {"Status": "Active"})
    if campaign_name:
        print(f"  Activated: {campaign_name}")


def pause_campaign(campaign_id: str, campaign_name: str = "") -> None:
    """Set campaign Status to 'Discontinued'."""
    update_row(campaign_id, "campaigns", {"Status": "Discontinued"})
    if campaign_name:
        print(f"  Paused: {campaign_name}")
