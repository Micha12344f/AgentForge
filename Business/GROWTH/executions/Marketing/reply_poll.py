"""
Hedge Edge — Reply Polling
━━━━━━━━━━━━━━━━━━━━━━━━━━
Polls Resend's inbound email API for new lead replies and processes them:
  1. Fetches recent inbound emails from Resend (/emails/receiving)
  2. Skips already-processed (exists in lead_replies) and automated senders
  3. Finds matching email_logs row → sets Replied + Delivered + Opened
  4. Creates a lead_replies row in Notion
  5. Forwards notification to hedgeedge@outlook.com

Usage:
    python Business/GROWTH/executions/Marketing/reply_poll.py   # one-shot run
"""

import os
import sys
import re
import logging
import requests
from datetime import datetime, timezone

_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, _WS)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS, ".env"), override=True)

from shared.notion_client import (
    DATABASES, query_db, add_row, update_row, notion_request,
)

# ── Config ────────────────────────────────────────────────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_BASE = "https://api.resend.com"

EMAIL_LOGS_DB_ID = DATABASES["email_logs"]
LEAD_REPLIES_DB_ID = DATABASES["lead_replies"]

NOTION_API_KEY = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"
NOTION_BASE = "https://api.notion.com/v1"

log = logging.getLogger("reply-poll")

# ── Filters ───────────────────────────────────────────────────────────────────
OOO_PATTERNS = [
    "out of office", "automatic reply", "auto-reply", "ooo:",
    "abwesenheit", "absence", "away from",
]

IGNORED_SENDER_DOMAINS = {
    "github.com", "email.github.com", "x.com", "twitter.com",
    "facebookmail.com", "linkedin.com", "accounts.google.com",
    "noreply.google.com", "hedgedge.info",
}

IGNORED_SENDER_PREFIXES = [
    "noreply@", "no-reply@", "notify@", "notifications@",
    "mailer-daemon@", "alerts@",
]

PREFIX_RE = re.compile(r"^(?:(?:re|fwd?|aw|sv|tr|rif|r)\s*(?:\[\d+\])?\s*:\s*)+", re.IGNORECASE)


# ── Resend helpers ────────────────────────────────────────────────────────────

def _resend_headers():
    return {"Authorization": f"Bearer {RESEND_API_KEY}"}


def list_inbound_emails(limit: int = 50) -> list[dict]:
    """Fetch recent inbound emails from Resend."""
    resp = requests.get(
        f"{RESEND_BASE}/emails/receiving",
        headers=_resend_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])[:limit]


def get_inbound_email(email_id: str) -> dict:
    """Fetch full inbound email details (body, headers)."""
    resp = requests.get(
        f"{RESEND_BASE}/emails/receiving/{email_id}",
        headers=_resend_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Notion helpers ────────────────────────────────────────────────────────────

def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def get_processed_resend_ids() -> set[str]:
    """Return set of Resend IDs already in lead_replies (to skip duplicates)."""
    rows = query_db("lead_replies", page_size=100)
    return {r.get("Resend ID", "") for r in rows if r.get("Resend ID")}


def find_email_log(from_email: str, subject_clean: str, in_reply_to: str = "") -> dict | None:
    """
    Find the matching email_logs row using 3 strategies:
      1. In-Reply-To header → extract UUID → match Resend ID
      2. Email + cleaned subject
      3. Email only (fallback)
    Returns {"_id": page_id, "match": method} or None.
    """
    headers = _notion_headers()

    # Strategy 1: In-Reply-To header → UUID match
    if in_reply_to:
        uuid_match = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            in_reply_to,
        )
        if uuid_match:
            candidate_id = uuid_match.group(1)
            resp = notion_request(
                "post",
                f"{NOTION_BASE}/databases/{EMAIL_LOGS_DB_ID}/query",
                headers=headers,
                json={
                    "filter": {"property": "Resend ID", "rich_text": {"equals": candidate_id}},
                    "page_size": 1,
                },
            )
            if resp.ok:
                data = resp.json()
                if data.get("results"):
                    return {"_id": data["results"][0]["id"], "match": "in_reply_to"}

    # Strategy 2: Email + cleaned subject
    if subject_clean:
        resp = notion_request(
            "post",
            f"{NOTION_BASE}/databases/{EMAIL_LOGS_DB_ID}/query",
            headers=headers,
            json={
                "filter": {
                    "and": [
                        {"property": "Email", "email": {"equals": from_email}},
                        {"property": "Subject", "rich_text": {"contains": subject_clean[:50]}},
                    ]
                },
                "sorts": [{"property": "Timestamp", "direction": "descending"}],
                "page_size": 1,
            },
        )
        if resp.ok:
            data = resp.json()
            if data.get("results"):
                return {"_id": data["results"][0]["id"], "match": "email_subject"}

    # Strategy 3: Email only
    resp = notion_request(
        "post",
        f"{NOTION_BASE}/databases/{EMAIL_LOGS_DB_ID}/query",
        headers=headers,
        json={
            "filter": {"property": "Email", "email": {"equals": from_email}},
            "sorts": [{"property": "Timestamp", "direction": "descending"}],
            "page_size": 1,
        },
    )
    if resp.ok:
        data = resp.json()
        if data.get("results"):
            return {"_id": data["results"][0]["id"], "match": "email_only"}

    return None


def set_replied_checkboxes(page_id: str) -> bool:
    """Set Replied + Delivered + Opened = True on email_logs row."""
    try:
        update_row(page_id, "email_logs", {
            "Replied": True,
            "Delivered": True,
            "Opened": True,
        })
        return True
    except Exception as e:
        log.error("Failed to update replied checkboxes on %s: %s", page_id, e)
        return False


