#!/usr/bin/env python3
"""
conversion_tracker.py — Beta & Paid Conversion Analytics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pulls user_attribution records from Supabase and reports on recent
beta signups (and eventually paid conversions) with source breakdowns.

Usage:
    python conversion_tracker.py --action recent            # last 24h
    python conversion_tracker.py --action recent --days 7   # last 7 days
    python conversion_tracker.py --action summary           # all-time summary
    python conversion_tracker.py --action by-source         # breakdown by UTM source
    python conversion_tracker.py --action by-method         # breakdown by signup method
"""

import sys
import os
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import log_task
from shared.supabase_client import get_supabase


# ──────────────────────────────────────────────
# Data Access
# ──────────────────────────────────────────────

def _get_all_conversions() -> list[dict]:
    """Pull all user_attribution rows from Supabase."""
    sb = get_supabase(use_service_role=True)
    return sb.table("user_attribution").select("*").order(
        "created_at", desc=True
    ).execute().data or []


def _get_recent_conversions(days: int = 1) -> list[dict]:
    """Pull user_attribution rows from the last N days."""
    sb = get_supabase(use_service_role=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return sb.table("user_attribution").select("*").gte(
        "created_at", cutoff
    ).order("created_at", desc=True).execute().data or []


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_recent(days: int = 1) -> dict:
    """Show conversions from the last N days."""
    rows = _get_recent_conversions(days)
    label = "24 hours" if days == 1 else f"{days} days"

    print("=" * 60)
    print(f"  Conversions — Last {label} (Source: Supabase)")
    print("=" * 60)
    print(f"\n  Total: {len(rows)}")

    if not rows:
        print("  (none)")
        return {"period": label, "count": 0, "conversions": []}

    print()
    for r in rows:
        email = r.get("ref") or "(unknown)"
        source = r.get("utm_source") or "direct"
        medium = r.get("utm_medium") or ""
        method = r.get("signup_method") or ""
        signed = r.get("signed_up_at") or r.get("created_at") or ""
        ts = signed[:19].replace("T", " ") if signed else ""

        channel = f"{source}/{medium}" if medium else source
        print(f"  {ts}  {email:<35s}  {channel:<20s}  {method}")

    # Source breakdown for this period
    by_source: dict[str, int] = defaultdict(int)
    for r in rows:
        by_source[r.get("utm_source") or "direct"] += 1

    print(f"\n  {'─' * 56}")
    print("  Source breakdown:")
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {src}: {cnt}")

    return {"period": label, "count": len(rows), "by_source": dict(by_source)}


def action_summary() -> dict:
    """All-time conversion summary with insights."""
    rows = _get_all_conversions()

    print("=" * 60)
    print("  Conversion Summary \u2014 All Time (Source: Supabase)")
    print("=" * 60)
    print(f"\n  Total conversions: {len(rows)}")

    if not rows:
        return {"total": 0}

    # By source
    by_source: dict[str, int] = defaultdict(int)
    by_method: dict[str, int] = defaultdict(int)
    by_campaign: dict[str, int] = defaultdict(int)
    for r in rows:
        by_source[r.get("utm_source") or "direct"] += 1
        by_method[r.get("signup_method") or "unknown"] += 1
        by_campaign[r.get("utm_campaign") or "none"] += 1

    print("\n  By source:")
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {src}: {cnt}")

    print("\n  By signup method:")
    for m, cnt in sorted(by_method.items(), key=lambda x: -x[1]):
        print(f"    {m}: {cnt}")

    print("\n  By campaign:")
    for c, cnt in sorted(by_campaign.items(), key=lambda x: -x[1]):
        print(f"    {c}: {cnt}")

    # Date range
    earliest = rows[-1].get("created_at", "")[:10]
    latest = rows[0].get("created_at", "")[:10]
    print(f"\n  Date range: {earliest} → {latest}")

    # ── Insights & Improvements ──────────────────────────────
    top_source = max(by_source, key=by_source.get) if by_source else "n/a"
    top_method = max(by_method, key=by_method.get) if by_method else "n/a"
    direct_pct = round(by_source.get("direct", 0) / max(len(rows), 1) * 100, 1)

    print(f"\n{'─' * 60}")
    print("  Insights")
    print(f"  - Top conversion source: {top_source} ({by_source.get(top_source, 0)} conversions)")
    print(f"  - Top signup method: {top_method} ({by_method.get(top_method, 0)})")
    print(f"  - Direct (unattributed) conversions: {direct_pct}% of total")
    if direct_pct > 50:
        print("  - ⚠️  Over half of conversions have no attribution — UTM gaps.")

    print("\n  Improvements")
    if direct_pct > 40:
        print("  - [Attribution gap] Enforce UTM params on all shared links to reduce direct%. → @growth")
    if by_source.get("twitter", 0) > 0:
        twitter_share = round(by_source["twitter"] / max(len(rows), 1) * 100, 1)
        print(f"  - [Twitter converts at {twitter_share}%] Double down on Twitter bio/post links. → @growth")
    if len(by_source) <= 2:
        print(f"  - [Source concentration] Only {len(by_source)} sources converting — diversify acquisition channels. → @strategy")

    return {
        "total": len(rows),
        "by_source": dict(by_source),
        "by_method": dict(by_method),
        "by_campaign": dict(by_campaign),
    }


def action_by_source() -> dict:
    """Breakdown by UTM source with detail."""
    rows = _get_all_conversions()
    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_source[r.get("utm_source") or "direct"].append(r)

    print("=" * 60)
    print("  Conversions by Source")
    print("=" * 60)
    for src, items in sorted(by_source.items(), key=lambda x: -len(x[1])):
        print(f"\n  {src} ({len(items)})")
        for r in items[:10]:
            email = r.get("ref") or "(unknown)"
            ts = (r.get("signed_up_at") or "")[:10]
            print(f"    {ts}  {email}")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")

    return {src: len(items) for src, items in by_source.items()}


def action_by_method() -> dict:
    """Breakdown by signup method."""
    rows = _get_all_conversions()
    by_method: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_method[r.get("signup_method") or "unknown"].append(r)

    print("=" * 60)
    print("  Conversions by Signup Method")
    print("=" * 60)
    for method, items in sorted(by_method.items(), key=lambda x: -len(x[1])):
        print(f"\n  {method} ({len(items)})")
        for r in items[:10]:
            email = r.get("ref") or "(unknown)"
            ts = (r.get("signed_up_at") or "")[:10]
            source = r.get("utm_source") or "direct"
            print(f"    {ts}  {email:<35s}  via {source}")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")

    return {m: len(items) for m, items in by_method.items()}


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Conversion Tracker")
    parser.add_argument("--action", required=True,
                        choices=["recent", "summary", "by-source", "by-method"])
    parser.add_argument("--days", type=int, default=1,
                        help="Lookback period for 'recent' action (default: 1)")
    args = parser.parse_args()

    if args.action == "recent":
        action_recent(args.days)
    elif args.action == "summary":
        action_summary()
    elif args.action == "by-source":
        action_by_source()
    elif args.action == "by-method":
        action_by_method()

    log_task("Analytics", "conversion-track", args.action, "success")


if __name__ == "__main__":
    main()
