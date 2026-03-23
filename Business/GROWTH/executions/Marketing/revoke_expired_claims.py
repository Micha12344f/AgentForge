"""
revoke_expired_claims.py — 48-Hour Beta Key Revocation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Finds beta keys that were claimed but NOT activated within 48 hours,
then returns them to the available pool so the next waitlisted user
can claim one.

"Activated" = at least one device registered in license_devices,
  OR at least one successful validation in license_validation_logs.

Usage:
    python revoke_expired_claims.py              # dry-run (default)
    python revoke_expired_claims.py --revoke     # actually revoke + notify
    python revoke_expired_claims.py --status     # pool status overview
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.supabase_client import get_supabase
from shared.resend_client import send_email

POOL_PLACEHOLDER = "pool-unassigned@beta.hedgedge-internal"
EXPIRY_HOURS = 48


def get_db():
    return get_supabase(use_service_role=True)


def pool_status():
    """Print current pool statistics."""
    db = get_db()

    total = db.table("licenses").select("id", count="exact").execute()
    available = (
        db.table("licenses")
        .select("id", count="exact")
        .eq("email", POOL_PLACEHOLDER)
        .eq("is_active", True)
        .execute()
    )
    claimed = (
        db.table("licenses")
        .select("id", count="exact")
        .neq("email", POOL_PLACEHOLDER)
        .eq("is_active", True)
        .eq("plan", "professional")
        .execute()
    )

    print("Beta License Pool — Status")
    print("=" * 40)
    print(f"  Total licenses:    {total.count}")
    print(f"  Available (pool):  {available.count}")
    print(f"  Claimed (active):  {claimed.count}")
    print()


def find_expired_claims(db):
    """Find claimed keys past the 48h activation window."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=EXPIRY_HOURS)).isoformat()

    # Get all claimed beta keys (email != placeholder)
    claimed = (
        db.table("licenses")
        .select("id, license_key, email, notes, updated_at")
        .neq("email", POOL_PLACEHOLDER)
        .eq("is_active", True)
        .eq("plan", "professional")
        .execute()
    )

    expired = []
    for row in claimed.data or []:
        notes = {}
        if row.get("notes"):
            try:
                notes = json.loads(row["notes"])
            except (json.JSONDecodeError, TypeError):
                pass

        claimed_at = notes.get("claimed_at") or row.get("updated_at")
        if not claimed_at:
            continue

        # Check if past expiry window
        if claimed_at > cutoff:
            continue  # still within 48h

        # Check if this key has been activated (device registered or successful validation)
        license_id = row["id"]
        license_key = row["license_key"]

        # Check license_devices for this license
        devices = (
            db.table("license_devices")
            .select("id", count="exact")
            .eq("license_id", license_id)
            .eq("is_active", True)
            .execute()
        )
        if devices.count and devices.count > 0:
            continue  # key is activated — skip

        # Check license_validation_logs for successful validations
        validations = (
            db.table("license_validation_logs")
            .select("id", count="exact")
            .eq("license_key", license_key)
            .eq("success", True)
            .execute()
        )
        if validations.count and validations.count > 0:
            continue  # key was successfully validated — skip

        expired.append({
            "id": license_id,
            "license_key": license_key,
            "email": row["email"],
            "claimed_at": claimed_at,
            "first_name": notes.get("first_name", ""),
        })

    return expired


def build_revocation_email(first_name: str, license_key: str) -> str:
    name = first_name or "there"
    masked_key = license_key[:5] + "..." + license_key[-5:]
    return f"""
<div style="font-family:'Segoe UI',Inter,Helvetica,Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0a;color:#e5e5e5;border-radius:16px;overflow:hidden;">
  <div style="padding:40px 32px 24px;text-align:center;border-bottom:1px solid #1a1a1a;">
    <h1 style="color:#f87171;font-size:24px;margin:0 0 8px;font-weight:700;">Beta Key Expired</h1>
    <p style="color:#a3a3a3;margin:0;font-size:15px;">Hi {name},</p>
  </div>
  <div style="padding:32px;">
    <p style="margin:0 0 16px;font-size:15px;color:#d4d4d4;">
      Your beta key <code style="color:#f87171;background:#7f1d1d30;padding:2px 6px;border-radius:4px;">{masked_key}</code>
      was not activated within 48 hours and has been reassigned to the next person on the waitlist.
    </p>
    <p style="margin:0 0 24px;font-size:15px;color:#d4d4d4;">
      If you'd still like to try Hedge Edge, you can request a new key from our website:
    </p>
    <div style="text-align:center;margin:0 0 24px;">
      <a href="https://hedgedge.info" style="display:inline-block;background:#22c55e;color:#000;font-weight:700;text-decoration:none;padding:14px 28px;border-radius:10px;font-size:15px;">Request New Key</a>
    </div>
  </div>
  <div style="padding:16px 32px;border-top:1px solid #1a1a1a;text-align:center;">
    <p style="font-size:12px;color:#525252;margin:0;">Questions? Reply to this email &bull; <a href="https://hedgedge.info/support" style="color:#22c55e;">hedgedge.info/support</a></p>
  </div>
</div>"""


def revoke_key(db, item: dict, notify: bool = True):
    """Return a key to the pool and optionally notify the user."""
    db.table("licenses").update({
        "email": POOL_PLACEHOLDER,
        "notes": json.dumps({
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "revoked_from": item["email"],
            "reason": f"not activated within {EXPIRY_HOURS}h",
        }),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("license_key", item["license_key"]).execute()

    if notify:
        try:
            html = build_revocation_email(item["first_name"], item["license_key"])
            send_email(
                to=item["email"],
                subject="Your Hedge Edge Beta Key Has Expired",
                html=html,
                reply_to="reply@hedgedge.info",
                tags=[
                    {"name": "category", "value": "beta-revocation"},
                    {"name": "key", "value": item["license_key"][:8]},
                ],
            )
            print(f"    Notified {item['email']}")
        except Exception as e:
            print(f"    Warning: notification failed for {item['email']}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Beta key 48h revocation")
    parser.add_argument("--revoke", action="store_true", help="Actually revoke expired keys (default: dry-run)")
    parser.add_argument("--status", action="store_true", help="Show pool status and exit")
    parser.add_argument("--no-notify", action="store_true", help="Skip sending revocation emails")
    args = parser.parse_args()

    if args.status:
        pool_status()
        return

    db = get_db()
    expired = find_expired_claims(db)

    if not expired:
        print("No expired claims found. All claimed keys are either activated or still within 48h.")
        pool_status()
        return

    print(f"Found {len(expired)} expired claim(s):")
    print("-" * 80)
    for item in expired:
        hours_ago = (
            datetime.now(timezone.utc) - datetime.fromisoformat(item["claimed_at"])
        ).total_seconds() / 3600
        print(f"  {item['license_key']}  →  {item['email']:<35}  claimed {hours_ago:.0f}h ago")

    if not args.revoke:
        print()
        print("DRY RUN — no changes made. Use --revoke to reclaim these keys.")
        return

    print()
    print("Revoking...")
    for item in expired:
        revoke_key(db, item, notify=not args.no_notify)
        print(f"  ✅ {item['license_key'][:10]}... → returned to pool")

    print()
    pool_status()


if __name__ == "__main__":
    main()
