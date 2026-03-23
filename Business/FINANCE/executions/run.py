"""Finance task dispatcher — routes --task to the appropriate execution script."""

import argparse
import sys

TASKS = {
    "ib-report": "Aggregate IB commission data across brokers",
    "scrape-vantage": "Scrape Vantage Markets IB portal",
    "scrape-blackbull": "Scrape BlackBull Markets IB portal",
    "revenue-track": "Creem.io subscription MRR tracking",
    "subscription-analyze": "Churn, expansion, contraction analysis",
    "expense-manage": "Expense categorisation and tracking",
    "financial-report": "P&L and cash flow report generation",
    "invoice-generate": "Generate invoices for broker payouts",
}


def main():
    parser = argparse.ArgumentParser(description="Finance Agent task dispatcher")
    parser.add_argument("--task", choices=list(TASKS.keys()), help="Task to run")
    parser.add_argument("--list", action="store_true", help="List available tasks")
    args = parser.parse_args()

    if args.list or not args.task:
        print("Available Finance tasks:")
        for task, desc in TASKS.items():
            print(f"  {task:24s} {desc}")
        return

    print(f"[FINANCE] Running task: {args.task}")
    print(f"  → {TASKS[args.task]}")
    print("  (execution scripts not yet implemented)")


if __name__ == "__main__":
    main()
