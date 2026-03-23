#!/usr/bin/env python3
"""
Hedge Edge — Discord Slash Command Registration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Registers (or updates) slash commands with the Discord API.
Run this once, or whenever commands change.

Commands:
    /ask <message>          — Free-form question routed through Orchestrator + Groq
    /run <agent> <task>     — Direct task execution
    /status                 — System health + agent status
    /logs <agent> [count]   — Recent log entries for an agent
    /brief                  — On-demand daily brief

Usage:
    python scripts/discord/register_commands.py
    python scripts/discord/register_commands.py --guild   # Guild-only (instant, for testing)
    python scripts/discord/register_commands.py --global  # Global (takes ~1h to propagate)

Requires: DISCORD_BOT_TOKEN, DISCORD_APPLICATION_ID in .env
          (also DISCORD_GUILD_ID if using --guild)
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if os.path.isfile(os.path.join(d, "shared", "notion_client.py")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)
load_dotenv(os.path.join(_WS_ROOT, ".env"))

BASE_URL = "https://discord.com/api/v10"

# ── Agent choices for slash command options ──
AGENT_CHOICES = [
    {"name": "Orchestrator",        "value": "orchestrator"},
    {"name": "Marketing",           "value": "marketing"},
    {"name": "Sales",               "value": "sales"},
    {"name": "Analytics",           "value": "analytics"},
    {"name": "Finance",             "value": "finance"},
    {"name": "Content Engine",      "value": "content-engine"},
    {"name": "Community Manager",   "value": "community-manager"},
    {"name": "Product",             "value": "product"},
    {"name": "Business Strategist", "value": "business-strategist"},
]

# ── Slash command definitions ──
COMMANDS = [
    {
        "name": "ask",
        "type": 1,  # CHAT_INPUT
        "description": "Ask the Orchestrator a question (routed via Groq AI)",
        "options": [
            {
                "name": "message",
                "description": "Your question or instruction",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    },
    {
        "name": "run",
        "type": 1,
        "description": "Execute an agent task directly",
        "options": [
            {
                "name": "agent",
                "description": "Which agent to run",
                "type": 3,  # STRING
                "required": True,
                "choices": AGENT_CHOICES,
            },
            {
                "name": "task",
                "description": "Task name (e.g. email-marketing, kpi-snapshot)",
                "type": 3,
                "required": True,
            },
            {
                "name": "action",
                "description": "Action to perform (default: run)",
                "type": 3,
                "required": False,
            },
        ],
    },
    {
        "name": "status",
        "type": 1,
        "description": "Get system health and agent status overview",
    },
    {
        "name": "logs",
        "type": 1,
        "description": "View recent log entries for an agent",
        "options": [
            {
                "name": "agent",
                "description": "Which agent's logs to view",
                "type": 3,
                "required": True,
                "choices": AGENT_CHOICES + [{"name": "System", "value": "system"}],
            },
            {
                "name": "count",
                "description": "Number of log entries (default 10, max 25)",
                "type": 4,  # INTEGER
                "required": False,
                "min_value": 1,
                "max_value": 25,
            },
        ],
    },
    {
        "name": "brief",
        "type": 1,
        "description": "Generate and display the daily business brief on demand",
    },
]


def _headers() -> dict:
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not set in .env")
    return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}


def register_guild_commands(app_id: str, guild_id: str) -> None:
    """Register commands for a specific guild (instant propagation)."""
    url = f"{BASE_URL}/applications/{app_id}/guilds/{guild_id}/commands"
    r = requests.put(url, headers=_headers(), json=COMMANDS, timeout=30)
    r.raise_for_status()
    result = r.json()
    print(f"  ✅ Registered {len(result)} guild commands")
    for cmd in result:
        print(f"     /{cmd['name']} (id: {cmd['id']})")


def register_global_commands(app_id: str) -> None:
    """Register commands globally (takes ~1 hour to propagate)."""
    url = f"{BASE_URL}/applications/{app_id}/commands"
    r = requests.put(url, headers=_headers(), json=COMMANDS, timeout=30)
    r.raise_for_status()
    result = r.json()
    print(f"  ✅ Registered {len(result)} global commands (propagation takes ~1hr)")
    for cmd in result:
        print(f"     /{cmd['name']} (id: {cmd['id']})")


def main():
    parser = argparse.ArgumentParser(description="Register Discord slash commands")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--guild", action="store_true", default=True,
                       help="Register as guild commands (instant, default)")
    group.add_argument("--global", dest="global_", action="store_true",
                       help="Register as global commands (~1hr propagation)")
    args = parser.parse_args()

    app_id = os.getenv("DISCORD_APPLICATION_ID", "")
    if not app_id:
        print("❌ DISCORD_APPLICATION_ID not set in .env")
        sys.exit(1)

    print("=" * 60)
    print("  Hedge Edge — Slash Command Registration")
    print("=" * 60)
    print(f"  Application: {app_id}")
    print(f"  Commands: {len(COMMANDS)}")
    print(f"  Scope: {'global' if args.global_ else 'guild'}")
    print()

    if args.global_:
        register_global_commands(app_id)
    else:
        guild_id = os.getenv("DISCORD_GUILD_ID", "")
        if not guild_id:
            print("❌ DISCORD_GUILD_ID not set in .env (required for guild commands)")
            sys.exit(1)
        print(f"  Guild: {guild_id}")
        register_guild_commands(app_id, guild_id)

    print()
    print("  Done! Set your Interactions Endpoint URL in the Discord Developer Portal:")
    print("  → https://interact.hedgedge.info/interactions")


if __name__ == "__main__":
    main()
