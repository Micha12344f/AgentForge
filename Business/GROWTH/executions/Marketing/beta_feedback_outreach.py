#!/usr/bin/env python3
"""Send a personalized beta feedback check-in to current external beta users."""

import argparse
import os
import re
import sys
from datetime import datetime, timezone


def _find_workspace_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(here, "shared")) and os.path.isdir(os.path.join(here, "Business")):
            return here
        here = os.path.dirname(here)
    raise RuntimeError("Cannot locate workspace root")


WORKSPACE_ROOT = _find_workspace_root()
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"), override=True)

from shared.notion_client import log_task
from shared.resend_client import RecipientUnsubscribedError, send_email
from shared.supabase_client import get_supabase

try:
    from Business.ANALYTICS.executions.beta_email_parser import parse_beta_recipients
except Exception:
    parse_beta_recipients = None


CAL_LINK = "https://cal.eu/hedgedge/30min"
FROM_ADDR = "Hedge Edge <hello@hedgedge.info>"
REPLY_TO = "reply@hedgedge.info"
POOL_PLACEHOLDER = "pool-unassigned@beta.hedgedge-internal"
INTERNAL_DOMAINS = {"hedgeedge.com", "hedge-edge.com", "hedgedge.info"}
INTERNAL_EMAILS = {
    "sossionryan@gmail.com",
    "rmcap1ta7@gmail.com",
    "test@hedgeedge.com",
    "friend@hedgeedge.com",
    "developer@hedge-edge.com",
}


def _is_internal_email(email: str) -> bool:
    clean = email.strip().lower()
    if clean in INTERNAL_EMAILS:
        return True
    domain = clean.split("@")[-1]
    return domain in INTERNAL_DOMAINS


def _fallback_first_name(email: str) -> str:
    local = email.split("@", 1)[0]
    parts = [part for part in re.split(r"[._\-+]", local) if part]
    for part in parts:
        if part.isalpha() and len(part) > 1:
            return part.capitalize()
    return "there"


def _recipient_name_map(limit: int = 300) -> dict[str, dict]:
    if parse_beta_recipients is None:
        return {}
    try:
        recipients = parse_beta_recipients(limit=limit)
    except Exception:
        return {}
    return {row["email"].strip().lower(): row for row in recipients}


def fetch_current_beta_users(include_internal: bool = False) -> list[dict]:
    db = get_supabase(use_service_role=True)
    licenses = (
        db.table("licenses")
        .select("id,email,license_key,updated_at,plan,is_active")
        .neq("email", POOL_PLACEHOLDER)
        .eq("plan", "professional")
        .eq("is_active", True)
        .execute()
        .data
        or []
    )
    devices = (
        db.table("license_devices")
        .select("license_id,platform,broker,account_id,last_seen_at")
        .eq("is_active", True)
        .execute()
        .data
        or []
    )
    recipient_map = _recipient_name_map()
    current_users: list[dict] = []

    for license_row in licenses:
        email = (license_row.get("email") or "").strip().lower()
        if not email:
            continue
        if not include_internal and _is_internal_email(email):
            continue
        beta_meta = recipient_map.get(email, {})
        first_name = beta_meta.get("first_name") or _fallback_first_name(email)
        user_devices = [d for d in devices if d.get("license_id") == license_row.get("id")]
        current_users.append(
            {
                "email": email,
                "first_name": first_name,
                "license_key": license_row.get("license_key", ""),
                "updated_at": license_row.get("updated_at", ""),
                "last_event": beta_meta.get("last_event", ""),
                "device_count": len(user_devices),
                "last_seen_at": max((d.get("last_seen_at") or "" for d in user_devices), default=""),
                "devices": user_devices,
            }
        )

    current_users.sort(key=lambda row: row.get("updated_at", ""), reverse=True)
    return current_users


def _build_explicit_user(email: str) -> dict:
    clean = email.strip().lower()
    beta_meta = _recipient_name_map().get(clean, {})
    first_name = beta_meta.get("first_name") or _fallback_first_name(clean)
    return {
        "email": clean,
        "first_name": first_name,
        "license_key": "",
        "updated_at": "",
        "last_event": beta_meta.get("last_event", ""),
        "device_count": 0,
        "last_seen_at": "",
        "devices": [],
    }


