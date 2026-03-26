#!/usr/bin/env python3
"""
kpi_snapshot.py — Analytics Agent KPI Dashboard

Queries Notion kpi_snapshots and funnel_metrics, computes day-over-day
deltas, and outputs a formatted report. Optionally posts to Discord.

Usage:
    python kpi_snapshot.py --action daily-report
    python kpi_snapshot.py --action latest
    python kpi_snapshot.py --action weekly-report
"""

import sys
import os
import argparse
import json

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timezone

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import query_db, log_task
from shared.alerting import send_alert
from shared.llm_router import chat as routed_chat


def _delta_str(current, previous) -> str:
    """Format a delta as +X / -X / ±0."""
    if current is None or previous is None:
        return "n/a"
    diff = current - previous
    if diff > 0:
        return f"+{diff:,.0f}" if isinstance(diff, (int, float)) else f"+{diff}"
    elif diff < 0:
        return f"{diff:,.0f}" if isinstance(diff, (int, float)) else f"{diff}"
    return "±0"


def _pct_change(current, previous) -> str:
    if not previous or not current:
        return ""
    pct = ((current - previous) / abs(previous)) * 100
    if pct > 0:
        return f" (+{pct:.1f}%)"
    elif pct < 0:
        return f" ({pct:.1f}%)"
    return ""


def _safe_number(value):
    return value if isinstance(value, (int, float)) else None


def _generate_briefing(report_type: str, payload: dict) -> str | None:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the Hedge Edge Analytics agent. "
                "Write a concise executive briefing from KPI data only. "
                "Do not invent numbers. "
                "Return 3 short bullets separated by newlines. "
                "Each bullet must start with '- '. "
                "Focus on movement, likely implication, and the next metric to watch."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"report_type": report_type, "payload": payload}, default=str),
        },
    ]
    try:
        briefing = routed_chat(
            "analytics",
            messages,
            temperature=0.1,
            max_tokens=220,
        )
    except Exception:
        return None

    cleaned = "\n".join(line.strip() for line in str(briefing).splitlines() if line.strip())
    return cleaned or None


