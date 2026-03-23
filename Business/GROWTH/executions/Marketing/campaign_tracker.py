#!/usr/bin/env python3
"""Campaign tracker for the Marketing agent — campaign-track task."""

from __future__ import annotations

import argparse
import os
import sys


def _find_repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if (os.path.isfile(os.path.join(d, "shared", "notion_client.py")) and os.path.isdir(os.path.join(d, "Business"))):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Could not locate the Orchestrator repo root")


_REPO = _find_repo_root()
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from dotenv import load_dotenv

load_dotenv(os.path.join(_REPO, ".env"))
load_dotenv(os.path.join(_REPO, "Hedge Edge Business", "IDE 1", ".env"), override=True)

from shared.notion_client import query_db


def _pct(n, d):
    return round(n / d * 100, 1) if d else 0.0


def _health(rate, good, warn):
    if rate >= good:
        return "HEALTHY"
    if rate >= warn:
        return "WARNING"
    return "CRITICAL"


def _read_campaigns():
    rows = query_db("campaigns")
    out = []
    for r in rows:
        sent = r.get("Total Sent") or 0
        delivered = r.get("Total Delivered") or 0
        bounced = r.get("Total Bounced") or 0
        opened = r.get("Total Opened") or 0
        clicked = r.get("Total Clicked") or 0
        replied = r.get("Total Replied") or 0
        out.append({
            "name": r.get("Name") or "?",
            "status": r.get("Status") or "Unknown",
            "score": r.get("Campaign Score") or 0,
            "sequences": r.get("Sequence Count") or 0,
            "sent": sent, "delivered": delivered, "bounced": bounced,
            "opened": opened, "clicked": clicked, "replied": replied,
            "delivery_rate": _pct(delivered, sent),
            "open_rate": _pct(opened, delivered),
            "click_rate": _pct(clicked, delivered),
            "reply_rate": _pct(replied, delivered),
            "invisible_fails": max(0, sent - delivered - bounced),
        })
    out.sort(key=lambda c: (c["status"] != "Active", -c["sent"]))
    return out


def _print(c):
    dr = c["delivery_rate"]
    print(f"  {c['name']}")
    print(f"    Status: {c['status']}  Score: {c['score']}  Sequences: {c['sequences']}")
    print(f"    Sent {c['sent']} -> Delivered {c['delivered']} ({dr}%) [{_health(dr,95,90)}]")
    print(f"    Open {c['opened']} ({c['open_rate']}%)  Click {c['clicked']} ({c['click_rate']}%)  Reply {c['replied']} ({c['reply_rate']}%)")
    if c["invisible_fails"]:
        print(f"    Invisible fails: {c['invisible_fails']}")


def cmd_active():
    camps = [c for c in _read_campaigns() if c["status"] == "Active"]
    print("=" * 60)
    print("  ACTIVE CAMPAIGNS")
    print("=" * 60)
    print(f"  Count: {len(camps)}\n")
    for c in camps:
        _print(c)
        print()


def cmd_report():
    camps = _read_campaigns()
    print("=" * 60)
    print("  ALL CAMPAIGNS")
    print("=" * 60)
    grouped = {}
    for c in camps:
        grouped.setdefault(c["status"], []).append(c)
    for status, items in grouped.items():
        print(f"\n  [{status}] ({len(items)})")
        for c in items:
            _print(c)
            print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--action", required=True, choices=["active-campaigns", "report", "status"])
    args = p.parse_args()
    if args.action in ("active-campaigns", "status"):
        cmd_active()
    else:
        cmd_report()


if __name__ == "__main__":
    main()