#!/usr/bin/env python3
"""
link_tracker.py — UTM Link Tracking via Short.io

Create and analyze UTM-tracked Short.io links for Hedge Edge campaigns.

Usage:
    python link_tracker.py --action create-link --url URL --campaign CAMPAIGN
    python link_tracker.py --action create-link --url URL --campaign CAMPAIGN --source EMAIL --medium email
    python link_tracker.py --action list-links
    python link_tracker.py --action campaign-performance --campaign CAMPAIGN
    python link_tracker.py --action link-stats --url URL
"""

import sys
import os
import argparse

# ── Workspace root (4 levels up) ───────────────────────────────────
_EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_EXEC_DIR, *(['..'] * 4)))
sys.path.insert(0, _WORKSPACE)

from shared.notion_client import log_task
from shared.shortio_client import (
    create_tracked_link,
    get_campaign_performance,
    list_links,
    get_link_stats,
    list_domains,
)

AGENT = "Marketing"


def _check_shortio():
    import os
    if not os.getenv("SHORTIO_API_KEY"):
        print("❌ SHORTIO_API_KEY not set in .env — Short.io integration disabled")
        import sys; sys.exit(1)


def create_link(args):
    """Create a UTM-tracked Short.io link for a campaign."""
    _check_shortio()

    source = getattr(args, "source", None) or "agent"
    medium = getattr(args, "medium", None) or "link"
    content = getattr(args, "content", None) or ""

    print("=" * 60)
    print("  🔗 CREATING UTM-TRACKED LINK")
    print("=" * 60)
    print(f"  URL:      {args.url}")
    print(f"  Campaign: {args.campaign}")
    print(f"  Source:   {source}  Medium: {medium}")

    try:
        result = create_tracked_link(
            original_url=args.url,
            campaign=args.campaign,
            source=source,
            medium=medium,
            content=content if content else None,
        )
        short_url = result.get("shortURL") or result.get("short_url") or result.get("secureShortURL", "")
        print(f"\n  ✅ Short link: {short_url}")
        print(f"  Full UTM URL: {result.get('originalURL', args.url)}")

        log_task(AGENT, f"Created link: {args.campaign}", "Complete", "P3",
                 f"Short: {short_url} | Campaign: {args.campaign} | Source: {source}")
        return result
    except Exception as e:
        print(f"\n  ❌ Failed to create link: {e}")
        log_task(AGENT, f"Link create failed: {args.campaign}", "Error", "P2", str(e))
        sys.exit(1)


def list_all_links(args):
    """List all Short.io links with click counts."""
    _check_shortio()

    print("=" * 60)
    print("  🔗 SHORT.IO TRACKED LINKS")
    print("=" * 60)

    try:
        links = list_links()
    except Exception as e:
        print(f"  ❌ Failed to fetch links: {e}")
        sys.exit(1)

    if not links:
        print("  No links found.")
        return

    total_clicks = 0
    for link in links:
        url = link.get("originalURL") or link.get("original_url") or "?"
        short = link.get("shortURL") or link.get("short_url") or "?"
        clicks = link.get("clicks") or link.get("clicksCount") or 0
        campaign = link.get("tags") or ""
        total_clicks += clicks
        print(f"\n  {short}")
        print(f"    → {url[:70]}")
        if campaign:
            print(f"    Campaign: {campaign}  | Clicks: {clicks}")
        else:
            print(f"    Clicks: {clicks}")

    print(f"\n{'─' * 60}")
    print(f"  Total links: {len(links)} | Total clicks: {total_clicks}")
    log_task(AGENT, "Link list", "Complete", "P3",
             f"{len(links)} links, {total_clicks} total clicks")


def campaign_performance(args):
    """Show aggregate performance for a campaign's tracked links."""
    _check_shortio()

    print("=" * 60)
    print(f"  📊 CAMPAIGN PERFORMANCE: {args.campaign}")
    print("=" * 60)

    try:
        perf = get_campaign_performance(args.campaign)
    except Exception as e:
        print(f"  ❌ Failed to fetch performance: {e}")
        sys.exit(1)

    if not perf:
        print(f"  No data found for campaign: {args.campaign}")
        return

    total_clicks = sum(p.get("clicks", 0) for p in perf) if isinstance(perf, list) else perf.get("totalClicks", 0)
    if isinstance(perf, list):
        for item in perf:
            short = item.get("shortURL") or item.get("short_url") or "?"
            clicks = item.get("clicks", 0)
            print(f"  {short:<45} {clicks:>6} clicks")
        print(f"\n{'─' * 60}")
        print(f"  Total: {total_clicks} clicks across {len(perf)} links")
    else:
        for k, v in perf.items():
            print(f"  {k}: {v}")

    log_task(AGENT, f"Campaign performance: {args.campaign}", "Complete", "P3",
             f"{total_clicks} total clicks")


def link_stats(args):
    """Show click stats for a specific original URL."""
    _check_shortio()

    print("=" * 60)
    print(f"  📈 LINK STATS")
    print("=" * 60)
    print(f"  URL: {args.url}")

    try:
        stats = get_link_stats(args.url)
    except Exception as e:
        print(f"  ❌ Failed to fetch stats: {e}")
        sys.exit(1)

    if not stats:
        print("  No stats found for this URL.")
        return

    if isinstance(stats, dict):
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print(f"  {stats}")

    log_task(AGENT, f"Link stats: {args.url[:60]}", "Complete", "P3", str(stats)[:200])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UTM Link Tracker — Short.io")
    parser.add_argument("--action", required=True,
                        choices=["create-link", "list-links", "campaign-performance", "link-stats"])
    parser.add_argument("--url", help="Original URL to shorten / look up")
    parser.add_argument("--campaign", help="UTM campaign name")
    parser.add_argument("--source", default="agent", help="UTM source (default: agent)")
    parser.add_argument("--medium", default="link", help="UTM medium (default: link)")
    parser.add_argument("--content", default="", help="UTM content (optional)")
    args = parser.parse_args()

    actions = {
        "create-link": create_link,
        "list-links": list_all_links,
        "campaign-performance": campaign_performance,
        "link-stats": link_stats,
    }

    if args.action == "create-link" and not args.url:
        parser.error("--url is required for create-link")
    if args.action == "create-link" and not args.campaign:
        parser.error("--campaign is required for create-link")
    if args.action == "campaign-performance" and not args.campaign:
        parser.error("--campaign is required for campaign-performance")
    if args.action == "link-stats" and not args.url:
        parser.error("--url is required for link-stats")

    actions[args.action](args)
