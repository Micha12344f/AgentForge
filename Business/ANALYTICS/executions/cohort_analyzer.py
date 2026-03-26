#!/usr/bin/env python3
"""
cohort_analyzer.py — Cohort Retention & LTV Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analyzes user cohorts by signup week/month, tracks retention curves,
estimates LTV, and identifies churn patterns.

Usage:
    python cohort_analyzer.py --action retention
    python cohort_analyzer.py --action ltv
    python cohort_analyzer.py --action churn
    python cohort_analyzer.py --action summary
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from collections import defaultdict

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 3)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.notion_client import log_task
from shared.supabase_client import get_supabase


def _get_profiles() -> list[dict]:
    """Pull user profiles from Supabase."""
    sb = get_supabase(use_service_role=True)
    result = sb.table("profiles").select("id,created_at,last_active_at,plan").execute()
    return result.data or []


def retention_analysis() -> dict:
    """Analyze retention by signup cohort (weekly)."""
    print("=" * 60)
    print("  Cohort Retention Analysis")
    print("=" * 60)

    profiles = _get_profiles()
    if not profiles:
        print("  No user data — retention analysis requires active users.")
        return {"cohorts": {}, "note": "no data"}

    now = datetime.now(timezone.utc)
    cohorts: dict[str, dict] = defaultdict(lambda: {"total": 0, "active_7d": 0, "active_30d": 0})

    for p in profiles:
        created = p.get("created_at", "")
        if not created:
            continue
        # Group by ISO week
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        week_key = dt.strftime("%Y-W%W")
        cohorts[week_key]["total"] += 1

        last_active = p.get("last_active_at")
        if last_active:
            la = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
            if (now - la).days <= 7:
                cohorts[week_key]["active_7d"] += 1
            if (now - la).days <= 30:
                cohorts[week_key]["active_30d"] += 1

    print(f"  Cohorts: {len(cohorts)}")
    for week, data in sorted(cohorts.items()):
        r7 = (data["active_7d"] / data["total"] * 100) if data["total"] else 0
        r30 = (data["active_30d"] / data["total"] * 100) if data["total"] else 0
        print(f"    {week}: {data['total']} users | 7d: {r7:.0f}% | 30d: {r30:.0f}%")

    return {"cohorts": dict(cohorts)}


def ltv_estimation() -> dict:
    """Estimate LTV based on current pricing and retention."""
    print("  [LTV Estimation]")
    profiles = _get_profiles()
    if not profiles:
        print("  No data for LTV — need paying customers.")
        return {"ltv": 0, "note": "pre-revenue"}

    # Placeholder: assume $29/mo average and estimate from retention
    avg_price = 29.0
    # With 0 churn data, use default 12-month estimate
    estimated_ltv = avg_price * 12
    print(f"  Estimated LTV (placeholder): ${estimated_ltv:.2f}")
    print("  ⚠️  Requires real subscription data for accurate calculation.")
    return {"ltv": estimated_ltv, "avg_price": avg_price}


def churn_analysis() -> dict:
    """Analyze churn patterns."""
    print("  [Churn Analysis]")
    profiles = _get_profiles()
    now = datetime.now(timezone.utc)

    active = 0
    churned = 0
    for p in profiles:
        last_active = p.get("last_active_at")
        if last_active:
            la = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
            if (now - la).days > 30:
                churned += 1
            else:
                active += 1
        else:
            churned += 1

    total = active + churned
    rate = (churned / total * 100) if total else 0
    print(f"  Total users: {total} | Active: {active} | Churned (30d): {churned} ({rate:.1f}%)")
    return {"active": active, "churned": churned, "churn_rate": round(rate, 1)}


def main():
    parser = argparse.ArgumentParser(description="Cohort Analyzer")
    parser.add_argument("--action", required=True,
                        choices=["retention", "ltv", "churn", "summary"])
    args = parser.parse_args()

    if args.action == "retention":
        retention_analysis()
    elif args.action == "ltv":
        ltv_estimation()
    elif args.action == "churn":
        churn_analysis()
    elif args.action == "summary":
        retention_analysis()
        print()
        ltv_estimation()
        print()
        churn_analysis()

    log_task("Analytics", "cohort", args.action, "success")


if __name__ == "__main__":
    main()
