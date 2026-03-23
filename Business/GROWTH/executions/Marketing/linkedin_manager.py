#!/usr/bin/env python3
"""
linkedin_manager.py — Content Engine Agent LinkedIn Management

Manage LinkedIn content, thought leadership posts, and professional engagement
for Hedge Edge brand authority building.

Usage:
    python linkedin_manager.py --action plan-post --content-type article --topic "Why Every Funded Trader Needs a Hedging Strategy" --scheduled-date 2026-02-24 --cta "Try Hedge Edge free"
    python linkedin_manager.py --action queue
    python linkedin_manager.py --action record-engagement --post-title "Why Every Funded..." --impressions 2400 --reactions 86 --comments 12 --shares 8 --clicks 145
    python linkedin_manager.py --action performance-report
    python linkedin_manager.py --action thought-leadership
"""

import sys, os, argparse, json
from datetime import datetime, timezone

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

sys.path.insert(0, _find_ws_root())
from shared.notion_client import add_row, query_db, update_row, log_task

CONTENT_TYPES = ["text", "article", "carousel", "poll", "video"]

THOUGHT_LEADERSHIP_ANGLES = [
    {
        "angle": "The Hidden Cost of Prop Firm Resets",
        "hook": "Most traders calculate the challenge fee. Few calculate the emotional cost of resetting 3× in a row.",
        "format": "text",
        "cta": "We built Hedge Edge to end the reset cycle.",
    },
    {
        "angle": "Hedging Is Not Cheating — It's Risk Management",
        "hook": "Banks hedge. Funds hedge. Institutions hedge. But somehow retail traders think it's 'cheating'?",
        "format": "carousel",
        "cta": "Learn how institutional hedging works for retail traders.",
    },
    {
        "angle": "I Analyzed 500 Prop Firm Failures. Here's the Pattern.",
        "hook": "It's not bad entries. It's not bad strategies. It's inadequate risk management during drawdown.",
        "format": "text",
        "cta": "Protect your funded account with automated hedging.",
    },
    {
        "angle": "The $29/Month Insurance Policy for Your $100K Account",
        "hook": "You wouldn't drive without insurance. Why trade a funded account without drawdown protection?",
        "format": "text",
        "cta": "Hedge Edge Challenge Shield — $29/mo.",
    },
    {
        "angle": "MT5 Has a Superpower Most Traders Ignore",
        "hook": "MT5 allows hedging on the same instrument. MT4 doesn't. This single feature changes everything for funded traders.",
        "format": "article",
        "cta": "Read our MT5 hedging setup guide.",
    },
    {
        "angle": "Poll: What Caused Your Last Prop Firm Failure?",
        "hook": "Be honest — what killed your last funded account?",
        "format": "poll",
        "options": ["Drawdown limit", "Daily loss limit", "Time limit", "Emotional trading"],
    },
    {
        "angle": "From 3 Failed Challenges to Funded in 30 Days",
        "hook": "A trader shares how one strategy change — adding automated hedging — transformed their results.",
        "format": "article",
        "cta": "Read the full case study.",
    },
]


def plan_post(args):
    """Plan a LinkedIn post and add to content calendar."""
    if args.content_type not in CONTENT_TYPES:
        print(f"❌ Invalid type '{args.content_type}'. Choose from: {', '.join(CONTENT_TYPES)}")
        return
    row = {
        "Title":        args.topic,
        "Platform":     "LinkedIn",
        "Format":       args.content_type.capitalize(),
        "Status":       "Scheduled",
        "Publish Date": args.scheduled_date or "",
        "Topic":        args.topic,
        "CTA":          args.cta or "",
    }
    add_row("content_calendar", row)
    print("=" * 65)
    print("  🔗 LINKEDIN POST PLANNED")
    print("=" * 65)
    print(f"\n  Topic:     {args.topic}")
    print(f"  Type:      {args.content_type}")
    print(f"  Scheduled: {args.scheduled_date or 'TBD'}")
    if args.cta:
        print(f"  CTA:       {args.cta}")
    print(f"  Status:    Scheduled")
    print(f"\n{'─' * 65}")
    log_task("Content Engine", f"LI post planned: {args.topic[:50]}", "Complete", "P2",
             f"Type={args.content_type}, Date={args.scheduled_date or 'TBD'}")


