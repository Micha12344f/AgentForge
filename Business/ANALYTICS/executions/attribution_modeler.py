#!/usr/bin/env python3
"""
attribution_modeler.py — Marketing Attribution Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-model marketing attribution (first-touch, last-touch, linear)
using Supabase user_attribution data and UTM parameters.

Usage:
    python attribution_modeler.py --action first-touch
    python attribution_modeler.py --action last-touch
    python attribution_modeler.py --action linear
    python attribution_modeler.py --action summary
"""

import sys
import os
import argparse

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timezone
from collections import defaultdict

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import log_task
from shared.supabase_client import get_supabase


def _get_attribution_data() -> list[dict]:
    """Pull user attribution records from Supabase."""
    sb = get_supabase(use_service_role=True)
    result = sb.table("user_attribution").select("*").execute()
    return result.data or []


def first_touch_attribution() -> dict:
    """Attribute conversions to the first touchpoint (utm_source)."""
    print("  [First-Touch Attribution]")
    rows = _get_attribution_data()
    by_source: dict[str, int] = defaultdict(int)
    for r in rows:
        source = r.get("utm_source") or "direct"
        by_source[source] += 1

    print(f"  Total attributed users: {len(rows)}")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {source}: {count}")
    return {"model": "first-touch", "by_source": dict(by_source), "total": len(rows)}


def last_touch_attribution() -> dict:
    """Attribute conversions to the last touchpoint (utm_medium + source)."""
    print("  [Last-Touch Attribution]")
    rows = _get_attribution_data()
    by_medium: dict[str, int] = defaultdict(int)
    for r in rows:
        medium = r.get("utm_medium") or "none"
        by_medium[medium] += 1

    print(f"  Total attributed users: {len(rows)}")
    for medium, count in sorted(by_medium.items(), key=lambda x: -x[1]):
        print(f"    {medium}: {count}")
    return {"model": "last-touch", "by_medium": dict(by_medium), "total": len(rows)}


def linear_attribution() -> dict:
    """Equal credit across all touchpoints."""
    print("  [Linear Attribution]")
    rows = _get_attribution_data()
    channels: dict[str, float] = defaultdict(float)
    for r in rows:
        touches = []
        if r.get("utm_source"):
            touches.append(r["utm_source"])
        if r.get("utm_medium"):
            touches.append(r["utm_medium"])
        if r.get("utm_campaign"):
            touches.append(r["utm_campaign"])
        if not touches:
            touches = ["direct"]
        credit = 1.0 / len(touches)
        for t in touches:
            channels[t] += credit

    print(f"  Total attributed users: {len(rows)}")
    for ch, credit in sorted(channels.items(), key=lambda x: -x[1]):
        print(f"    {ch}: {credit:.1f}")
    return {"model": "linear", "channels": {k: round(v, 2) for k, v in channels.items()}}


def summary() -> None:
    """Run all attribution models and print comparison."""
    print("=" * 60)
    print("  Attribution Model Comparison")
    print("=" * 60)
    first_touch_attribution()
    print()
    last_touch_attribution()
    print()
    linear_attribution()


def main():
    parser = argparse.ArgumentParser(description="Attribution Modeler")
    parser.add_argument("--action", required=True,
                        choices=["first-touch", "last-touch", "linear", "summary"])
    args = parser.parse_args()

    if args.action == "first-touch":
        first_touch_attribution()
    elif args.action == "last-touch":
        last_touch_attribution()
    elif args.action == "linear":
        linear_attribution()
    elif args.action == "summary":
        summary()

    log_task("Analytics", f"attribution/{args.action}", "Complete", "P2")


if __name__ == "__main__":
    main()