def create_lead_reply(
    resend_id: str,
    from_email: str,
    subject: str,
    body_preview: str,
    replied_at: str,
    is_ooo: bool,
) -> str | None:
    """Create a row in lead_replies. Returns page ID or None."""
    try:
        page = add_row("lead_replies", {
            "Reply": body_preview[:200] or "(no preview)",
            "Resend ID": resend_id,
            "Follow-up Status": "OOO" if is_ooo else "Needs Follow-up",
            "Replied At": replied_at[:10],   # date only for Notion date property
            "Email": from_email,
            "Subject": subject[:200],
        })
        return page.get("id")
    except Exception as e:
        log.error("Failed to create lead_reply for %s: %s", resend_id, e)
        return None


def notify_outlook(from_email: str, subject: str, body_preview: str) -> bool:
    """Forward reply notification to hedgeedge@outlook.com via Resend."""
    text = "\n".join([
        "A lead replied to a Hedge Edge drip email.",
        "",
        f"From    : {from_email}",
        f"Subject : {subject}",
        "",
        "--- Reply content ---",
        body_preview[:500] or "(no preview)",
        "---",
        "",
        f"Hit Reply to respond directly to {from_email}.",
    ])

    payload = {
        "from": "Hedge Edge Alerts <alerts@hedgedge.info>",
        "to": ["hedgeedge@outlook.com"],
        "reply_to": from_email,
        "subject": f"[Lead Reply] {from_email} re: {subject[:50]}",
        "text": text,
        "tags": [
            {"name": "sequence", "value": "lead-drip-notification"},
            {"name": "type", "value": "reply-alert"},
        ],
    }

    try:
        resp = requests.post(
            f"{RESEND_BASE}/emails",
            headers={**_resend_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error("Outlook notification failed: %s", e)
        return False


# ── Core logic ────────────────────────────────────────────────────────────────

def _extract_email(from_raw: str) -> str:
    """Extract email from 'Name <email>' format."""
    m = re.search(r"<([^>]+)>", from_raw)
    return m.group(1).strip().lower() if m else from_raw.strip().lower()


def _is_automated(email: str) -> bool:
    domain = email.split("@")[-1] if "@" in email else ""
    if domain in IGNORED_SENDER_DOMAINS:
        return True
    return any(email.startswith(p) for p in IGNORED_SENDER_PREFIXES)


def _is_ooo(subject: str, body: str) -> bool:
    combined = (subject + " " + body).lower()
    return any(p in combined for p in OOO_PATTERNS)


def process_new_replies() -> dict:
    """
    Main entry point: poll Resend for inbound emails, process new ones.
    Returns summary dict with counts.
    """
    if not RESEND_API_KEY:
        log.error("RESEND_API_KEY not set")
        return {"error": "no_api_key"}

    summary = {"checked": 0, "new": 0, "processed": 0, "skipped": 0, "errors": 0}

    # Step 1: Get already-processed Resend IDs
    processed_ids = get_processed_resend_ids()
    log.info("Already processed: %d reply Resend IDs", len(processed_ids))

    # Step 2: List recent inbound emails
    inbound = list_inbound_emails(limit=50)
    summary["checked"] = len(inbound)
    log.info("Fetched %d inbound emails from Resend", len(inbound))

    for item in inbound:
        resend_id = item.get("id", "")
        from_raw = item.get("from", "")
        from_email = _extract_email(from_raw)

        # Skip already processed
        if resend_id in processed_ids:
            continue

        # Skip automated senders
        if _is_automated(from_email):
            log.debug("Skipping automated sender: %s", from_email)
            summary["skipped"] += 1
            continue

        summary["new"] += 1
        log.info("Processing new reply: %s from %s", resend_id, from_email)

        try:
            # Fetch full email details
            full = get_inbound_email(resend_id)

            subject_raw = full.get("subject", "")
            subject_clean = PREFIX_RE.sub("", subject_raw).strip()
            body_text = full.get("text", "") or full.get("html", "")
            body_preview = body_text[:500].strip()
            created_at = full.get("created_at", datetime.now(timezone.utc).isoformat())
            is_ooo = _is_ooo(subject_raw, body_preview)

            # Get in-reply-to header for matching
            headers_raw = full.get("headers", {})
            in_reply_to = headers_raw.get("in-reply-to", "")

            # Find matching email_logs row
            match = find_email_log(from_email, subject_clean, in_reply_to)

            if not match:
                log.info("  No email_logs match for %s — skipping (not a drip reply)", from_email)
                summary["skipped"] += 1
                continue

            # Update Replied checkbox
            ok = set_replied_checkboxes(match["_id"])
            log.info("  Replied checkbox: %s (match=%s)", "OK" if ok else "FAIL", match["match"])

            # Create lead_replies row
            reply_id = create_lead_reply(
                resend_id, from_email, subject_raw, body_preview, created_at, is_ooo,
            )
            log.info("  Lead reply created: %s", reply_id or "FAIL")

            # Notify Outlook (skip OOO)
            if not is_ooo:
                notified = notify_outlook(from_email, subject_raw, body_preview)
                log.info("  Outlook notification: %s", "sent" if notified else "FAIL")
            else:
                log.info("  Skipping Outlook notification (OOO)")

            summary["processed"] += 1

        except Exception as e:
            log.error("Error processing %s: %s", resend_id, e, exc_info=True)
            summary["errors"] += 1

    log.info("Reply poll complete: %s", summary)
    return summary


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    result = process_new_replies()
    print(f"Reply poll result: {result}")
    return result


if __name__ == "__main__":
    main()
