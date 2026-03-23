#!/usr/bin/env python3
"""Landing-page optimizer helper for the Marketing agent -- landing-page task."""

from __future__ import annotations

import argparse
import os
import sys


def _find_repo_root():
    """Walk up to the Orchestrator root (has shared/ AND Business/)."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if (os.path.isfile(os.path.join(d, "shared", "notion_client.py"))
                and os.path.isdir(os.path.join(d, "Business"))):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Could not locate the Orchestrator repo root")


_REPO = _find_repo_root()
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from dotenv import load_dotenv

load_dotenv(os.path.join(_REPO, ".env"))

from shared.notion_client import query_db


def _dur(seconds):
    m, s = divmod(int(seconds or 0), 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _load_ga4():
    from shared import google_analytics_client as ga4
    return ga4


def _ga4_landing_pages():
    ga4 = _load_ga4()
    rows = ga4.run_report(
        dimensions=["landingPage"],
        metrics=["sessions", "totalUsers", "bounceRate",
                 "averageSessionDuration", "conversions"],
        start_date="7daysAgo", end_date="yesterday",
        order_bys=[{"metric": {"metricName": "sessions"}, "desc": True}],
        limit=15,
    )
    # Filter junk
    clean = [r for r in rows
             if r.get("landingPage", "") not in {"(not set)", "/cart"}
             and "}}" not in r.get("landingPage", "")
             and not r.get("landingPage", "").startswith("/api/")]
    return clean[:10]


def cmd_list_tests():
    print("=" * 60)
    print("  LANDING PAGE STATUS")
    print("=" * 60)

    # Try Notion DB first
    try:
        rows = query_db("landing_page_tests")
        if rows:
            print(f"\n  A/B Tests in Notion: {len(rows)}")
            for r in rows:
                name = r.get("Name") or r.get("Test") or "Untitled"
                status = r.get("Status") or "Unknown"
                print(f"    {name} -- {status}")
            print()
    except Exception:
        print("  (landing_page_tests DB not available)\n")

    # GA4 fallback -- always useful
    print("  GA4 Landing Page Performance (last 7 days):")
    try:
        pages = _ga4_landing_pages()
        for p in pages:
            lp = p.get("landingPage", "?")
            br = p.get("bounceRate", 0)
            print(f"    {lp:<25} {p.get('sessions',0):>4} sess  "
                  f"bounce {br:.0%}  dur {_dur(p.get('averageSessionDuration',0))}  "
                  f"conv {p.get('conversions',0)}")
    except Exception as e:
        print(f"    GA4 unavailable: {e}")
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--action", required=True, choices=["list-tests", "status"])
    args = p.parse_args()
    cmd_list_tests()


if __name__ == "__main__":
    main()