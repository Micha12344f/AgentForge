#!/usr/bin/env python3
"""
beta_email_parser.py — Resend Beta Key Email Parser & Sanity Checker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Parses Resend emails with subject "🔑 Your Free Beta License Key — Hedge Edge",
extracts first name + email for every recipient, and provides:

  • scan         — List all beta key email recipients with first name + email
  • cross-check  — Compare Resend recipients vs Supabase user_attribution (sanity)
  • hot-leads    — Show recipients who clicked/opened = high-interest leads

Usage (Analytics — sanity check):
    python beta_email_parser.py --action scan
    python beta_email_parser.py --action cross-check

Usage (Marketing — hot lead discovery):
    python beta_email_parser.py --action hot-leads
"""

import sys
import os
import re

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse
import requests
from datetime import datetime, timezone, timedelta

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import log_task
from shared.supabase_client import get_supabase

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
BETA_SUBJECT_MATCH = "Beta License Key"
RESEND_PAGE_LIMIT = 100


# ──────────────────────────────────────────────
# Resend helpers
# ──────────────────────────────────────────────

def _resend_headers() -> dict:
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set in .env")
    return {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }


def _fetch_beta_emails(limit: int = 300) -> list[dict]:
    """
    Paginate Resend /emails, keep only those whose subject contains
    the beta license key identifier. Returns list of raw Resend dicts.
    """
    collected: list[dict] = []
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

        for e in data.get("data", []):
            subj = e.get("subject", "")
            if BETA_SUBJECT_MATCH.lower() in subj.lower():
                collected.append(e)

        fetched += len(data.get("data", []))
        if not data.get("has_more"):
            break
        next_cursor = data.get("next")

    return collected


def _extract_first_name_from_html(html: str) -> str:
    """Extract first name from the greeting in the beta key email HTML.
    The email body includes a pattern like 'Hi <name>,' or 'Hi <name>!'."""
    # Match "Hi <Name>," or "Hi <Name>!"
    m = re.search(r'(?:Hi|Hey|Hello)\s+([A-Z][a-z]+)', html)
    if m:
        return m.group(1)
    return ""


def _parse_name_from_email(email: str) -> str:
    """Best-effort first name from the email local part."""
    local = email.split("@")[0]
    parts = re.split(r"[._\-+]", local)
    parts = [p.capitalize() for p in parts if p.isalpha() and len(p) > 1]
    return parts[0] if parts else local.capitalize()


