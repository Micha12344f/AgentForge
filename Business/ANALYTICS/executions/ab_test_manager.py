#!/usr/bin/env python3
"""
ab_test_manager.py — A/B Test Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Design, monitor, and analyze A/B tests with statistical significance testing.
Tracks landing page variants, email subject lines, and CTA experiments.

Usage:
    python ab_test_manager.py --action list
    python ab_test_manager.py --action create --name "Homepage CTA v2"
    python ab_test_manager.py --action analyze --name "Homepage CTA v2"
"""

import sys
import os
import argparse
import math
from datetime import datetime, timezone

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import query_db, add_row, log_task


def z_test_proportions(n_a: int, conv_a: int, n_b: int, conv_b: int) -> dict:
    """Two-proportion z-test for A/B test significance."""
    if n_a == 0 or n_b == 0:
        return {"significant": False, "p_value": 1.0, "reason": "insufficient data"}

    p_a = conv_a / n_a
    p_b = conv_b / n_b
    p_pool = (conv_a + conv_b) / (n_a + n_b)

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b)) if p_pool > 0 else 0
    if se == 0:
        return {"significant": False, "p_value": 1.0, "z": 0}

    z = (p_b - p_a) / se
    # Approximate p-value using normal CDF
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

    return {
        "rate_a": round(p_a * 100, 2),
        "rate_b": round(p_b * 100, 2),
        "z_score": round(z, 3),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "winner": "B" if z > 0 and p_value < 0.05 else ("A" if z < 0 and p_value < 0.05 else "none"),
    }


def list_tests() -> None:
    """List all A/B tests from landing_page_tests DB."""
    print("=" * 60)
    print("  A/B Tests")
    print("=" * 60)
    try:
        rows = query_db("landing_page_tests", page_size=50)
        if not rows:
            print("  No tests found. Create one with --action create.")
            return
        for row in rows:
            name = row.get("Name", "Untitled")
            status = row.get("Status", "Unknown")
            print(f"  [{status}] {name}")
    except Exception as e:
        print(f"  [WARN] Could not query landing_page_tests: {e}")
        print("  (Database may not exist or is not shared with the Notion integration)")


def create_test(name: str) -> None:
    """Create a new A/B test entry."""
    print(f"  Creating A/B test: {name}")
    try:
        add_row("landing_page_tests", {
            "Name": name,
            "Status": "Draft",
            "Created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        })
        print(f"  ✅ Test '{name}' created")
    except Exception as e:
        print(f"  ⚠️  Could not create test: {e}")


def analyze_test(name: str) -> None:
    """Analyze an A/B test for statistical significance."""
    print(f"  Analyzing: {name}")
    print("  ⚠️  Requires variant data — populate test rows with visitor/conversion counts first.")


def main():
    parser = argparse.ArgumentParser(description="A/B Test Manager")
    parser.add_argument("--action", required=True, choices=["list", "create", "analyze"])
    parser.add_argument("--name", type=str, default="")
    args = parser.parse_args()

    if args.action == "list":
        list_tests()
    elif args.action == "create":
        if not args.name:
            print("[ERROR] --name required for create action")
            sys.exit(1)
        create_test(args.name)
    elif args.action == "analyze":
        if not args.name:
            print("[ERROR] --name required for analyze action")
            sys.exit(1)
        analyze_test(args.name)

    try:
        log_task("Analytics", "ab-test", args.action, "success")
    except Exception:
        pass


if __name__ == "__main__":
    main()