def queue(args):
    """Show upcoming LinkedIn posting queue."""
    try:
        items = query_db("content_calendar", filter={
            "and": [
                {"property": "Platform", "select": {"equals": "LinkedIn"}},
                {"property": "Status", "select": {"does_not_equal": "Published"}},
            ]
        })
    except Exception:
        all_items = query_db("content_calendar")
        items = [i for i in all_items if i.get("Platform") == "LinkedIn" and i.get("Status") != "Published"]
    print("=" * 65)
    print("  📋 LINKEDIN POSTING QUEUE")
    print("=" * 65)
    if not items:
        print("\n  No upcoming LinkedIn posts in queue.")
        print("  Use --action plan-post to schedule content.")
        return
    items.sort(key=lambda x: x.get("Publish Date", "9999-12-31"))
    for i, item in enumerate(items, 1):
        title = item.get("Title", "Untitled")
        date = item.get("Publish Date", "TBD")
        fmt = item.get("Format", "?")
        status = item.get("Status", "?")
        cta = item.get("CTA", "")
        print(f"\n  {i}. [{fmt}] {title}")
        print(f"     Date: {date} | Status: {status}")
        if cta:
            print(f"     CTA: {cta}")
    print(f"\n{'─' * 65}")
    print(f"  Total queued: {len(items)} posts")
    log_task("Content Engine", "LI queue viewed", "Complete", "P3",
             f"{len(items)} posts in queue")


def record_engagement(args):
    """Record engagement metrics for a LinkedIn post."""
    try:
        items = query_db("content_calendar", filter={
            "and": [
                {"property": "Platform", "select": {"equals": "LinkedIn"}},
                {"property": "Title", "title": {"contains": args.post_title}},
            ]
        })
    except Exception:
        all_items = query_db("content_calendar")
        items = [i for i in all_items if i.get("Platform") == "LinkedIn" and args.post_title in (i.get("Title") or "")]
    if not items:
        print(f"❌ LinkedIn post not found: {args.post_title}")
        return
    item = items[0]

    engagement_total = (args.reactions or 0) + (args.comments or 0) + (args.shares or 0) + (args.clicks or 0)
    engagement_rate = (engagement_total / args.impressions * 100) if args.impressions else 0

    updates = {}
    if args.impressions: updates["Impressions"] = args.impressions
    if args.reactions:   updates["Reactions"] = args.reactions
    if args.comments:    updates["Comments"] = args.comments
    if args.shares:      updates["Shares"] = args.shares
    if args.clicks:      updates["Clicks"] = args.clicks
    updates["Engagement Rate"] = round(engagement_rate, 2)
    updates["Status"] = "Published"

    update_row(item["_id"], "content_calendar", updates)
    print("=" * 65)
    print("  📊 LINKEDIN ENGAGEMENT RECORDED")
    print("=" * 65)
    print(f"\n  Post:        {item.get('Title', '?')}")
    if args.impressions: print(f"  Impressions: {args.impressions:,}")
    if args.reactions:   print(f"  Reactions:   {args.reactions:,}")
    if args.comments:    print(f"  Comments:    {args.comments:,}")
    if args.shares:      print(f"  Shares:      {args.shares:,}")
    if args.clicks:      print(f"  Clicks:      {args.clicks:,}")
    print(f"  Eng. Rate:   {engagement_rate:.2f}%")
    print(f"\n{'─' * 65}")
    log_task("Content Engine", f"LI engagement: {args.post_title[:40]}", "Complete", "P3",
             f"Impr={args.impressions or 0}, ER={engagement_rate:.2f}%")


