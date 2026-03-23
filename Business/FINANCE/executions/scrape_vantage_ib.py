#!/usr/bin/env python3
"""
scrape_vantage_ib.py — Vantage Markets IB Commission Scraper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scrapes the Vantage Markets IB portal for commission data
and writes results to the Notion ib_commissions database.

Usage:
    python scrape_vantage_ib.py --action pull
    python scrape_vantage_ib.py --action summary
"""

import sys
import os
import argparse
from datetime import datetime, timezone

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(_AGENT_DIR)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import add_row, query_db, log_task


def pull_commissions() -> dict:
    """Pull latest commission data from Vantage IB portal."""
    print("[Vantage IB] Pulling commission data ...")
    # TODO: Implement actual scraping once IB portal credentials are available
    # For now, return empty result
    print("[Vantage IB] ⚠️  Not yet implemented — awaiting IB portal access")
    return {"broker": "Vantage Markets", "commissions": [], "total": 0.0}


def show_summary() -> None:
    """Show summary of stored Vantage IB commissions."""
    print("[Vantage IB] Commission Summary")
    try:
        rows = query_db("ib_commissions", filter={
            "property": "Broker",
            "select": {"equals": "Vantage Markets"},
        })
        total = sum(
            r.get("Commission", 0) for r in rows if isinstance(r.get("Commission"), (int, float))
        )
        print(f"  Records: {len(rows)}")
        print(f"  Total Commission: ${total:,.2f}")
    except Exception as e:
        print(f"  ⚠️  Could not query ib_commissions: {e}")


def main():
    parser = argparse.ArgumentParser(description="Vantage Markets IB Scraper")
    parser.add_argument("--action", required=True, choices=["pull", "summary"])
    args = parser.parse_args()

    if args.action == "pull":
        result = pull_commissions()
        log_task("Finance", "scrape-vantage", "pull", "success",
                 notes=f"Total: ${result['total']:.2f}")
    elif args.action == "summary":
        show_summary()


if __name__ == "__main__":
    main()
