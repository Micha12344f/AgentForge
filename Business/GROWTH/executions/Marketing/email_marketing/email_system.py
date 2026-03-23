#!/usr/bin/env python3
"""
email_system.py — Marketing Agent: Waitlist Nurture Task
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified email pipeline: Supabase sync → welcome → drip → enrich → Notion.

Actions:
    --action run              Full cycle (sync + welcome + drips + enrich)
    --action status           Show pipeline status
    --action sync-supabase    Pull new signups from Supabase → Notion
    --action enrich           Update Notion from Resend delivery data
    --action health           Full metrics health report

Usage (from agent dispatcher):
    python email_system.py --action run
    python email_system.py --action status
    python email_system.py --action health
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta


def _find_orchestrator_root() -> str:
    """Walk up from this file until we find a directory containing both
    'shared/' and 'Business/' — that's the Orchestrator root."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if (os.path.isdir(os.path.join(d, "shared")) and
                os.path.isdir(os.path.join(d, "Business"))):
            return d
        d = os.path.dirname(d)
    raise RuntimeError(
        "Cannot locate Orchestrator root (no shared/ + Business/ found)"
    )


_ROOT = _find_orchestrator_root()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from shared.notion_client import query_db, add_row, update_row, log_task
from shared.resend_client import send_email, list_contacts, list_audiences
from shared.supabase_client import get_supabase
from shared.alerting import send_alert


# ── Helpers ──────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _safe_get(row: dict, key: str, default=""):
    v = row.get(key)
    return v if v is not None else default


# ── Action: status ───────────────────────────────────────

def action_status(_args):
    """Show current email pipeline status."""
    print("=" * 60)
    print("  📧 EMAIL PIPELINE STATUS")
    print("=" * 60)

    # Pull email_sends counts
    sends = query_db("email_sends")
    total = len(sends)
    by_status = {}
    for s in sends:
        st = _safe_get(s, "Status", "Unknown")
        by_status[st] = by_status.get(st, 0) + 1

    print(f"\n  Total email_sends records: {total}")
    for st, cnt in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"    {st:20s} {cnt:>5d}")

    # Pull campaigns
    campaigns = query_db("campaigns")
    active = [c for c in campaigns if _safe_get(c, "Status") == "Active"]
    print(f"\n  Campaigns: {len(campaigns)} total, {len(active)} active")
    for c in active:
        print(f"    • {_safe_get(c, 'Name', '?')}")

    # Pull sequences
    sequences = query_db("email_sequences")
    print(f"\n  Email Sequences: {len(sequences)}")
    for seq in sequences[:5]:
        print(f"    • {_safe_get(seq, 'Name', '?')} — {_safe_get(seq, 'Status', '?')}")

    # Pull leads CRM count
    leads = query_db("leads_crm")
    print(f"\n  Leads CRM: {len(leads)} records")

    print(f"\n  Snapshot: {_now()}")
    print("=" * 60)

    log_task("Marketing", "waitlist-nurture/status", "Complete", "P3",
             f"{total} sends, {len(active)} active campaigns, {len(leads)} leads")


# ── Action: sync-supabase ────────────────────────────────

def action_sync_supabase(_args):
    """Pull new signups from Supabase waitlist → add to Notion email_sends."""
    print("=" * 60)
    print("  🔄 SUPABASE → NOTION SYNC")
    print("=" * 60)

    sb = get_supabase(use_service_role=True)

    # Get signups from Supabase profiles
    result = sb.table("profiles").select("*").order("created_at", desc=True).limit(200).execute()
    supabase_emails = {r["email"].lower().strip() for r in result.data if r.get("email")}

    # Get existing email_sends
    existing = query_db("email_sends")
    existing_emails = {_safe_get(r, "Email", "").lower().strip() for r in existing}

    new_signups = supabase_emails - existing_emails
    print(f"\n  Supabase waitlist:  {len(supabase_emails)}")
    print(f"  Already in Notion:  {len(existing_emails)}")
    print(f"  New to sync:        {len(new_signups)}")

    synced = 0
    for email in sorted(new_signups):
        # Find the matching Supabase record for metadata
        sb_record = next((r for r in result.data if r.get("email", "").lower().strip() == email), {})
        try:
            add_row("email_sends", {
                "Email": email,
                "Status": "Active",
                "Source": sb_record.get("source", "waitlist"),
                "Signup Date": sb_record.get("created_at", _now())[:10],
                "Wave": sb_record.get("wave", 1),
            })
            synced += 1
        except Exception as e:
            print(f"    ⚠️  Failed to sync {email}: {e}")

    print(f"\n  ✅ Synced {synced} new signups to Notion email_sends")

    log_task("Marketing", "waitlist-nurture/sync-supabase", "Complete", "P2",
             f"Synced {synced} new signups from Supabase")


# ── Action: enrich ───────────────────────────────────────

