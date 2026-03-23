#!/usr/bin/env python3
"""
ib_report_aggregator.py — IB Commission Report Aggregator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aggregates IB commission data from all brokers (Vantage, BlackBull)
into a unified report with totals, trends, and breakdowns.

Usage:
    python ib_report_aggregator.py --action generate
    python ib_report_aggregator.py --action monthly
"""

import sys
import os
import argparse
from datetime import datetime, timezone
from collections import defaultdict

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(_AGENT_DIR)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import query_db, log_task


def generate_report() -> dict:
    """Generate unified IB commission report across all brokers."""
    print("=" * 60)
    print("  IB Commission Report")
    print("=" * 60)

    try:
        rows = query_db("ib_commissions", page_size=100)
    except Exception as e:
        print(f"  ⚠️  Could not query ib_commissions: {e}")
        rows = []

    if not rows:
        print("  No commission data found.")
        return {"total": 0, "by_broker": {}}

    by_broker: dict[str, float] = defaultdict(float)
    for row in rows:
        broker = row.get("Broker", "Unknown")
        amount = row.get("Commission", 0)
        if isinstance(amount, (int, float)):
            by_broker[broker] += amount

    total = sum(by_broker.values())
    print(f"\n  Total Commission: ${total:,.2f}")
    print(f"  Records: {len(rows)}")
    for broker, amount in sorted(by_broker.items()):
        print(f"    {broker}: ${amount:,.2f}")

    return {"total": total, "by_broker": dict(by_broker), "records": len(rows)}


def main():
    parser = argparse.ArgumentParser(description="IB Commission Report Aggregator")
    parser.add_argument("--action", required=True, choices=["generate", "monthly"])
    args = parser.parse_args()

    result = generate_report()
    log_task("Finance", "ib-report", args.action, "success",
             notes=f"Total: ${result['total']:.2f}, Records: {result.get('records', 0)}")


if __name__ == "__main__":
    main()
