#!/usr/bin/env python3
"""
email_sequence_manager.py — Marketing Agent Email Orchestration

CLI entry point for email-related tasks triggered via the agent dispatcher.
Bridges to the existing cron email_send system for on-demand sends,
and provides campaign status + sequence management.

Usage:
    python email_sequence_manager.py --action send-now
    python email_sequence_manager.py --action sanity-check
    python email_sequence_manager.py --action campaign-status
    python email_sequence_manager.py --action list-sequences
"""

import sys
import os
import argparse
from datetime import datetime, timezone

_EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_EXEC_DIR, *(['..'] * 5)))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import query_db, log_task
from shared.alerting import send_alert


def send_now(args):
    """Trigger an on-demand email send using the existing email_send system."""
    print("=" * 60)
    print("  📧 ON-DEMAND EMAIL SEND")
    print("=" * 60)

    # Import the cron email_send module
    railway_dir = os.path.join(_WORKSPACE, "scripts", "Railway")
    sys.path.insert(0, railway_dir)

    try:
        from email_send import run_email_send
    except ImportError:
        print("❌ Could not import email_send module from scripts/Railway/")
        print(f"   Searched: {railway_dir}")
        sys.exit(1)

    dry_run = getattr(args, "dry_run", False)
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE SEND'}")
    print("─" * 60)

    summary = run_email_send(dry_run=dry_run)
    sent = summary.get("sent", 0)
    errors = summary.get("errors", 0)
    campaigns = summary.get("per_campaign", {})

    print(f"\n  Sent: {sent} | Errors: {errors}")
    for camp_name, count in campaigns.items():
        print(f"    • {camp_name}: {count}")

    # Alert to Discord
    campaign_lines = "\n".join(f"• **{k}**: {v}" for k, v in campaigns.items())
    send_alert(
        f"📧 Email Send Complete — {sent} sent",
        f"**Sent:** {sent} | **Errors:** {errors}\n\n{campaign_lines}",
        "info" if errors == 0 else "warn",
        fields=[
            {"name": "Agent", "value": "Marketing", "inline": True},
            {"name": "Task", "value": "email-sequences/send-now", "inline": True},
            {"name": "Mode", "value": "DRY RUN" if dry_run else "LIVE", "inline": True},
        ],
    )

    log_task("Marketing", "email-sequences/send-now", "Complete", "P1",
             f"Sent={sent}, Errors={errors}, Campaigns={len(campaigns)}")

    print(f"\n✅ Email send complete")


def sanity_check(args):
    """Run a read-only fallback check of campaign assignments and due emails."""
    from email_send_sanity import run_sanity_check, inspect_lead

    print("=" * 60)
    print("  📧 EMAIL SANITY CHECK")
    print("=" * 60)

    if getattr(args, "email", None):
        inspect_lead(args.email)
        log_task("Marketing", "email-sequences/sanity-check", "Complete", "P2",
                 f"Lead inspection for {args.email}")
        return

    summary = run_sanity_check(limit=getattr(args, "limit", 5))
    print(f"\n✅ Sanity check complete — due={summary['due']} assigned={summary['assigned']} unassigned={summary['unassigned']}")


def campaign_status(args):
    """Show status of all email campaigns."""
    campaigns = query_db("campaigns")

    print("=" * 60)
    print("  📧 CAMPAIGN STATUS")
    print("=" * 60)

    by_status = {}
    for c in campaigns:
        status = c.get("Status", "Unknown")
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(c)

    for status in ["Active", "Draft", "Paused", "Completed", "Unknown"]:
        if status not in by_status:
            continue
        items = by_status[status]
        print(f"\n  {status} ({len(items)})")
        for c in items:
            name = c.get("Name", "?")
            open_rate = c.get("Open Rate", 0)
            click_rate = c.get("Click Rate", 0)
            print(f"    • {name}  (Open: {open_rate}% | Click: {click_rate}%)")

    total = len(campaigns)
    active = len(by_status.get("Active", []))
    print(f"\n{'─' * 60}")
    print(f"  Total: {total} campaigns | {active} active")

    log_task("Marketing", "email-sequences/campaign-status", "Complete", "P3",
             f"{total} campaigns, {active} active")


def list_sequences(args):
    """List email sequences from Notion."""
    sequences = query_db("email_sequences")

    print("=" * 60)
    print("  📧 EMAIL SEQUENCES")
    print("=" * 60)

    if not sequences:
        print("\n  No sequences found")
        return

    for seq in sequences:
        name = seq.get("Subject Line") or seq.get("Template", "?")
        sent = seq.get("Sent Count", 0)
        delivered = seq.get("Delivered Count", 0)
        open_r = seq.get("Open Rate", 0)
        click_r = seq.get("Click Rate", 0)
        print(f"\n  {name}")
        print(f"    Sent: {sent} | Delivered: {delivered} | Open: {open_r}% | Click: {click_r}%")

    print(f"\n  Total: {len(sequences)} sequences")
    log_task("Marketing", "email-sequences/list-sequences", "Complete", "P3",
             f"{len(sequences)} sequences listed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Marketing Email Sequence Manager")
    parser.add_argument("--action", required=True,
                        choices=["send-now", "sanity-check", "campaign-status", "list-sequences"])
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="Run email send in dry-run mode (no actual sends)")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max due leads shown per campaign for sanity-check")
    parser.add_argument("--email",
                        help="Inspect a single lead email during sanity-check")
    args = parser.parse_args()
    {"send-now": send_now, "sanity-check": sanity_check, "campaign-status": campaign_status,
     "list-sequences": list_sequences}[args.action](args)