def performance_report(args):
    """LinkedIn content performance report."""
    try:
        items = query_db("content_calendar", filter={
            "property": "Platform", "select": {"equals": "LinkedIn"}
        })
    except Exception:
        all_items = query_db("content_calendar")
        items = [i for i in all_items if i.get("Platform") == "LinkedIn"]
    print("=" * 65)
    print("  📈 LINKEDIN PERFORMANCE REPORT")
    print("=" * 65)
    if not items:
        print("\n  No LinkedIn content tracked yet.")
        return

    total = len(items)
    published = [i for i in items if i.get("Status") == "Published"]
    total_impressions = sum(int(i.get("Impressions", 0) or 0) for i in items)
    total_reactions = sum(int(i.get("Reactions", 0) or 0) for i in items)
    total_comments = sum(int(i.get("Comments", 0) or 0) for i in items)
    total_clicks = sum(int(i.get("Clicks", 0) or 0) for i in items)
    total_shares = sum(int(i.get("Shares", 0) or 0) for i in items)

    print(f"\n  Total Posts:      {total}")
    print(f"  Published:        {len(published)}")
    print(f"\n  Engagement Totals:")
    print(f"    Impressions:    {total_impressions:,}")
    print(f"    Reactions:      {total_reactions:,}")
    print(f"    Comments:       {total_comments:,}")
    print(f"    Clicks:         {total_clicks:,}")
    print(f"    Shares:         {total_shares:,}")

    # Top posts by engagement
    scored = [(i, int(i.get("Reactions", 0) or 0) + int(i.get("Comments", 0) or 0) * 3 + int(i.get("Shares", 0) or 0) * 5) for i in items]
    scored.sort(key=lambda x: -x[1])
    top = [s for s in scored if s[1] > 0][:5]
    if top:
        print(f"\n  Top Posts (weighted engagement score):")
        for i, (item, score) in enumerate(top, 1):
            print(f"    {i}. {item.get('Title', '?')[:50]}")
            print(f"       Score: {score} | Type: {item.get('Format', '?')}")

    # Content type comparison
    by_type = {}
    for item in items:
        fmt = item.get("Format", "Unknown")
        impr = int(item.get("Impressions", 0) or 0)
        eng = int(item.get("Reactions", 0) or 0) + int(item.get("Comments", 0) or 0)
        by_type.setdefault(fmt, {"count": 0, "impressions": 0, "engagement": 0})
        by_type[fmt]["count"] += 1
        by_type[fmt]["impressions"] += impr
        by_type[fmt]["engagement"] += eng
    if by_type:
        print(f"\n  Content Type Comparison:")
        for fmt, stats in sorted(by_type.items(), key=lambda x: -x[1]["engagement"]):
            avg_eng = stats["engagement"] / stats["count"] if stats["count"] else 0
            print(f"    {fmt:<12} {stats['count']} posts | {stats['impressions']:,} impr | avg eng: {avg_eng:,.1f}")

    print(f"\n  LinkedIn Best Practices (B2B / Fintech):")
    print(f"    • Post Tue-Thu 8-10 AM for max reach")
    print(f"    • Text posts outperform links for engagement")
    print(f"    • Carousels drive highest save rates")
    print(f"    • Comment within first 30 min to boost algorithm")
    print(f"\n{'─' * 65}")
    log_task("Content Engine", "LI performance report", "Complete", "P3",
             f"{total} posts, {total_impressions:,} impressions")


def thought_leadership(args):
    """Generate thought leadership content angles for LinkedIn."""
    print("=" * 65)
    print("  🧠 THOUGHT LEADERSHIP — CONTENT ANGLES")
    print("=" * 65)
    print(f"\n  Focus: Hedging expertise × Prop-firm industry × Trading technology\n")

    for i, tl in enumerate(THOUGHT_LEADERSHIP_ANGLES, 1):
        print(f"  {i}. {tl['angle']}")
        print(f"     Format: {tl['format'].upper()}")
        print(f"     Hook:   \"{tl['hook']}\"")
        if "options" in tl:
            print(f"     Options: {' / '.join(tl['options'])}")
        if "cta" in tl:
            print(f"     CTA:    {tl['cta']}")
        print()

    print(f"  Content Pillars for LinkedIn Authority:")
    print(f"    1. Risk Management Expertise — Position as the hedging authority")
    print(f"    2. Prop Firm Industry Analysis — Data-driven insights traders trust")
    print(f"    3. Product Thought Leadership — How Hedge Edge solves real problems")
    print(f"    4. Trader Success Stories — Social proof through case studies")
    print(f"    5. Market Commentary — Timely takes on volatility events")
    print(f"\n{'─' * 65}")
    log_task("Content Engine", "LI thought leadership generated", "Complete", "P3",
             f"{len(THOUGHT_LEADERSHIP_ANGLES)} angles across 5 pillars")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Manager — Plan, track, and grow LI presence")
    parser.add_argument("--action", required=True,
                        choices=["plan-post", "queue", "record-engagement", "performance-report", "thought-leadership"])
    parser.add_argument("--content-type", default="text", dest="content_type", choices=CONTENT_TYPES)
    parser.add_argument("--topic", default="")
    parser.add_argument("--scheduled-date", default="", dest="scheduled_date")
    parser.add_argument("--cta", default="")
    parser.add_argument("--post-title", default="", dest="post_title")
    parser.add_argument("--impressions", type=int, default=0)
    parser.add_argument("--reactions", type=int, default=0)
    parser.add_argument("--comments", type=int, default=0)
    parser.add_argument("--shares", type=int, default=0)
    parser.add_argument("--clicks", type=int, default=0)
    args = parser.parse_args()
    {"plan-post": plan_post, "queue": queue, "record-engagement": record_engagement,
     "performance-report": performance_report, "thought-leadership": thought_leadership}[args.action](args)
