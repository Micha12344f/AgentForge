#!/usr/bin/env python3
"""
Chat Analytics — Supabase support_chat_logs queries
====================================================
Provides analytics functions for the Hedge Edge support bot conversation logs.

Usage:
    from chat_analytics import quick_stats, trending_questions, failed_answers
    quick_stats(hours=24)
    trending_questions(days=7)
    failed_answers(days=7)
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

sys.path.insert(0, _find_ws_root())

from dotenv import load_dotenv
load_dotenv(os.path.join(_find_ws_root(), ".env"))

from shared.supabase_client import get_supabase


def _query_logs(hours: int = 24, limit: int = 1000) -> list[dict]:
    """Fetch recent chat logs from Supabase."""
    sb = get_supabase(use_service_role=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return (
        sb.table("support_chat_logs")
        .select("*")
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )


def quick_stats(hours: int = 24) -> dict:
    """
    Quick overview of support bot usage.

    Returns dict: total, by_source, avg_ms, fallback_rate, flagged_count
    """
    rows = _query_logs(hours=hours)
    total = len(rows)
    if total == 0:
        print(f"No conversations in the last {hours}h.")
        return {"total": 0}

    by_source = Counter(r["source"] for r in rows)
    times = [r["response_ms"] for r in rows if r.get("response_ms")]
    avg_ms = sum(times) / len(times) if times else 0
    fallbacks = sum(1 for r in rows if r.get("fallback"))
    flagged = sum(1 for r in rows if r.get("flagged"))

    result = {
        "total": total,
        "by_source": dict(by_source),
        "avg_response_ms": round(avg_ms),
        "fallback_rate": round(fallbacks / total * 100, 1),
        "fallback_count": fallbacks,
        "flagged_count": flagged,
    }

    print(f"=== Support Bot Stats (last {hours}h) ===")
    print(f"Total conversations: {total}")
    for src, cnt in by_source.items():
        print(f"  {src}: {cnt}")
    print(f"Avg response time:  {avg_ms:.0f}ms")
    print(f"Fallback rate:      {fallbacks}/{total} ({result['fallback_rate']}%)")
    print(f"Flagged messages:   {flagged}")
    return result


def trending_questions(days: int = 7, top_n: int = 15) -> list[tuple]:
    """
    Find the most common question topics.

    Groups by first 60 chars of user_message (lowercased).
    Returns list of (prefix, count) tuples.
    """
    rows = _query_logs(hours=days * 24, limit=2000)
    if not rows:
        print("No data.")
        return []

    prefixes = Counter()
    for r in rows:
        msg = r.get("user_message", "").strip().lower()[:60]
        if msg:
            prefixes[msg] += 1

    top = prefixes.most_common(top_n)
    print(f"=== Trending Questions (last {days}d, top {top_n}) ===")
    for i, (q, cnt) in enumerate(top, 1):
        print(f"  {i:2d}. [{cnt}x] {q}")
    return top


def failed_answers(days: int = 7, limit: int = 50) -> list[dict]:
    """
    Find answers where the bot fell back to 70B (uncertain 8B response).

    These indicate doc gaps — the 8B model couldn't confidently answer.
    """
    sb = get_supabase(use_service_role=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = (
        sb.table("support_chat_logs")
        .select("session_id, user_message, bot_reply, model_used, created_at")
        .eq("fallback", True)
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )

    print(f"=== Fallback/Uncertain Answers (last {days}d) ===")
    if not rows:
        print("None! All answers were confident.")
        return []

    for i, r in enumerate(rows, 1):
        ts = r["created_at"][:16].replace("T", " ")
        print(f"\n  {i}. [{ts}] session={r['session_id'][:8]}...")
        print(f"     Q: {r['user_message'][:100]}")
        print(f"     A: {r['bot_reply'][:100]}...")
    return rows


def replay_session(session_id: str) -> list[dict]:
    """
    Replay a full conversation session in chronological order.

    Args:
        session_id: The session UUID (full or partial prefix).
    """
    sb = get_supabase(use_service_role=True)
    q = sb.table("support_chat_logs").select("*").order("created_at")

    if len(session_id) < 36:
        # Partial match — use ilike
        rows = q.ilike("session_id", f"{session_id}%").limit(100).execute().data or []
    else:
        rows = q.eq("session_id", session_id).limit(100).execute().data or []

    print(f"=== Session Replay: {session_id[:12]}... ({len(rows)} exchanges) ===")
    for r in rows:
        ts = r["created_at"][:19].replace("T", " ")
        model = r.get("model_used", "?")
        ms = r.get("response_ms", 0)
        fb = " [FALLBACK]" if r.get("fallback") else ""
        print(f"\n  [{ts}] {model} {ms}ms{fb}")
        print(f"  USER: {r['user_message']}")
        print(f"  BOT:  {r['bot_reply'][:200]}")
    return rows


def model_performance(days: int = 7) -> dict:
    """
    Compare performance between 8B and 70B models.

    Returns dict with per-model stats.
    """
    rows = _query_logs(hours=days * 24, limit=5000)
    if not rows:
        print("No data.")
        return {}

    models = {}
    for r in rows:
        m = r.get("model_used", "unknown")
        if m not in models:
            models[m] = {"count": 0, "total_ms": 0, "fallback": 0}
        models[m]["count"] += 1
        models[m]["total_ms"] += r.get("response_ms", 0)
        if r.get("fallback"):
            models[m]["fallback"] += 1

    print(f"=== Model Performance (last {days}d) ===")
    for m, s in sorted(models.items()):
        avg = s["total_ms"] / s["count"] if s["count"] else 0
        fb_pct = s["fallback"] / s["count"] * 100 if s["count"] else 0
        print(f"  {m}:")
        print(f"    Count: {s['count']}, Avg: {avg:.0f}ms, Fallback: {fb_pct:.1f}%")
        models[m]["avg_ms"] = round(avg)
        models[m]["fallback_pct"] = round(fb_pct, 1)

    return models


def export_logs(days: int = 30, fmt: str = "csv") -> str:
    """
    Export chat logs to a file.

    Args:
        days: How many days of data to export.
        fmt: 'csv' or 'json'.

    Returns:
        Path to the exported file.
    """
    import json as _json
    rows = _query_logs(hours=days * 24, limit=10000)
    if not rows:
        print("No data to export.")
        return ""

    out_dir = os.path.join(_ws_root, "exports")
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        path = os.path.join(out_dir, f"chat_logs_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(rows, f, indent=2, default=str)
    else:
        import csv
        path = os.path.join(out_dir, f"chat_logs_{ts}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Exported {len(rows)} rows to {path}")
    return path


# ── CLI ──
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Support Chat Analytics")
    p.add_argument("command", choices=["stats", "trending", "failed", "replay", "models", "export"])
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--session", type=str, default="")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--format", type=str, default="csv")
    args = p.parse_args()

    if args.command == "stats":
        quick_stats(hours=args.hours)
    elif args.command == "trending":
        trending_questions(days=args.days, top_n=args.top)
    elif args.command == "failed":
        failed_answers(days=args.days)
    elif args.command == "replay":
        if not args.session:
            print("--session required")
        else:
            replay_session(args.session)
    elif args.command == "models":
        model_performance(days=args.days)
    elif args.command == "export":
        export_logs(days=args.days, fmt=args.format)
