"""
report.py — Interactive email marketing analytics report for the Analytics Agent.

Run from the repo root with PYTHONPATH set to the skill root:

    $env:PYTHONPATH = "<repo>/Hedge Edge Business/IDE 1/agents/ANALYTICS/Analytics Agent/.agents/skills/Email-marketing analytics"
    .venv/Scripts/python.exe "Hedge Edge Business/IDE 1/agents/ANALYTICS/Analytics Agent/.agents/skills/Email-marketing analytics/execution/report.py"

The report dynamically fetches all campaigns and templates at runtime — no hardcoded names.
"""

from .campaigns import read_campaign_metrics
from .templates import read_template_metrics
from .leads import read_lead_engagement


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
