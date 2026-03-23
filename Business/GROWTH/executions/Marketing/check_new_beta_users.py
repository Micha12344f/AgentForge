#!/usr/bin/env python3
"""
check_new_beta_users.py — Marketing: Beta User Discovery, Sync & Onboarding
===========================================================================
Checks Resend for newly delivered beta license key emails and syncs
any recipients not yet in the Notion beta_waitlist database.

Actions:
    check-resend   → Pull recent beta key emails from Resend, compare with Notion
    sync-missing   → Add Resend recipients not in Notion to the waitlist (auto)
    pending        → Show all Notion entries with Beta Key Sent but not yet activated
    add            → Manually add a single user to the Notion beta waitlist
    onboard        → Full onboarding: generate key, send email, add to leads DB,
                     assign to Beta Activation campaign, update waitlist record

Usage:
    python check_new_beta_users.py --action check-resend
    python check_new_beta_users.py --action sync-missing
    python check_new_beta_users.py --action pending
    python check_new_beta_users.py --action add --email user@example.com --name "Jane Doe" --source "Twitter Bio"
    python check_new_beta_users.py --action onboard --email user@example.com --name "Jane Doe"
"""

import sys
import os
import argparse
import json
import re
import uuid
import requests
from datetime import datetime, date, timezone

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "shared")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"))

import shared.notion_client as nc

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")

# Subject substring that identifies a beta license key email
BETA_KEY_SUBJECT = "Beta License Key"

# Notion ID of the "Beta Activation" campaign in email_sends
BETA_CAMPAIGN_ID = "329652ea-6c6d-8192-8343-cc91260c359a"

# Resend pagination limit per page
RESEND_PAGE_LIMIT = 100

VALID_SOURCES = [
    "Email Drip", "Twitter Bio", "LinkedIn", "Discord",
    "Referral", "Landing Page", "Instagram", "Direct", "Other"
]


# ─────────────────────────────────────────────────────────────────────────────
# Resend helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resend_headers() -> dict:
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set in .env")
    return {"Authorization": f"Bearer {RESEND_API_KEY}"}


def fetch_beta_emails_from_resend(limit: int = 200) -> list[dict]:
    """
    Pull recent outbound emails from Resend and return only those
    that match the beta license key subject.
    """
    collected = []
    next_cursor = None
    fetched = 0

    while fetched < limit:
        batch = min(RESEND_PAGE_LIMIT, limit - fetched)
        url = f"https://api.resend.com/emails?limit={batch}"
        if next_cursor:
            url += f"&next={next_cursor}"

        resp = requests.get(url, headers=_resend_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()

        emails = data.get("data", [])
        for e in emails:
            subj = e.get("subject", "")
            if BETA_KEY_SUBJECT.lower() in subj.lower():
                for recipient in e.get("to", []):
                    collected.append({
                        "email": recipient.lower().strip(),
                        "subject": subj,
                        "created_at": e.get("created_at", ""),
                        "last_event": e.get("last_event", ""),
                        "resend_id": e.get("id", ""),
                    })

        fetched += len(emails)
        if not data.get("has_more"):
            break
        next_cursor = data.get("next")

    # Deduplicate by email (keep most recent)
    seen = {}
    for entry in collected:
        em = entry["email"]
        if em not in seen or entry["created_at"] > seen[em]["created_at"]:
            seen[em] = entry
    return list(seen.values())


# ─────────────────────────────────────────────────────────────────────────────
# Notion helpers
# ─────────────────────────────────────────────────────────────────────────────

def _notion_headers() -> dict:
    if not NOTION_TOKEN:
        raise RuntimeError("NOTION_API_KEY not set in .env")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": nc._NOTION_VERSION,
        "Content-Type": "application/json",
    }


def fetch_all_beta_emails_from_notion() -> set[str]:
    """Return a set of lowercase emails already in the beta_waitlist DB."""
    db_id = nc.DATABASES["beta_waitlist"]
    url = f"{nc._API_BASE}/databases/{db_id}/query"
    emails = set()
    cursor = None

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = nc.notion_request("post", url, headers=_notion_headers(), json=body, timeout=30)
        data = resp.json()

        for page in data.get("results", []):
            raw = page["properties"].get("Email", {}).get("email")
            if raw:
                emails.add(raw.lower().strip())

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return emails


