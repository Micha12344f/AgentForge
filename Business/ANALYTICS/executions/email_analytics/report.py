"""
report.py — Email marketing analytics report for the Analytics Agent.

Pulls campaign, template, and lead engagement data from Notion and prints
formatted summaries for campaign health, sequence funnels, and lead segments.

Usage:
    python -m Business.ANALYTICS.executions.email_analytics.report
"""

import os
import sys

_EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_EXEC_DIR, *(['..'] * 4)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from shared.notion_client import query_db


# ──────────────────────────────────────────────
# Data Access (replaces old non-existent sub-modules)
# ──────────────────────────────────────────────

def read_campaign_metrics() -> list[dict]:
    """Pull campaign rows from Notion campaigns DB."""
    rows = query_db("campaigns", page_size=50)
    results = []
    for row in rows:
        results.append({
            "name": row.get("Name") or row.get("Campaign Name") or "",
            "status": row.get("Status") or "Unknown",
            "total_sent": int(row.get("Emails Sent") or 0),
            "total_delivered": int(row.get("Delivered") or 0),
            "total_bounced": int(row.get("Bounced") or 0),
            "total_opened": int(row.get("Opened") or 0),
            "total_clicked": int(row.get("Clicked") or 0),
            "total_replied": int(row.get("Replied") or 0),
            "invisible_fail_count": max(0, int(row.get("Emails Sent") or 0) - int(row.get("Delivered") or 0) - int(row.get("Bounced") or 0)),
            "delivery_rate_pct": round(int(row.get("Delivered") or 0) / max(int(row.get("Emails Sent") or 0), 1) * 100, 1),
        })
    return results


def read_template_metrics() -> list[dict]:
    """Pull email sequence/template metrics from Notion email_sequences DB."""
    rows = query_db("email_sequences", page_size=50)
    results = []
    for idx, row in enumerate(rows, start=1):
        sent = int(row.get("Sent Count") or row.get("Total Sent") or row.get("Emails Count") or 0)
        delivered = int(row.get("Delivered Count") or row.get("Total Delivered") or 0)
        results.append({
            "template_name": row.get("Template") or row.get("Name") or "",
            "subject_line": row.get("Subject Line") or "",
            "sent_count": sent,
            "delivered_count": delivered,
            "opened_count": int(row.get("Opened Count") or row.get("Total Opened") or 0),
            "clicked_count": int(row.get("Clicked Count") or row.get("Total Clicked") or 0),
            "replied_count": int(row.get("Replied Count") or row.get("Total Replied") or 0),
            "invisible_fail_count": max(0, sent - delivered - int(row.get("Bounced Count") or 0)),
            "delivery_rate_pct": round(delivered / max(sent, 1) * 100, 1),
            "open_rate": row.get("Open Rate") or 0,
            "click_rate": row.get("Click Rate") or 0,
            "reply_rate": row.get("Reply Rate") or 0,
            "seq_num": idx,
        })
    return results


def read_lead_engagement() -> list[dict]:
    """Pull lead engagement data from Notion email_sends (Leads DB)."""
    rows = query_db("email_sends", page_size=200)
    results = []
    for row in rows:
        status = (row.get("Last Email Status") or "Unknown").lower()
        opens = int(row.get("Opens") or row.get("Total Opens") or (1 if status in ("opened", "clicked") else 0))
        clicks = int(row.get("Clicks") or row.get("Total Clicks") or (1 if status == "clicked" else 0))
        unsubscribed = row.get("Unsubscribed", False)

        if clicks > 0:
            segment = "Hot"
        elif opens >= 2:
            segment = "Warm"
        elif status == "bounced" or unsubscribed:
            segment = "Invalid"
        else:
            segment = "Cold"

        results.append({
            "email": row.get("Email") or row.get("Name") or "",
            "status": row.get("Last Email Status") or "Unknown",
            "total_opens": opens,
            "total_clicks": clicks,
            "unsubscribed": unsubscribed,
            "segment": segment,
        })
    return results


def _pct(numerator, denominator):
    """Safe percentage: returns 0.0 if denominator is 0."""
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 1)


def _delivery_health(rate):
    if rate >= 95:
        return "HEALTHY"
    if rate >= 90:
        return "WARNING"
    return "CRITICAL"


def _open_health(rate):
    if rate >= 35:
        return "EXCELLENT"
    if rate >= 20:
        return "AVERAGE"
    return "WEAK"


def _click_health(rate):
    if rate >= 5:
        return "STRONG"
    if rate >= 1:
        return "LOW"
    return "ZERO"


