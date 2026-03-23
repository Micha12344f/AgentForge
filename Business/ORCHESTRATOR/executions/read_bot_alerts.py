#!/usr/bin/env python3
"""
Discord #bot-alerts Reader — Error Handler Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads recent messages from the #bot-alerts Discord channel so agents can
inspect error notifications without requiring manual screenshots.

Actions:
  recent   — Last N messages (default 20)
  errors   — Only warn/critical alerts (red/orange embeds)
  search   — Messages matching a keyword
  summary  — Compact one-line-per-alert digest

Usage:
    python read_bot_alerts.py --action recent
    python read_bot_alerts.py --action recent --limit 10
    python read_bot_alerts.py --action errors --limit 50
    python read_bot_alerts.py --action search --keyword "reply"
    python read_bot_alerts.py --action summary
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ──
_ws_root = Path(__file__).resolve().parents[6]  # up to Orchestrator/
sys.path.insert(0, str(_ws_root))

from dotenv import load_dotenv
load_dotenv(_ws_root / ".env")

from shared.discord_client import (
    get_channel_messages,
    search_channel_messages,
    get_guild_channels,
)


# ── Channel resolution ──

def _get_alerts_channel_id() -> str:
    """Get #bot-alerts channel ID from env or auto-discover."""
    cid = os.getenv("DISCORD_ALERTS_CHANNEL_ID", "")
    if cid:
        return cid
    # Try discovering by name
    guild_id = os.getenv("DISCORD_GUILD_ID", "")
    if guild_id:
        channels = get_guild_channels(guild_id)
        for ch in channels:
            if ch.get("name") in ("bot-alerts", "bot_alerts"):
                return ch["id"]
    raise RuntimeError(
        "Cannot resolve #bot-alerts channel. "
        "Set DISCORD_ALERTS_CHANNEL_ID in .env or provide DISCORD_GUILD_ID."
    )


# ── Formatters ──

def _format_message(msg: dict, compact: bool = False) -> str:
    """Pretty-print a single Discord message."""
    ts = msg.get("timestamp", "")[:19].replace("T", " ")
    author = msg.get("author", {}).get("username", "unknown")
    content = msg.get("content", "")
    embeds = msg.get("embeds", [])

    if compact:
        # One-liner: timestamp | title or first 80 chars
        title = ""
        for emb in embeds:
            title = emb.get("title", "")
            if title:
                break
        summary = title or content[:80] or "(embed only)"
        return f"  {ts}  {summary}"

    lines = [f"── {ts} by {author} ──"]
    if content:
        lines.append(content[:500])
    for emb in embeds:
        if emb.get("title"):
            lines.append(f"  Title:  {emb['title']}")
        if emb.get("description"):
            desc = emb["description"][:300]
            lines.append(f"  Body:   {desc}")
        for f in emb.get("fields", []):
            lines.append(f"  {f['name']}: {f['value']}")
        color = emb.get("color", 0)
        if color in (0xFF3333, 16711475):
            lines.append("  [CRITICAL — red]")
        elif color in (0xFFA500, 16753920):
            lines.append("  [WARNING — orange]")
    return "\n".join(lines)


# ── Actions ──

def action_recent(channel_id: str, limit: int) -> None:
    msgs = get_channel_messages(channel_id, limit=limit)
    if not msgs:
        print("No messages found.")
        return
    print(f"=== Last {len(msgs)} messages from #bot-alerts ===\n")
    for m in reversed(msgs):  # chronological
        print(_format_message(m))
        print()


def action_errors(channel_id: str, limit: int) -> None:
    msgs = search_channel_messages(channel_id, error_only=True, limit=limit)
    if not msgs:
        print("No error/warning alerts found.")
        return
    print(f"=== {len(msgs)} error/warning alerts (scanning {limit} messages) ===\n")
    for m in reversed(msgs):
        print(_format_message(m))
        print()


def action_search(channel_id: str, keyword: str, limit: int) -> None:
    msgs = search_channel_messages(channel_id, keyword=keyword, limit=limit)
    if not msgs:
        print(f'No messages matching "{keyword}".')
        return
    print(f'=== {len(msgs)} messages matching "{keyword}" ===\n')
    for m in reversed(msgs):
        print(_format_message(m))
        print()


def action_summary(channel_id: str, limit: int) -> None:
    msgs = get_channel_messages(channel_id, limit=limit)
    if not msgs:
        print("No messages found.")
        return
    print(f"=== Alert summary (last {len(msgs)}) ===")
    for m in reversed(msgs):
        print(_format_message(m, compact=True))


def action_json(channel_id: str, limit: int) -> None:
    """Raw JSON dump for programmatic consumption."""
    msgs = get_channel_messages(channel_id, limit=limit)
    print(json.dumps(msgs, indent=2, default=str))


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="Read #bot-alerts Discord channel")
    parser.add_argument("--action", choices=["recent", "errors", "search", "summary", "json"],
                        default="recent")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--keyword", type=str, default="")
    parser.add_argument("--channel-id", type=str, default="",
                        help="Override channel ID (default: DISCORD_ALERTS_CHANNEL_ID)")
    args = parser.parse_args()

    channel_id = args.channel_id or _get_alerts_channel_id()

    if args.action == "recent":
        action_recent(channel_id, args.limit)
    elif args.action == "errors":
        action_errors(channel_id, args.limit)
    elif args.action == "search":
        if not args.keyword:
            parser.error("--keyword required for search action")
        action_search(channel_id, args.keyword, args.limit)
    elif args.action == "summary":
        action_summary(channel_id, args.limit)
    elif args.action == "json":
        action_json(channel_id, args.limit)


if __name__ == "__main__":
    main()
