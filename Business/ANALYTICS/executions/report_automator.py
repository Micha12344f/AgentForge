#!/usr/bin/env python3
"""
report_automator.py — Automated Business Reports
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates daily, weekly, and monthly business reports by pulling
data from Notion (KPIs, funnels, campaigns) and formatting them
for Discord delivery or PDF export.

Usage:
    python report_automator.py --action daily
    python report_automator.py --action weekly
    python report_automator.py --action monthly
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import query_db, log_task
from shared.alerting import send_alert


def _get_latest_kpi() -> dict:
    """Get the most recent KPI snapshot."""
    rows = query_db("kpi_snapshots", page_size=5, sorts=[
        {"property": "Date", "direction": "descending"}
    ])
    return rows[0] if rows else {}


def _get_campaign_stats() -> list[dict]:
    """Get active campaign statistics."""
    return query_db("campaigns", page_size=20)


def daily_report() -> str:
    """Generate daily business report."""
    print("=" * 60)
    print("  📊 Daily Business Report")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print("=" * 60)

    kpi = _get_latest_kpi()
    if kpi:
        print(f"\n  MRR:           ${kpi.get('MRR', 0):,.0f}")
        print(f"  Total Leads:   {kpi.get('Total Leads', 0)}")
        print(f"  Active Users:  {kpi.get('Active Users', 0)}")
        print(f"  Emails Sent:   {kpi.get('Emails Sent', 0)}")
        print(f"  Signups:       {kpi.get('Signups', 0)}")
    else:
        print("\n  ⚠️  No KPI snapshot data available.")

    campaigns = _get_campaign_stats()
    active = [c for c in campaigns if (c.get("Status") or "").lower() == "active"]
    print(f"\n  Active Campaigns: {len(active)}")
    for c in active:
        name = c.get("Campaign Name", "Untitled")
        sent = c.get("Emails Sent", 0)
        print(f"    • {name}: {sent} sent")

    report = f"Daily Report: MRR=${kpi.get('MRR', 0)}, Leads={kpi.get('Total Leads', 0)}"
    print(f"\n{'─' * 60}")
    return report


def weekly_report() -> str:
    """Generate weekly business report with trends."""
    print("=" * 60)
    print("  📊 Weekly Business Report")
    print("=" * 60)

    kpis = query_db("kpi_snapshots", page_size=7, sorts=[
        {"property": "Date", "direction": "descending"}
    ])

    if len(kpis) >= 2:
        latest = kpis[0]
        prev = kpis[-1]
        print(f"\n  MRR:    ${latest.get('MRR', 0):,.0f} (was ${prev.get('MRR', 0):,.0f})")
        print(f"  Leads:  {latest.get('Total Leads', 0)} (was {prev.get('Total Leads', 0)})")
        print(f"  Users:  {latest.get('Active Users', 0)} (was {prev.get('Active Users', 0)})")
    elif kpis:
        latest = kpis[0]
        print(f"\n  MRR: ${latest.get('MRR', 0):,.0f}")
        print(f"  Leads: {latest.get('Total Leads', 0)}")
    else:
        print("\n  ⚠️  No KPI data available for weekly report.")

    report = "Weekly report generated"
    print(f"\n{'─' * 60}")
    return report


def monthly_report() -> str:
    """Generate monthly business report."""
    print("=" * 60)
    print("  📊 Monthly Business Report")
    print("=" * 60)

    kpis = query_db("kpi_snapshots", page_size=30, sorts=[
        {"property": "Date", "direction": "descending"}
    ])

    if kpis:
        latest = kpis[0]
        oldest = kpis[-1]
        print(f"\n  Period: {oldest.get('Date', '?')} → {latest.get('Date', '?')}")
        print(f"  MRR Start:  ${oldest.get('MRR', 0):,.0f}")
        print(f"  MRR End:    ${latest.get('MRR', 0):,.0f}")
        leads_start = oldest.get("Total Leads", 0)
        leads_end = latest.get("Total Leads", 0)
        print(f"  Leads:      {leads_start} → {leads_end} (+{leads_end - leads_start})")
    else:
        print("\n  ⚠️  No KPI data for monthly report.")

    report = "Monthly report generated"
    print(f"\n{'─' * 60}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Report Automator")
    parser.add_argument("--action", required=True, choices=["daily", "weekly", "monthly"])
    args = parser.parse_args()

    if args.action == "daily":
        report = daily_report()
    elif args.action == "weekly":
        report = weekly_report()
    elif args.action == "monthly":
        report = monthly_report()

    log_task("Analytics", "report", args.action, "success", notes=report[:200])


if __name__ == "__main__":
    main()
