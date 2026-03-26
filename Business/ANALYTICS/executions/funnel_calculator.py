#!/usr/bin/env python3
"""
funnel_calculator.py — Conversion Funnel Calculator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Calculates conversion funnels from Notion data:
  • Email funnel: sent → delivered → opened → clicked → replied
  • Signup funnel: visitor → lead → demo → trial → paid
  • Stage drop-off rates and bottleneck identification

Usage:
    python funnel_calculator.py --action snapshot
    python funnel_calculator.py --action email-funnel
    python funnel_calculator.py --action signup-funnel
"""

import sys
import os
import argparse
from datetime import datetime, timezone

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import query_db, add_row, log_task


# ──────────────────────────────────────────────
# Email Funnel
# ──────────────────────────────────────────────
def calculate_email_funnel() -> dict:
    """Calculate email funnel: sent → delivered → opened → clicked → replied."""
    print("  [Email Funnel] Querying leads DB for email stats ...")
    rows = query_db("email_sends", page_size=100)

    stages = {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "replied": 0, "bounced": 0}
    for row in rows:
        status = (row.get("Last Email Status") or "").lower()
        if status in stages:
            stages[status] += 1
        has_replied = row.get("Has Replied", False)
        if has_replied:
            stages["replied"] += 1

    stages["sent"] = len(rows)
    print(f"  Sent: {stages['sent']} → Delivered: {stages['delivered']} → "
          f"Opened: {stages['opened']} → Clicked: {stages['clicked']} → "
          f"Replied: {stages['replied']}")

    # Calculate drop-off rates
    funnel_order = ["sent", "delivered", "opened", "clicked", "replied"]
    dropoffs = {}
    for i in range(1, len(funnel_order)):
        prev = stages[funnel_order[i - 1]]
        curr = stages[funnel_order[i]]
        rate = (curr / prev * 100) if prev > 0 else 0
        dropoffs[f"{funnel_order[i-1]}_to_{funnel_order[i]}"] = round(rate, 1)

    return {"stages": stages, "dropoffs": dropoffs}


# ──────────────────────────────────────────────
# Signup Funnel
# ──────────────────────────────────────────────
def calculate_signup_funnel() -> dict:
    """Calculate signup funnel from CRM and demo data."""
    print("  [Signup Funnel] Querying CRM and demo data ...")

    leads = query_db("leads_crm", page_size=100)
    demos = query_db("demo_log", page_size=100)

    stages = {
        "leads": len(leads),
        "demos_booked": len(demos),
        "demos_completed": sum(1 for d in demos if (d.get("Status") or "").lower() == "completed"),
        "trials": 0,  # TODO: pull from Supabase subscriptions
        "paid": 0,     # TODO: pull from Creem
    }

    print(f"  Leads: {stages['leads']} → Demos: {stages['demos_booked']} → "
          f"Completed: {stages['demos_completed']} → Trials: {stages['trials']} → "
          f"Paid: {stages['paid']}")

    return {"stages": stages}


def snapshot() -> dict:
    """Run all funnels and return combined report."""
    print("=" * 60)
    print("  Funnel Snapshot")
    print("=" * 60)

    email = calculate_email_funnel()
    signup = calculate_signup_funnel()

    return {"email_funnel": email, "signup_funnel": signup}


def main():
    parser = argparse.ArgumentParser(description="Funnel Calculator")
    parser.add_argument("--action", required=True,
                        choices=["snapshot", "email-funnel", "signup-funnel"])
    args = parser.parse_args()

    if args.action == "snapshot":
        result = snapshot()
    elif args.action == "email-funnel":
        result = calculate_email_funnel()
    elif args.action == "signup-funnel":
        result = calculate_signup_funnel()

    log_task("Analytics", "funnel-calc", args.action, "success")


if __name__ == "__main__":
    main()