def _get_email_detail(email_id: str) -> dict:
    """GET /emails/{id} to retrieve full email including HTML body."""
    url = f"https://api.resend.com/emails/{email_id}"
    resp = requests.get(url, headers=_resend_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_beta_recipients(limit: int = 300) -> list[dict]:
    """
    Core parser: pull beta key emails from Resend, extract first name
    + email for each recipient.  Returns deduplicated list sorted by date.
    """
    raw_emails = _fetch_beta_emails(limit=limit)
    recipients: dict[str, dict] = {}  # keyed by email for dedup

    for e in raw_emails:
        email_id = e.get("id", "")
        created = e.get("created_at", "")
        last_event = e.get("last_event", "")
        to_list = e.get("to", [])

        # Try to get first name from email HTML body
        first_name = ""
        try:
            detail = _get_email_detail(email_id)
            html_body = detail.get("html", "")
            first_name = _extract_first_name_from_html(html_body)
        except Exception:
            pass

        for addr in to_list:
            addr_lower = addr.lower().strip()
            if not first_name:
                first_name = _parse_name_from_email(addr_lower)

            # Keep most recent entry per email
            if addr_lower not in recipients or created > recipients[addr_lower]["sent_at"]:
                recipients[addr_lower] = {
                    "email": addr_lower,
                    "first_name": first_name,
                    "sent_at": created,
                    "last_event": last_event,
                    "resend_id": email_id,
                }

    return sorted(recipients.values(), key=lambda r: r["sent_at"], reverse=True)


# ──────────────────────────────────────────────
# Supabase helpers
# ──────────────────────────────────────────────

def _get_attribution_emails() -> dict[str, dict]:
    """Pull all user_attribution rows, keyed by ref (email)."""
    sb = get_supabase(use_service_role=True)
    rows = sb.table("user_attribution").select("*").execute().data or []
    result: dict[str, dict] = {}
    for r in rows:
        email = (r.get("ref") or "").lower().strip()
        if email:
            result[email] = r
    return result


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_scan(limit: int = 300) -> dict:
    """List all beta key email recipients with first name + email."""
    recipients = parse_beta_recipients(limit=limit)

    print("=" * 65)
    print("  Beta Key Emails — Resend Scan")
    print("=" * 65)
    print(f"\n  Total recipients: {len(recipients)}\n")

    if not recipients:
        print("  (none found)")
        return {"count": 0, "recipients": []}

    print(f"  {'First Name':<16s}  {'Email':<36s}  {'Event':<12s}  {'Sent'}")
    print(f"  {'─' * 16}  {'─' * 36}  {'─' * 12}  {'─' * 19}")
    for r in recipients:
        ts = r["sent_at"][:19].replace("T", " ") if r["sent_at"] else ""
        print(f"  {r['first_name']:<16s}  {r['email']:<36s}  {r['last_event']:<12s}  {ts}")

    return {"count": len(recipients), "recipients": recipients}


def action_cross_check(limit: int = 300) -> dict:
    """
    Sanity check: compare Resend beta key recipients against Supabase
    user_attribution.  Flag any mismatches.
    """
    print("  Fetching beta key emails from Resend...")
    recipients = parse_beta_recipients(limit=limit)

    print("  Fetching user_attribution from Supabase...")
    attribution = _get_attribution_emails()

    resend_emails = {r["email"] for r in recipients}
    supa_emails = set(attribution.keys())

    in_both = resend_emails & supa_emails
    resend_only = resend_emails - supa_emails
    supa_only = supa_emails - resend_emails

    print()
    print("=" * 65)
    print("  Cross-Check: Resend Beta Emails vs Supabase Attribution")
    print("=" * 65)
    print(f"\n  Resend recipients:       {len(resend_emails)}")
    print(f"  Supabase attributions:   {len(supa_emails)}")
    print(f"  Matched (in both):       {len(in_both)}")
    print(f"  Resend only (no attrib): {len(resend_only)}")
    print(f"  Supabase only (no email):{len(supa_only)}")

    if in_both:
        print(f"\n  {'─' * 61}")
        print(f"  ✓ MATCHED ({len(in_both)}):")
        for email in sorted(in_both):
            r = next(x for x in recipients if x["email"] == email)
            a = attribution[email]
            source = a.get("utm_source") or "direct"
            print(f"    {r['first_name']:<16s}  {email:<36s}  source={source}")

    if resend_only:
        print(f"\n  {'─' * 61}")
        print(f"  ⚠ RESEND ONLY — received beta key but NO Supabase attribution ({len(resend_only)}):")
        for email in sorted(resend_only):
            r = next(x for x in recipients if x["email"] == email)
            print(f"    {r['first_name']:<16s}  {email:<36s}  event={r['last_event']}")

    if supa_only:
        print(f"\n  {'─' * 61}")
        print(f"  ⚠ SUPABASE ONLY — attribution exists but no beta key email ({len(supa_only)}):")
        for email in sorted(supa_only):
            a = attribution[email]
            method = a.get("signup_method") or "unknown"
            print(f"    {email:<36s}  method={method}")

    print()
    ok = len(resend_only) == 0 and len(supa_only) == 0
    print(f"  SANITY: {'✓ PASS — all records match' if ok else '⚠ MISMATCH — see above'}")
    print("=" * 65)

    return {
        "matched": len(in_both),
        "resend_only": len(resend_only),
        "supabase_only": len(supa_only),
        "pass": ok,
    }


def action_hot_leads(limit: int = 300) -> dict:
    """
    Marketing hot-lead finder: show recipients who clicked or opened
    the beta key email = high-interest signals.
    """
    recipients = parse_beta_recipients(limit=limit)

    # Engagement tiers (Resend last_event values)
    hot = [r for r in recipients if r["last_event"] == "clicked"]
    warm = [r for r in recipients if r["last_event"] == "opened"]
    delivered = [r for r in recipients if r["last_event"] == "delivered"]
    other = [r for r in recipients if r["last_event"] not in ("clicked", "opened", "delivered")]

    print("=" * 65)
    print("  Beta Key Leads — Engagement Tiers")
    print("=" * 65)
    print(f"\n  Total: {len(recipients)}")
    print(f"  🔥 Clicked (HOT):    {len(hot)}")
    print(f"  🟡 Opened (WARM):    {len(warm)}")
    print(f"  📬 Delivered only:   {len(delivered)}")
    if other:
        print(f"  ❓ Other:            {len(other)}")

    if hot:
        print(f"\n  {'─' * 61}")
        print("  🔥 HOT LEADS (clicked — very interested):")
        for r in hot:
            ts = r["sent_at"][:10] if r["sent_at"] else ""
            print(f"    {r['first_name']:<16s}  {r['email']:<36s}  sent={ts}")

    if warm:
        print(f"\n  {'─' * 61}")
        print("  🟡 WARM LEADS (opened — interested):")
        for r in warm:
            ts = r["sent_at"][:10] if r["sent_at"] else ""
            print(f"    {r['first_name']:<16s}  {r['email']:<36s}  sent={ts}")

    if delivered:
        print(f"\n  {'─' * 61}")
        print("  📬 DELIVERED (not opened yet):")
        for r in delivered:
            ts = r["sent_at"][:10] if r["sent_at"] else ""
            print(f"    {r['first_name']:<16s}  {r['email']:<36s}  sent={ts}")

    print()
    return {
        "total": len(recipients),
        "hot": [{"first_name": r["first_name"], "email": r["email"]} for r in hot],
        "warm": [{"first_name": r["first_name"], "email": r["email"]} for r in warm],
        "delivered": len(delivered),
    }


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Beta Key Email Parser & Sanity Checker")
    parser.add_argument("--action", required=True,
                        choices=["scan", "cross-check", "hot-leads"])
    parser.add_argument("--limit", type=int, default=300,
                        help="Max Resend emails to scan (default: 300)")
    args = parser.parse_args()

    if args.action == "scan":
        action_scan(args.limit)
    elif args.action == "cross-check":
        action_cross_check(args.limit)
    elif args.action == "hot-leads":
        action_hot_leads(args.limit)

    log_task("Analytics", "beta-email-parse", args.action, "success")


if __name__ == "__main__":
    main()