def action_enrich(_args):
    """Update Notion email_sends from Resend audience contact data."""
    print("=" * 60)
    print("  📈 RESEND → NOTION ENRICHMENT")
    print("=" * 60)

    # Get audiences from Resend
    try:
        audiences = list_audiences()
    except Exception as e:
        print(f"  ❌ Failed to fetch Resend audiences: {e}")
        return

    if not audiences:
        print("  No Resend audiences found")
        return

    print(f"  Resend audiences: {len(audiences)}")

    # Get contacts from each audience
    all_contacts = []
    for aud in audiences:
        aud_id = aud.get("id", "")
        aud_name = aud.get("name", "?")
        try:
            contacts = list_contacts(aud_id)
            all_contacts.extend(contacts)
            print(f"    • {aud_name}: {len(contacts)} contacts")
        except Exception as e:
            print(f"    ⚠️  Failed to get contacts for {aud_name}: {e}")

    # Get Notion email_sends for matching
    sends = query_db("email_sends")
    email_map = {}
    for s in sends:
        e = _safe_get(s, "Email", "").lower().strip()
        if e:
            email_map[e] = s

    enriched = 0
    for contact in all_contacts:
        email = (contact.get("email") or "").lower().strip()
        if email in email_map:
            notion_row = email_map[email]
            row_id = notion_row.get("id", "")
            if not row_id:
                continue

            updates = {}
            # Sync unsubscribed status
            if contact.get("unsubscribed") and _safe_get(notion_row, "Status") != "Unsubscribed":
                updates["Status"] = "Unsubscribed"

            if updates:
                try:
                    update_row("email_sends", row_id, updates)
                    enriched += 1
                except Exception as e:
                    print(f"    ⚠️  Failed to enrich {email}: {e}")

    print(f"\n  ✅ Enriched {enriched} records from Resend contact data")

    log_task("Marketing", "waitlist-nurture/enrich", "Complete", "P3",
             f"Enriched {enriched} email_sends records")


# ── Action: health ───────────────────────────────────────

def action_health(_args):
    """Full email system health report."""
    print("=" * 60)
    print("  🏥 EMAIL SYSTEM HEALTH REPORT")
    print("=" * 60)

    # Check API connectivity
    checks = []

    # 1. Notion
    try:
        campaigns = query_db("campaigns")
        checks.append(("Notion API", "🟢", f"{len(campaigns)} campaigns"))
    except Exception as e:
        checks.append(("Notion API", "🔴", str(e)[:60]))

    # 2. Resend
    try:
        audiences = list_audiences()
        checks.append(("Resend API", "🟢", f"{len(audiences)} audiences"))
    except Exception as e:
        checks.append(("Resend API", "🔴", str(e)[:60]))

    # 3. Supabase
    try:
        sb = get_supabase(use_service_role=True)
        result = sb.table("profiles").select("id", count="exact").limit(1).execute()
        checks.append(("Supabase", "🟢", f"{result.count} profile rows"))
    except Exception as e:
        checks.append(("Supabase", "🔴", str(e)[:60]))

    # 4. Email sends volume
    try:
        sends = query_db("email_sends")
        active = [s for s in sends if _safe_get(s, "Status") == "Active"]
        checks.append(("Email Pipeline", "🟢", f"{len(active)} active / {len(sends)} total"))
    except Exception as e:
        checks.append(("Email Pipeline", "🔴", str(e)[:60]))

    # 5. Leads CRM
    try:
        leads = query_db("leads_crm")
        checks.append(("Leads CRM", "🟢", f"{len(leads)} leads"))
    except Exception as e:
        checks.append(("Leads CRM", "🔴", str(e)[:60]))

    print()
    for name, status, detail in checks:
        print(f"  {status} {name:20s} {detail}")

    healthy = sum(1 for _, st, _ in checks if st == "🟢")
    total = len(checks)
    print(f"\n  Overall: {healthy}/{total} healthy")
    print(f"  Timestamp: {_now()}")
    print("=" * 60)

    log_task("Marketing", "waitlist-nurture/health", "Complete", "P3",
             f"{healthy}/{total} systems healthy")


# ── Action: run (full cycle) ─────────────────────────────

def action_run(_args):
    """Full email nurture cycle: sync → enrich → status."""
    print("🚀 FULL EMAIL NURTURE CYCLE")
    print("━" * 40)

    print("\n[1/3] Syncing Supabase signups …")
    action_sync_supabase(_args)

    print("\n[2/3] Enriching from Resend …")
    action_enrich(_args)

    print("\n[3/3] Pipeline status …")
    action_status(_args)

    print("\n✅ Full nurture cycle complete")

    send_alert(
        "📧 Email Nurture Cycle Complete",
        f"Full cycle ran at {_now()}",
        "info",
    )


# ── CLI ──────────────────────────────────────────────────

ACTIONS = {
    "run": action_run,
    "status": action_status,
    "sync-supabase": action_sync_supabase,
    "enrich": action_enrich,
    "health": action_health,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email Nurture System")
    parser.add_argument("--action", default="status",
                        choices=list(ACTIONS.keys()))
    args = parser.parse_args()
    ACTIONS[args.action](args)
