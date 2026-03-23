#!/usr/bin/env python3
"""
resend_beta_key_webhook.py — Resend Webhook Handler for Beta Key Emails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processes Resend `email.sent` webhook events for the subject:
    "🔑 Your Free Beta License Key — Hedge Edge"

Actions on match:
  1. Extract email + first name from webhook payload
  2. Add/update the user in Notion `beta_waitlist` database
  3. Check if user exists in `leads_crm`; if not, create a lead
  4. Post a Discord alert to #log-alerts

Usage (standalone test):
    python resend_beta_key_webhook.py --test --email "user@example.com" --name "Jane"

Usage (as module — called from a web framework route):
    from Business.GROWTH.executions.Marketing.resend_beta_key_webhook import handle_webhook_event
    result = handle_webhook_event(event_payload)
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone

# ── Workspace root discovery ──
def _find_ws_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "shared")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"), override=True)

from shared.notion_client import add_row, query_db, update_row
from shared.discord_client import send_embed

# ── Constants ──
TARGET_SUBJECT = "\U0001f511 Your Free Beta License Key \u2014 Hedge Edge"
DISCORD_LOG_ALERTS_CHANNEL = "1477095672800083989"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extract_first_name_from_to(to_field) -> str:
    """
    Try to extract a first name from the 'to' field.
    Resend sends 'to' as a list of strings like ["Jane Doe <jane@example.com>"] or ["jane@example.com"].
    """
    if isinstance(to_field, list) and to_field:
        addr = to_field[0]
    elif isinstance(to_field, str):
        addr = to_field
    else:
        return ""

    # Format: "Jane Doe <jane@example.com>"
    if "<" in addr:
        name_part = addr.split("<")[0].strip()
        if name_part:
            return name_part.split()[0]

    # Fallback: use email prefix
    email = addr.strip().strip("<>")
    return email.split("@")[0].capitalize()


def _extract_email_from_to(to_field) -> str:
    """Extract plain email from Resend 'to' field."""
    if isinstance(to_field, list) and to_field:
        addr = to_field[0]
    elif isinstance(to_field, str):
        addr = to_field
    else:
        return ""

    if "<" in addr and ">" in addr:
        return addr.split("<")[1].split(">")[0].strip()
    return addr.strip()


def _find_in_beta_waitlist(email: str) -> dict | None:
    """Check if user already exists in beta_waitlist by email."""
    rows = query_db("beta_waitlist")
    email_lower = email.lower().strip()
    for row in rows:
        if (row.get("Email") or "").lower().strip() == email_lower:
            return row
    return None


def _find_in_leads(email: str) -> dict | None:
    """Check if user already exists in leads_crm by email."""
    rows = query_db("leads_crm")
    email_lower = email.lower().strip()
    for row in rows:
        if (row.get("Email") or "").lower().strip() == email_lower:
            return row
    return None


def _add_to_beta_waitlist(email: str, first_name: str) -> dict:
    """Add a new entry to beta_waitlist or update existing."""
    existing = _find_in_beta_waitlist(email)
    if existing:
        print(f"  \u2139\ufe0f  User {email} already in beta_waitlist — updating Beta Key Sent")
        result = update_row(existing["_id"], "beta_waitlist", {
            "Beta Key Sent": True,
            "Key Sent Date": TODAY,
        })
        return {"action": "updated", "page_id": existing["_id"], "result": result}

    print(f"  \u2795  Adding {email} to beta_waitlist")
    result = add_row("beta_waitlist", {
        "Name": first_name or email.split("@")[0],
        "First Name": first_name,
        "Email": email,
        "Source": "Landing Page",
        "Priority": "P2",
        "Beta Key Sent": True,
        "Key Sent Date": TODAY,
        "Lifecycle Owner": "Marketing",
    })
    return {"action": "created", "page_id": result.get("id"), "result": result}


def _ensure_in_leads(email: str, first_name: str) -> dict:
    """Check leads_crm for this email; add if missing."""
    existing = _find_in_leads(email)
    if existing:
        print(f"  \u2139\ufe0f  User {email} already in leads_crm — skipping")
        return {"action": "already_exists", "page_id": existing["_id"]}

    print(f"  \u2795  Adding {email} to leads_crm")
    result = add_row("leads_crm", {
        "Subject": first_name or email.split("@")[0],
        "First Name": first_name,
        "Email": email,
        "Source": "Beta Waitlist",
    })
    return {"action": "created", "page_id": result.get("id"), "result": result}


def _send_discord_alert(email: str, first_name: str, waitlist_result: dict, leads_result: dict):
    """Post a rich embed to #log-alerts."""
    fields = [
        {"name": "Email", "value": email, "inline": True},
        {"name": "First Name", "value": first_name or "(unknown)", "inline": True},
        {"name": "Waitlist", "value": waitlist_result["action"], "inline": True},
        {"name": "Leads CRM", "value": leads_result["action"], "inline": True},
    ]
    send_embed(
        channel_id=DISCORD_LOG_ALERTS_CHANNEL,
        title="\U0001f511 Beta Key Email Sent",
        description=f"Resend confirmed beta key email delivered to **{email}**",
        color=0x22C55E,
        fields=fields,
    )
    print(f"  \u2705  Discord alert sent to #log-alerts")