def daily_report():
    """Pull latest KPI snapshot + funnel metrics, compute deltas, print report."""
    # Pull kpi_snapshots sorted by date (most recent first)
    snapshots = query_db(
        "kpi_snapshots",
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=2,
    )

    if not snapshots:
        print("❌ No KPI snapshots found in Notion")
        return

    latest = snapshots[0]
    previous = snapshots[1] if len(snapshots) > 1 else {}

    # Pull funnel metrics
    funnels = query_db(
        "funnel_metrics",
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=2,
    )
    funnel_latest = funnels[0] if funnels else {}
    funnel_prev = funnels[1] if len(funnels) > 1 else {}

    # Build report
    date_str = latest.get("Date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    print("=" * 60)
    print(f"  📊 KPI DAILY REPORT — {date_str}")
    print("=" * 60)

    # Key metrics with deltas
    metrics = [
        ("Page Views", "Page Views"),
        ("Unique Visitors", "Unique Visitors"),
        ("Signups", "Signups"),
        ("Active Subs", "Active Subs"),
        ("MRR", "MRR"),
        ("Emails Sent", "Emails Sent"),
        ("Email Opens", "Email Opens"),
        ("Email Clicks", "Email Clicks"),
    ]

    report_lines = []
    for label, key in metrics:
        val = latest.get(key)
        prev_val = previous.get(key)
        if val is not None:
            delta = _delta_str(val, prev_val)
            pct = _pct_change(val, prev_val)
            line = f"  {label}: {val:,.0f}  ({delta}{pct})" if isinstance(val, (int, float)) else f"  {label}: {val}  ({delta})"
            print(line)
            report_lines.append(f"**{label}:** {val:,.0f} ({delta})" if isinstance(val, (int, float)) else f"**{label}:** {val} ({delta})")

    # Funnel metrics
    if funnel_latest:
        print(f"\n{'─' * 60}")
        print("  📈 FUNNEL")
        funnel_keys = ["Visit→Signup", "Signup→Trial", "Trial→Paid", "Overall Conversion"]
        for key in funnel_keys:
            val = funnel_latest.get(key)
            prev_val = funnel_prev.get(key)
            if val is not None:
                delta = _delta_str(val, prev_val)
                print(f"  {key}: {val}%  ({delta})")
                report_lines.append(f"**{key}:** {val}% ({delta})")

    briefing_payload = {
        "latest": {k: latest.get(k) for _, k in metrics},
        "previous": {k: previous.get(k) for _, k in metrics},
        "funnel_latest": {k: funnel_latest.get(k) for k in ["Visit→Signup", "Signup→Trial", "Trial→Paid", "Overall Conversion"]},
        "funnel_previous": {k: funnel_prev.get(k) for k in ["Visit→Signup", "Signup→Trial", "Trial→Paid", "Overall Conversion"]},
    }
    briefing = _generate_briefing("daily", briefing_payload)
    if briefing:
        print("  🧠 AI BRIEFING")
        for line in briefing.splitlines():
            print(f"  {line}")
        report_lines.append(f"**AI Briefing**\n{briefing}")

    print(f"\n{'─' * 60}")

    # Post to Discord #agent-ops
    discord_desc = "\n".join(report_lines) if report_lines else "No metrics available"
    send_alert(
        f"📊 KPI Daily — {date_str}",
        discord_desc,
        "info",
        fields=[
            {"name": "Agent", "value": "Analytics", "inline": True},
            {"name": "Task", "value": "kpi-snapshot/daily-report", "inline": True},
        ],
    )

    # Log to Notion
    log_task("Analytics", "kpi-snapshot/daily-report", "Complete", "P2",
             f"Date: {date_str} | {len(report_lines)} metrics reported")

    print(f"\n✅ Report complete — {len(report_lines)} metrics")


def latest():
    """Show just the latest snapshot values (no deltas)."""
    snapshots = query_db(
        "kpi_snapshots",
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=1,
    )
    if not snapshots:
        print("❌ No KPI snapshots found")
        return

    snap = snapshots[0]
    print("=" * 60)
    print(f"  📊 LATEST KPI SNAPSHOT — {snap.get('Date', '?')}")
    print("=" * 60)
    for key, val in sorted(snap.items()):
        if key.startswith("_"):
            continue
        print(f"  {key}: {val}")


def weekly_report():
    """Pull last 7 snapshots and show weekly trend."""
    snapshots = query_db(
        "kpi_snapshots",
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=7,
    )
    if not snapshots:
        print("❌ No KPI snapshots found")
        return

    newest = snapshots[0]
    oldest = snapshots[-1]
    days = len(snapshots)

    print("=" * 60)
    print(f"  📊 WEEKLY KPI REPORT ({oldest.get('Date', '?')} → {newest.get('Date', '?')})")
    print("=" * 60)

    trend_keys = ["Page Views", "Signups", "Active Subs", "MRR", "Emails Sent"]
    report_lines = []
    for key in trend_keys:
        new_val = newest.get(key)
        old_val = oldest.get(key)
        if new_val is not None and old_val is not None:
            delta = _delta_str(new_val, old_val)
            pct = _pct_change(new_val, old_val)
            line = f"  {key}: {old_val:,.0f} → {new_val:,.0f}  ({delta}{pct})"
            print(line)
            report_lines.append(f"**{key}:** {old_val:,.0f} → {new_val:,.0f} ({delta})")

    briefing_payload = {
        "newest": {key: newest.get(key) for key in trend_keys},
        "oldest": {key: oldest.get(key) for key in trend_keys},
        "days": days,
    }
    briefing = _generate_briefing("weekly", briefing_payload)
    if briefing:
        print("\n  🧠 AI BRIEFING")
        for line in briefing.splitlines():
            print(f"  {line}")
        report_lines.append(f"**AI Briefing**\n{briefing}")

    # Post to Discord
    discord_desc = "\n".join(report_lines) if report_lines else "No trend data"
    send_alert(
        f"📊 Weekly KPI Trend ({days}d)",
        discord_desc,
        "info",
        fields=[
            {"name": "Agent", "value": "Analytics", "inline": True},
            {"name": "Task", "value": "kpi-snapshot/weekly-report", "inline": True},
        ],
    )
    log_task("Analytics", "kpi-snapshot/weekly-report", "Complete", "P2",
             f"{days} days of data, {len(report_lines)} metrics trended")

    print(f"\n✅ Weekly trend — {days} data points")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analytics KPI Snapshot")
    parser.add_argument("--action", required=True,
                        choices=["daily-report", "latest", "weekly-report"])
    args = parser.parse_args()
    {"daily-report": daily_report, "latest": latest, "weekly-report": weekly_report}[args.action]()