def print_campaign_report():
    campaigns = read_campaign_metrics()
    active = [c for c in campaigns if c.get("status") == "Active"]
    other = [c for c in campaigns if c.get("status") != "Active"]

    print("=" * 60)
    print("  CAMPAIGN SUMMARY")
    print("=" * 60)

    print(f"\n  Active campaigns: {len(active)}")
    print(f"  In-pipeline / discontinued: {len(other)}\n")

    for c in active:
        sent = c.get("total_sent", 0)
        delivered = c.get("total_delivered", 0)
        bounced = c.get("total_bounced", 0)
        opened = c.get("total_opened", 0)
        clicked = c.get("total_clicked", 0)
        replied = c.get("total_replied", 0)
        invisible = c.get("invisible_fail_count", 0)
        delivery_rate = c.get("delivery_rate_pct", 0)

        open_rate = _pct(opened, delivered)
        click_rate = _pct(clicked, delivered)
        reply_rate = _pct(replied, delivered)
        bounce_rate = _pct(bounced, sent)

        print(f"  Campaign: {c.get('name')}")
        print(f"    Status:          {c.get('status')}")
        print(f"    Deliverability:  {sent} sent -> {delivered} delivered ({delivery_rate}%)  [{_delivery_health(delivery_rate)}]")
        print(f"    Bounced:         {bounced} ({bounce_rate}%)")
        print(f"    Invisible Fails: {invisible}  (silently dropped by spam filters)")
        print(f"    Open Rate:       {opened} opens  ({open_rate}%)  [{_open_health(open_rate)}]")
        print(f"    Click Rate:      {clicked} clicks ({click_rate}%)  [{_click_health(click_rate)}]")
        print(f"    Reply Rate:      {replied} replies ({reply_rate}%)")
        print()


def print_template_funnel(active_campaign_name=None):
    templates = read_template_metrics()

    # Filter to only templates with sends > 0 for a useful funnel view
    live = [t for t in templates if (t.get("sent_count") or 0) > 0]

    print("=" * 60)
    print("  EMAIL SEQUENCE FUNNEL BREAKDOWN")
    print("=" * 60)
    if active_campaign_name:
        print(f"  Filtering to campaign: {active_campaign_name}\n")
    else:
        print("  Showing all templates with send volume.\n")

    for t in live:
        sent = t.get("sent_count", 0)
        delivered = t.get("delivered_count", 0)
        opened = t.get("opened_count", 0)
        clicked = t.get("clicked_count", 0)
        replied = t.get("replied_count", 0)
        invisible = t.get("invisible_fail_count", 0)
        delivery_rate = t.get("delivery_rate_pct", 0)

        # Use Notion rollup rates when available, otherwise compute
        open_rate = t.get("open_rate") or _pct(opened, delivered)
        click_rate = t.get("click_rate") or _pct(clicked, delivered)
        reply_rate = t.get("reply_rate") or _pct(replied, delivered)

        print(f"  [{t.get('template_name')}]")
        print(f"    Subject:         \"{t.get('subject_line')}\"")
        print(f"    Deliverability:  {sent} sent -> {delivered} delivered ({delivery_rate}%)  [{_delivery_health(delivery_rate)}]")
        print(f"    Invisible Fails: {invisible}")
        print(f"    Open Rate:       {opened} opens  ({open_rate}%)  [{_open_health(open_rate)}]")
        print(f"    Click Rate:      {clicked} clicks ({click_rate}%)  [{_click_health(click_rate)}]")
        print(f"    Reply Rate:      {replied} replies ({reply_rate}%)")
        print()


def print_lead_summary():
    leads = read_lead_engagement()

    segments = {"Hot": [], "Warm": [], "Cold": [], "Invalid": []}
    for lead in leads:
        seg = lead.get("segment", "Cold")
        segments.setdefault(seg, []).append(lead)

    print("=" * 60)
    print("  LEAD SEGMENT DISTRIBUTION")
    print("=" * 60)

    total = len(leads)
    for seg, members in segments.items():
        count = len(members)
        pct = _pct(count, total)
        print(f"    {seg:<10} {count:>4} leads  ({pct}%)")

    print()
    # Highlight zero-click leads with high open rate (missed conversion opportunity)
    missed = [
        l for l in leads
        if l.get("total_opens", 0) >= 3
        and l.get("total_clicks", 0) == 0
        and not l.get("unsubscribed", False)
    ]
    print(f"  Missed conversions (3+ opens, 0 clicks): {len(missed)} leads")
    print("  These are readers who never clicked. Strong candidates for a personalised CTA nudge.")
    print()


def run_full_report():
    print("\n")
    print_campaign_report()
    print()
    print_template_funnel()
    print()
    print_lead_summary()


if __name__ == "__main__":
    run_full_report()