def _parse_name_from_email(email: str) -> tuple[str, str]:
    """Best-effort first/last name from the email local part."""
    local = email.split("@")[0]
    parts = re.split(r"[._\-]", local)
    parts = [p.capitalize() for p in parts if p.isalpha()]
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if parts:
        return parts[0], ""
    return local.capitalize(), ""


def add_beta_user_to_notion(
    email: str,
    name: str = "",
    first_name: str = "",
    last_name: str = "",
    source: str = "Email Drip",
    priority: str = "P2",
    key_sent_date: str = "",
    notes: str = "",
) -> dict:
    """
    Create a new entry in the Notion beta_waitlist database.
    Returns the created page dict.
    """
    if not name and not first_name:
        first_name, last_name = _parse_name_from_email(email)

    display_name = name or f"{first_name} {last_name}".strip()
    if not first_name and name:
        parts = name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    note_text = notes or f"Added automatically — beta key email detected in Resend on {today}."

    payload = {
        "parent": {"database_id": nc.DATABASES["beta_waitlist"]},
        "properties": {
            "Name":          {"title": [{"text": {"content": display_name}}]},
            "First Name":    {"rich_text": [{"text": {"content": first_name}}]},
            "Last Name":     {"rich_text": [{"text": {"content": last_name}}]},
            "Email":         {"email": email.lower().strip()},
            "Source":        {"select": {"name": source}},
            "Priority":      {"select": {"name": priority}},
            "Tags":          {"multi_select": [{"name": "Beta"}, {"name": "Beta Key Sent"}]},
            "Beta Key Sent": {"checkbox": True},
            "Beta Activated":{"checkbox": False},
            "Notes":         {"rich_text": [{"text": {"content": note_text}}]},
        },
    }

    if key_sent_date:
        payload["properties"]["Key Sent Date"] = {"date": {"start": key_sent_date}}

    url = f"{nc._API_BASE}/pages"
    resp = nc.notion_request("post", url, headers=_notion_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_pending_activation() -> list[dict]:
    """Return all Notion entries where Beta Key Sent=True and Beta Activated=False."""
    db_id = nc.DATABASES["beta_waitlist"]
    url = f"{nc._API_BASE}/databases/{db_id}/query"
    body = {
        "page_size": 100,
        "filter": {
            "and": [
                {"property": "Beta Key Sent", "checkbox": {"equals": True}},
                {"property": "Beta Activated", "checkbox": {"equals": False}},
            ]
        },
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
    }
    resp = nc.notion_request("post", url, headers=_notion_headers(), json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for page in data.get("results", []):
        props = page["properties"]
        name = "".join(x.get("plain_text", "") for x in props.get("Name", {}).get("title", []))
        email = props.get("Email", {}).get("email", "")
        source = (props.get("Source", {}).get("select") or {}).get("name", "")
        priority = (props.get("Priority", {}).get("select") or {}).get("name", "")
        tags = [x.get("name") for x in props.get("Tags", {}).get("multi_select", [])]
        created = page.get("created_time", "")[:10]
        results.append({
            "name": name, "email": email, "source": source,
            "priority": priority, "tags": tags, "created": created,
        })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Action handlers
# ─────────────────────────────────────────────────────────────────────────────

def action_check_resend(args):
    """
    Pull beta emails from Resend and show which are missing from Notion.
    """
    print("Fetching beta key emails from Resend...")
    resend_users = fetch_beta_emails_from_resend(limit=200)
    print(f"  Found {len(resend_users)} unique recipient(s) who received a beta key email.\n")

    print("Fetching existing emails from Notion beta_waitlist...")
    notion_emails = fetch_all_beta_emails_from_notion()
    print(f"  Found {len(notion_emails)} existing entries in Notion.\n")

    missing = [u for u in resend_users if u["email"] not in notion_emails]
    already_in = [u for u in resend_users if u["email"] in notion_emails]

    print("=" * 65)
    print(f"  ALREADY IN NOTION: {len(already_in)}")
    for u in already_in:
        print(f"    ✓  {u['email']}  ({u['last_event']})")

    print()
    print(f"  MISSING FROM NOTION: {len(missing)}")
    if missing:
        for u in missing:
            sent_date = u["created_at"][:10] if u["created_at"] else "unknown"
            print(f"    ✗  {u['email']}  sent={sent_date}  event={u['last_event']}")
        print()
        print("  ➜  Run with --action sync-missing to add them automatically.")
    else:
        print("    All Resend recipients are already in Notion.")
    print("=" * 65)


def action_sync_missing(args):
    """
    Add any Resend beta email recipients not yet in Notion.
    """
    print("Fetching beta key emails from Resend...")
    resend_users = fetch_beta_emails_from_resend(limit=200)

    print("Fetching existing emails from Notion...")
    notion_emails = fetch_all_beta_emails_from_notion()

    missing = [u for u in resend_users if u["email"] not in notion_emails]

    if not missing:
        print("✓  All Resend recipients are already in Notion. Nothing to sync.")
        return

    print(f"\nAdding {len(missing)} missing user(s) to Notion beta_waitlist...\n")
    added = []
    failed = []
    for u in missing:
        email = u["email"]
        sent_date = u["created_at"][:10] if u["created_at"] else ""
        try:
            page = add_beta_user_to_notion(
                email=email,
                source="Email Drip",
                priority="P2",
                key_sent_date=sent_date,
                notes=f"Auto-synced from Resend. Email sent {sent_date}, last event: {u['last_event']}.",
            )
            added.append({"email": email, "notion_id": page.get("id")})
            print(f"  ✓  Added: {email}")
        except Exception as e:
            failed.append({"email": email, "error": str(e)})
            print(f"  ✗  Failed: {email}  —  {e}")

    print()
    print("=" * 65)
    print(f"  SYNC COMPLETE: {len(added)} added, {len(failed)} failed")
    print("=" * 65)


def action_pending(args):
    """
    Show all beta users who received a key but haven't activated yet.
    """
    print("Fetching pending activation users from Notion...\n")
    users = fetch_pending_activation()

    if not users:
        print("✓  No pending activations — everyone has activated!")
        return

    print("=" * 65)
    print(f"  PENDING ACTIVATION ({len(users)} users)")
    print("=" * 65)
    for u in users:
        tags_str = ", ".join(u["tags"])
        print(f"  {u['name'] or '(no name)':25s}  {u['email']:35s}")
        print(f"    Source: {u['source']:20s}  Priority: {u['priority']:5s}  Added: {u['created']}")
        print(f"    Tags: {tags_str}")
        print()


def action_add(args):
    """
    Manually add a single user to the Notion beta waitlist.
    """
    if not args.email:
        print("ERROR: --email is required for --action add")
        sys.exit(1)

    source = args.source or "Direct"
    if source not in VALID_SOURCES:
        print(f"WARNING: '{source}' is not a standard source. Valid options: {VALID_SOURCES}")

    print(f"Adding {args.email} to Notion beta_waitlist...")
    page = add_beta_user_to_notion(
        email=args.email,
        name=args.name or "",
        source=source,
        priority=args.priority or "P2",
        notes=args.notes or "",
    )
    print(f"  ✓  Added! Notion page ID: {page.get('id')}")
    print(f"  ✓  URL: {page.get('url')}")


# ─────────────────────────────────────────────────────────────────────────────
# Onboard helpers
# ─────────────────────────────────────────────────────────────────────────────

def _generate_beta_key() -> str:
    """Generate a unique beta license key in HE-XXXX-XXXX-XXXX format."""
    raw = uuid.uuid4().hex.upper()
    return f"HE-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"


def _add_to_leads_db(email: str, first: str, last: str, source: str = "Email Drip") -> dict:
    """
    Create a new lead row in the email_sends (leads) DB and assign to
    the Beta Activation campaign.
    """
    payload = {
        "parent": {"database_id": nc.DATABASES["email_sends"]},
        "properties": {
            "Subject":      {"title":     [{"text": {"content": f"{first} {last}".strip()}}]},
            "First Name":   {"rich_text": [{"text": {"content": first}}]},
            "Last Name":    {"rich_text": [{"text": {"content": last}}]},
            "Email":        {"email": email.lower().strip()},
            "Source":       {"select": {"name": source}},
            "Campaign":     {"relation": [{"id": BETA_CAMPAIGN_ID}]},
            "Unsubscribed": {"checkbox": False},
        },
    }
    resp = nc.notion_request("post", f"{nc._API_BASE}/pages",
                             headers=_notion_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _is_in_leads_db(email: str) -> bool:
    """Return True if this email is already in the email_sends leads DB."""
    url = f"{nc._API_BASE}/databases/{nc.DATABASES['email_sends']}/query"
    body = {"filter": {"property": "Email", "email": {"equals": email.lower().strip()}}}
    resp = nc.notion_request("post", url, headers=_notion_headers(), json=body, timeout=30)
    resp.raise_for_status()
    return bool(resp.json().get("results"))


def _update_waitlist_with_key(email: str, beta_key: str) -> None:
    """Store the generated beta key and key-sent date on the waitlist record.
    If beta_key is empty, only stamps the Key Sent Date (preserves existing key)."""
    url = f"{nc._API_BASE}/databases/{nc.DATABASES['beta_waitlist']}/query"
    body = {"filter": {"property": "Email", "email": {"equals": email.lower().strip()}}}
    data = nc.notion_request("post", url, headers=_notion_headers(), json=body, timeout=30).json()
    results = data.get("results", [])
    if not results:
        return  # can't update — not in waitlist yet
    page_id = results[0]["id"]
    patch: dict = {
        "properties": {
            "Key Sent Date": {"date": {"start": date.today().isoformat()}},
            "Beta Key Sent": {"checkbox": True},
        }
    }
    if beta_key:
        patch["properties"]["Beta Key"] = {"rich_text": [{"text": {"content": beta_key}}]}
    nc.notion_request("patch", f"{nc._API_BASE}/pages/{page_id}",
                      headers=_notion_headers(), json=patch, timeout=30)


def action_onboard(args):
    """
    Full beta user onboarding pipeline (does NOT re-send the license key):
      1. Ensure user is in the Notion beta_waitlist
      2. Add the user to email_sends leads DB → Beta Activation campaign
      3. Send Beta Activation Email 1 ("Your beta is live") from the Notion sequence
      4. Stamp Key Sent Date on the waitlist record
    """
    if not args.email:
        print("ERROR: --email is required for --action onboard")
        sys.exit(1)

    email = args.email.lower().strip()
    source = args.source or "Email Drip"
    priority = args.priority or "P2"

    # Parse name
    name = args.name or ""
    if name:
        parts = name.split(" ", 1)
        first = parts[0]
        last  = parts[1] if len(parts) > 1 else ""
    else:
        first, last = _parse_name_from_email(email)
        name = f"{first} {last}".strip()

    print(f"\nOnboarding: {name} <{email}>")
    print("-" * 55)

    # Step 1 — ensure in waitlist
    existing_wl = fetch_all_beta_emails_from_notion()
    if email not in existing_wl:
        print("[1] Not in beta_waitlist — adding now...")
        add_beta_user_to_notion(
            email=email, name=name, source=source, priority=priority,
        )
        print("    ✓ Added to beta_waitlist.")
    else:
        print("[1] Already in beta_waitlist. ✓")

    # Step 2 — add to leads DB if not already there
    if _is_in_leads_db(email):
        print("[2] Already in leads DB (email_sends). ✓")
    else:
        lead_page = _add_to_leads_db(email, first, last, source)
        print(f"[2] Added to email_sends → Beta Activation campaign.  ID: {lead_page.get('id')}")

    # Step 3 — send Beta Activation Email 1 from Notion sequence
    try:
        import html as _html
        import requests as _req
        # Fetch Email 1 body from Notion sequence
        _EMAIL1_SEQ_ID = "329652ea-6c6d-8195-b4a2-c5aa4441e180"
        _blocks_resp = nc.notion_request(
            "get", f"{nc._API_BASE}/blocks/{_EMAIL1_SEQ_ID}/children",
            headers=_notion_headers(), timeout=20
        )
        _blocks = _blocks_resp.json().get("results", [])
        _body_text = ""
        for _b in _blocks:
            _btype = _b.get("type", "")
            if _btype in _b:
                _rich = _b[_btype].get("rich_text", [])
                _body_text = "".join(x.get("plain_text", "") for x in _rich)
            if _body_text:
                break

        _personalised = _body_text.replace("{{Name}}", first).replace("{{name}}", first)

        def _add_utm_to_hedgedge_links(text: str, campaign: str, medium: str = "drip") -> str:
            """Append UTM params to any bare or linked hedgedge.info URLs."""
            import re as _re
            def _replacer(m):
                url = m.group(0)
                sep = "&" if "?" in url else "?"
                return f"{url}{sep}utm_source=email&utm_medium={medium}&utm_campaign={campaign}"
            return _re.sub(r'https?://(?:www\.)?hedgedge\.info[^\s"<>]*', _replacer, text)

        _personalised = _add_utm_to_hedgedge_links(
            _personalised, campaign="beta-activation", medium="drip"
        )

        def _plain_to_html(txt, fname):
            esc = _html.escape(txt)
            paras = [
                f'<p style="margin:0 0 14px;font-size:15px;color:#333;line-height:1.7;">{p.replace(chr(10),"<br>")}</p>'
                for p in esc.split("\n\n") if p.strip()
            ]
            return (
                '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"></head>'
                '<body style="margin:0;padding:0;background:#f7f7f7;font-family:\'Segoe UI\',Arial,sans-serif;">'
                '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f7f7f7;">'
                '<tr><td align="center" style="padding:32px 16px;">'
                '<table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background:#fff;border-radius:8px;border:1px solid #e5e5e5;">'
                '<tr><td style="padding:24px 36px 8px;border-bottom:1px solid #eee;">'
                '<span style="font-size:22px;font-weight:700;color:#111;">Hedge</span>'
                '<span style="font-size:22px;font-weight:700;color:#16a34a;">Edge</span>'
                '</td></tr>'
                f'<tr><td style="padding:28px 36px 32px;">{"".join(paras)}</td></tr>'
                '</table></td></tr></table></body></html>'
            )

        _html_body = _plain_to_html(_personalised, first)
        _resend_payload = {
            "from":     "Ryan <hello@hedgedge.info>",
            "to":       [email],
            "reply_to": "reply@hedgedge.info",
            "subject":  "Your Hedge Edge beta is live — here's what to do first",
            "html":     _html_body,
            "text":     _personalised,
            "tags": [
                {"name": "campaign",  "value": "Beta_Activation"},
                {"name": "sequence",  "value": "Email_1"},
            ],
        }
        _r = _req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json=_resend_payload, timeout=15
        )
        _r.raise_for_status()
        print(f"[3] Beta Activation Email 1 sent!  Resend ID: {_r.json().get('id')}")
    except Exception as e:
        print(f"[3] WARNING: Email 1 send failed — {e}")

    # Step 4 — mark key sent date on waitlist entry
    _update_waitlist_with_key(email, "")  # clears nothing, just stamps today's date
    print("[4] Key sent date stamped on Notion waitlist record. ✓")

    print()
    print("=" * 55)
    print("  ONBOARDING COMPLETE")
    print(f"  Name:     {name}")
    print(f"  Email:    {email}")
    print(f"  Campaign: Beta Activation (Email 1 sent)")
    print("=" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

ACTIONS = {
    "check-resend": action_check_resend,
    "sync-missing": action_sync_missing,
    "pending":      action_pending,
    "add":          action_add,
    "onboard":      action_onboard,
}


def main():
    parser = argparse.ArgumentParser(
        description="Beta user discovery and Notion sync tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_new_beta_users.py --action check-resend
  python check_new_beta_users.py --action sync-missing
  python check_new_beta_users.py --action pending
  python check_new_beta_users.py --action add --email user@example.com --name "Jane Doe"
  python check_new_beta_users.py --action onboard --email user@example.com --name "Jane Doe" --source "Twitter Bio"
"""
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=list(ACTIONS.keys()),
        help="Which action to run"
    )
    parser.add_argument("--email",    help="Email address (used with --action add)")
    parser.add_argument("--name",     help="Full name (used with --action add)")
    parser.add_argument("--source",   help=f"Lead source. Options: {VALID_SOURCES}")
    parser.add_argument("--priority", help="Priority level: P1, P2, P3", default="P2")
    parser.add_argument("--notes",    help="Optional notes to attach to the Notion entry")

    args = parser.parse_args()
    ACTIONS[args.action](args)


if __name__ == "__main__":
    main()
