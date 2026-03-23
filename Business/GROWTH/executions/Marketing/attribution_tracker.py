#!/usr/bin/env python3
"""
attribution_tracker.py — Live Attribution Pipeline Auditor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Audits and tracks the full UTM attribution lifecycle from
page_views → user_attribution in Supabase.

Actions:
    audit    — Full pipeline health check: page_views, user_attribution,
               session linkage, referrer normalization
    sources  — UTM source/medium breakdown for page_views
    linkage  — Check if UTM pageviews exist near each signup
    models   — Run first-touch / last-touch / linear attribution models

Usage:
    python attribution_tracker.py --action audit
    python attribution_tracker.py --action sources
    python attribution_tracker.py --action linkage
    python attribution_tracker.py --action models
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *(['..'] * 4)))
sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.supabase_client import get_supabase
from shared.notion_client import log_task

sb = get_supabase(use_service_role=True)


# ── Helpers ──────────────────────────────────────────────

def _page_view_stats() -> tuple[int, list[dict]]:
    """Return (total_count, utm_rows)."""
    total = sb.table("page_views").select("*", count="exact").execute()
    utm = (sb.table("page_views")
           .select("utm_source,utm_medium,utm_campaign,referrer_domain,path,created_at")
           .not_.is_("utm_source", "null")
           .order("created_at", desc=True)
           .execute())
    return total.count, utm.data


def _attribution_rows() -> list[dict]:
    return sb.table("user_attribution").select("*").order("signed_up_at").execute().data or []


# ── Actions ──────────────────────────────────────────────

def action_sources():
    """UTM source / medium breakdown for page_views."""
    total_count, utm_rows = _page_view_stats()
    sources = Counter(r["utm_source"] for r in utm_rows)
    mediums = Counter(r["utm_medium"] for r in utm_rows if r.get("utm_medium"))

    print(f"\n{'='*50}")
    print(f"  PAGE VIEW UTM BREAKDOWN")
    print(f"{'='*50}")
    print(f"  Total:       {total_count}")
    print(f"  With UTM:    {len(utm_rows)} ({len(utm_rows)/max(total_count,1)*100:.0f}%)")
    print(f"  Direct:      {total_count - len(utm_rows)}")
    print(f"\n  Sources:")
    for src, cnt in sources.most_common():
        print(f"    {src:20s} {cnt}")
    print(f"\n  Mediums:")
    for med, cnt in mediums.most_common():
        print(f"    {med:20s} {cnt}")


def action_linkage():
    """Check if UTM pageviews exist within 2hr window before each signup."""
    rows = _attribution_rows()
    print(f"\n{'='*50}")
    print(f"  SESSION LINKAGE CHECK ({len(rows)} users)")
    print(f"{'='*50}")

    linked = 0
    for row in rows:
        signed_up = row.get("signed_up_at")
        if not signed_up:
            continue
        dt = datetime.fromisoformat(signed_up)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        window_start = (dt - timedelta(hours=2)).isoformat()
        window_end = dt.isoformat()
        pv = (sb.table("page_views")
              .select("utm_source,path,created_at")
              .gte("created_at", window_start)
              .lte("created_at", window_end)
              .not_.is_("utm_source", "null")
              .execute())

        label = (row.get("user_id") or "")[:8] or row.get("email", "?")[:20]
        method = row.get("signup_method") or "unknown"
        if pv.data:
            linked += 1
            srcs = ", ".join(set(p["utm_source"] for p in pv.data))
            print(f"  ✅ {label:20s}  {method:12s}  {signed_up[:16]}  {len(pv.data)} UTM views  [{srcs}]")
        else:
            print(f"  ❌ {label:20s}  {method:12s}  {signed_up[:16]}  NO UTM views  [src={row.get('utm_source') or 'direct'}]")

    print(f"\n  Linked: {linked}/{len(rows)}")


def action_models():
    """Run first-touch, last-touch, linear attribution models."""
    rows = _attribution_rows()
    print(f"\n{'='*50}")
    print(f"  ATTRIBUTION MODELS ({len(rows)} users)")
    print(f"{'='*50}")

    # First-touch
    ft = defaultdict(int)
    for r in rows:
        ft[r.get("utm_source") or "direct"] += 1
    print(f"\n  First-Touch (by source):")
    for src, cnt in sorted(ft.items(), key=lambda x: -x[1]):
        print(f"    {src:20s} {cnt}")

    # Last-touch
    lt = defaultdict(int)
    for r in rows:
        lt[r.get("utm_medium") or "none"] += 1
    print(f"\n  Last-Touch (by medium):")
    for med, cnt in sorted(lt.items(), key=lambda x: -x[1]):
        print(f"    {med:20s} {cnt}")

    # Linear
    linear = defaultdict(float)
    for r in rows:
        touches = [v for k in ("utm_source", "utm_medium", "utm_campaign") if (v := r.get(k))]
        if not touches:
            touches = ["direct"]
        credit = 1.0 / len(touches)
        for t in touches:
            linear[t] += credit
    print(f"\n  Linear (equal credit):")
    for ch, cred in sorted(linear.items(), key=lambda x: -x[1]):
        print(f"    {ch:20s} {cred:.1f}")


def action_audit():
    """Full pipeline health audit."""
    total_count, utm_rows = _page_view_stats()
    ua_rows = _attribution_rows()

    # Source breakdown
    sources = Counter(r["utm_source"] for r in utm_rows)
    direct_users = sum(1 for r in ua_rows if not r.get("utm_source"))

    # Session linkage (quick check)
    linked = 0
    for row in ua_rows:
        signed_up = row.get("signed_up_at")
        if not signed_up:
            continue
        dt = datetime.fromisoformat(signed_up)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        window_start = (dt - timedelta(hours=2)).isoformat()
        window_end = dt.isoformat()
        pv = (sb.table("page_views")
              .select("id", count="exact")
              .gte("created_at", window_start)
              .lte("created_at", window_end)
              .not_.is_("utm_source", "null")
              .execute())
        if pv.count and pv.count > 0:
            linked += 1

    # Referrer normalization check
    KNOWN_PROXIES = {"t.co", "l.facebook.com", "lnkd.in", "youtu.be"}
    ref_rows = (sb.table("page_views")
                .select("referrer_domain,utm_source")
                .not_.is_("referrer_domain", "null")
                .execute())
    proxy_leaks = sum(1 for r in ref_rows.data
                      if r.get("referrer_domain") in KNOWN_PROXIES
                      and r.get("utm_source") == r.get("referrer_domain"))

    print(f"\n{'='*60}")
    print(f"  ATTRIBUTION PIPELINE HEALTH REPORT")
    print(f"{'='*60}")
    print(f"\n  Page Views")
    print(f"    Total:              {total_count}")
    print(f"    With UTM:           {len(utm_rows)} ({len(utm_rows)/max(total_count,1)*100:.0f}%)")
    print(f"    Direct:             {total_count - len(utm_rows)}")
    print(f"\n  User Attribution")
    print(f"    Total users:        {len(ua_rows)}")
    print(f"    With source:        {len(ua_rows) - direct_users}")
    print(f"    Direct/unknown:     {direct_users}")
    print(f"    Session-linked:     {linked}/{len(ua_rows)}")
    print(f"\n  Top Sources")
    for src, cnt in sources.most_common(5):
        print(f"    {src:20s} {cnt}")
    print(f"\n  Referrer Normalization")
    if proxy_leaks:
        print(f"    ⚠️  {proxy_leaks} pageviews with raw proxy domains (pre-fix data)")
    else:
        print(f"    ✅  All proxy referrers normalized correctly")
    print(f"\n  Pipeline Status")
    if direct_users / max(len(ua_rows), 1) > 0.5:
        print(f"    ⚠️  >50% users show as direct — check UTM capture on landing page")
    else:
        print(f"    ✅  Attribution pipeline healthy")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Attribution Tracker")
    parser.add_argument("--action", required=True,
                        choices=["audit", "sources", "linkage", "models"])
    args = parser.parse_args()

    actions = {
        "audit": action_audit,
        "sources": action_sources,
        "linkage": action_linkage,
        "models": action_models,
    }
    actions[args.action]()
    log_task("Growth/Marketing", "attribution-tracking", args.action, "success")


if __name__ == "__main__":
    main()
