"""
templates.py — Email template (sequence) management layer.

CRUD for the 'email_sequences' Notion database.
Consumed by email_send_sanity.py, Send_Emails.ipynb, and the E2E test.
"""

import os
import sys

# Ensure workspace root and Marketing dir are importable
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

import shared.notion_client as _nc  # noqa: E402
from email_marketing.config import query_db, add_row, TEMPLATES_READ_ONLY  # noqa: E402


# ── Patch relation extractor so Campaign/relation fields return IDs ──────────

def _patch_relation_extractor() -> None:
    original = _nc._extract_value

    def _patched(prop: dict):
        if prop.get("type") == "relation":
            return [item["id"] for item in prop.get("relation", [])]
        return original(prop)

    _nc._extract_value = _patched


_patch_relation_extractor()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_template(row: dict, seq_num: int = 0) -> dict:
    """Map a raw Notion row to a clean template dict."""
    return {
        "id":               row.get("_id", ""),
        "template_name":    row.get("Template") or row.get("Name") or "",
        "subject_line":     row.get("Subject Line") or "",
        "campaign_ids":     row.get("Campaign") or [],
        "status":           row.get("Status") or "",
        "trigger":          row.get("Trigger") or "",
        "send_delay_hours": int(row.get("Send Delay Hours") or 0),
        "notes":            row.get("Notes") or "",
        "open_rate":        row.get("Open Rate") or 0,
        "click_rate":       row.get("Click Rate") or 0,
        "bounce_rate":      row.get("Bounce Rate") or 0,
        "reply_rate":       row.get("Reply Rate") or 0,
        "_seq_num":         seq_num,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def read_templates(campaign_id: str | None = None) -> list[dict]:
    """Return all email templates, optionally filtered by campaign ID.

    Args:
        campaign_id: Notion page ID of a campaign. Pass None for all.

    Returns:
        List of template dicts.
    """
    rows = query_db("email_sequences")
    templates = []
    for i, row in enumerate(rows):
        t = _parse_template(row, seq_num=i + 1)
        if campaign_id and campaign_id not in (t["campaign_ids"] or []):
            continue
        templates.append(t)
    return templates


def list_templates_for_campaign(campaign_id: str) -> list[dict]:
    """Return templates for a campaign sorted by Send Delay Hours (ascending).

    Args:
        campaign_id: Notion page ID of the target campaign.

    Returns:
        Ordered list of template dicts with _seq_num set from sort position.
    """
    rows = query_db("email_sequences")
    matched = []
    for row in rows:
        ids = row.get("Campaign") or []
        if campaign_id in ids:
            matched.append(row)
    matched.sort(key=lambda r: int(r.get("Send Delay Hours") or 0))
    return [_parse_template(row, i + 1) for i, row in enumerate(matched)]


def create_template(
    campaign_id: str,
    template_name: str,
    subject_line: str,
    trigger: str = "Sequence",
    send_delay_hours: int = 24,
    notes: str = "",
) -> dict:
    """Create a new email template linked to a campaign.

    Args:
        campaign_id: Notion page ID of the parent campaign.
        template_name: Display name for the template.
        subject_line: Email subject (shown to recipients).

    Returns:
        Minimal dict with id, template_name, subject_line.
    """
    page = add_row("email_sequences", {
        "Template":         template_name,
        "Subject Line":     subject_line,
        "Campaign":         campaign_id,
        "Status":           "Active",
        "Trigger":          trigger,
        "Send Delay Hours": send_delay_hours,
        "Notes":            notes,
    })
    return {"id": page["id"], "template_name": template_name, "subject_line": subject_line}