def build_subject(first_name: str) -> str:
    safe_name = first_name if first_name and first_name.lower() != "there" else ""
    if safe_name:
        return f"{safe_name}, how's Hedge Edge going so far?"
    return "Quick beta check-in from Hedge Edge"


def build_text(user: dict) -> str:
    first_name = user.get("first_name") or "there"
    greeting = f"Hi {first_name}," if first_name.lower() != "there" else "Hi there,"
    if user.get("device_count", 0) > 0:
        intro = "Wanted to check in and see how your experience with Hedge Edge has been going so far."
    else:
        intro = "Wanted to check in now that you have beta access and see how your experience with Hedge Edge is going so far."

    return (
        f"{greeting}\n\n"
        f"{intro}\n\n"
        "How is the experience going for you so far?\n\n"
        "If you're experiencing any issues, or you're curious about anything in the product or setup, just reply to this email and I'll help directly.\n\n"
        "If you'd prefer, you can also book a 30 minute demo here and we can walk through everything together:\n\n"
        f"{CAL_LINK}\n\n"
        "Best,\n"
        "Ryan\n\n"
        "Reply directly to this email if you'd rather send feedback asynchronously."
    )


def send_text_email(user: dict) -> dict:
    return send_email(
        to=user["email"],
        subject=build_subject(user.get("first_name", "")),
        text=build_text(user),
        from_addr=FROM_ADDR,
        reply_to=REPLY_TO,
        tags=[
            {"name": "campaign", "value": "beta-feedback-checkin"},
            {"name": "cohort", "value": "current-beta"},
        ],
        include_unsubscribe=True,
        respect_notion_unsubscribe=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or send a beta feedback outreach email.")
    parser.add_argument("--send", action="store_true", help="Actually send the emails. Default is dry-run.")
    parser.add_argument("--include-internal", action="store_true", help="Include internal/test addresses.")
    parser.add_argument("--recipient", action="append", default=[], help="Optional email filter. Can be passed multiple times.")
    args = parser.parse_args()

    recipients = fetch_current_beta_users(include_internal=args.include_internal)
    if args.recipient:
        wanted = {email.strip().lower() for email in args.recipient if email.strip()}
        existing = {row["email"]: row for row in recipients}
        recipients = [existing[email] if email in existing else _build_explicit_user(email) for email in sorted(wanted)]

    print("=" * 72)
    print("  BETA FEEDBACK OUTREACH")
    print("=" * 72)
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Mode:      {'SEND' if args.send else 'DRY RUN'}")
    print(f"  Recipients: {len(recipients)}")
    print()

    if not recipients:
        print("No recipients matched the current filter.")
        log_task(
            "Marketing",
            "beta-feedback-outreach",
            status="Complete",
            priority="P2",
            output_summary="No external current beta recipients matched the outreach filter.",
        )
        return 0

    for user in recipients:
        device_hint = f" devices={user['device_count']}" if user.get("device_count") is not None else ""
        print(
            f"  - {user['first_name']:<12s} {user['email']:<36s}"
            f" event={user.get('last_event') or '-':<10s}{device_hint}"
        )

    if not args.send:
        print()
        print("Dry run only. Re-run with --send to deliver the outreach email.")
        return 0

    print()
    sent = []
    skipped = []
    failed = []
    for user in recipients:
        try:
            result = send_text_email(user)
            resend_id = result.get("id", "")
            sent.append({"email": user["email"], "resend_id": resend_id})
            print(f"  Sent to {user['email']}  resend_id={resend_id}")
        except RecipientUnsubscribedError as exc:
            skipped.append({"email": user["email"], "reason": str(exc)})
            print(f"  SKIPPED {user['email']}  reason={exc}")
        except Exception as exc:
            failed.append({"email": user["email"], "error": str(exc)})
            print(f"  FAILED {user['email']}  error={exc}")

    summary = f"Sent {len(sent)} beta feedback email(s); skipped={len(skipped)}; failed={len(failed)}"
    log_task(
        "Marketing",
        "beta-feedback-outreach",
        status="Complete" if not failed else "In Progress",
        priority="P2",
        output_summary=summary,
        error="; ".join(
            [f"{row['email']}: {row['error']}" for row in failed]
            + [f"{row['email']}: {row['reason']}" for row in skipped]
        ),
    )

    print()
    print(summary)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())