def handle_webhook_event(event: dict) -> dict:
    """
    Process a Resend webhook event payload.

    Args:
        event: The full webhook JSON body from Resend

    Returns:
        dict with processing results
    """
    event_type = event.get("type", "")
    data = event.get("data", {})
    subject = data.get("subject", "")

    # Only process email.sent for our target subject
    if event_type != "email.sent":
        return {"status": "ignored", "reason": f"event type {event_type} not handled"}

    if subject != TARGET_SUBJECT:
        return {"status": "ignored", "reason": f"subject mismatch: {subject!r}"}

    # Extract user details
    to_field = data.get("to", [])
    email = _extract_email_from_to(to_field)
    first_name = _extract_first_name_from_to(to_field)

    if not email:
        return {"status": "error", "reason": "could not extract email from payload"}

    print(f"\n\U0001f511 Beta key email sent → {email} ({first_name})")

    # Step 1: Add/update beta_waitlist
    waitlist_result = _add_to_beta_waitlist(email, first_name)
    print(f"  Waitlist: {waitlist_result['action']}")

    # Step 2: Ensure user is in leads_crm
    leads_result = _ensure_in_leads(email, first_name)
    print(f"  Leads: {leads_result['action']}")

    # Step 3: Discord alert
    _send_discord_alert(email, first_name, waitlist_result, leads_result)

    return {
        "status": "processed",
        "email": email,
        "first_name": first_name,
        "waitlist": waitlist_result["action"],
        "leads": leads_result["action"],
    }


def _build_mock_event(email: str, first_name: str) -> dict:
    """Build a mock Resend email.sent webhook payload for testing."""
    return {
        "type": "email.sent",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "email_id": "test-mock-00000",
            "from": "Hedge Edge <hello@hedgedge.info>",
            "to": [f"{first_name} <{email}>"],
            "subject": TARGET_SUBJECT,
            "tags": {"category": "beta_key"},
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Resend Beta Key Webhook Handler")
    parser.add_argument("--test", action="store_true", help="Run with a mock event")
    parser.add_argument("--email", default="hedgedge@hedgedge.info", help="Test email")
    parser.add_argument("--name", default="TestUser", help="Test first name")
    args = parser.parse_args()

    if args.test:
        event = _build_mock_event(args.email, args.name)
        print(f"Mock event:\n{json.dumps(event, indent=2)}\n")
        result = handle_webhook_event(event)
        print(f"\nResult:\n{json.dumps(result, indent=2)}")
    else:
        print("Use --test to run with a mock event, or import handle_webhook_event for production use.")


if __name__ == "__main__":
    main()
