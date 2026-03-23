#!/usr/bin/env python3
"""
Hedge Edge — Discord Log Channel & Webhook Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creates per-agent log channels under a "AGENT LOGS" category,
sets them as private (team-only), and creates a webhook for each.

Outputs a LOG_WEBHOOKS JSON string ready to paste into .env.

Channels created:
    #logs-orchestrator   #logs-marketing     #logs-sales
    #logs-analytics      #logs-finance       #logs-content-engine
    #logs-community      #logs-product       #logs-strategy
    #logs-system         (cron, health, deploy events)

Permissions:
    @everyone denied view → channels are invisible to non-team members.
    Team role (DISCORD_TEAM_ROLE_ID) granted view + read history.

Usage:
    python scripts/discord/setup_log_channels.py
    python scripts/discord/setup_log_channels.py --dry-run

Requires: DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_TEAM_ROLE_ID in .env
"""

import os
import sys
import json
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

# ── Agent → channel name mapping ──
AGENT_CHANNELS = {
    "orchestrator":  "logs-orchestrator",
    "marketing":     "logs-marketing",
    "sales":         "logs-sales",
    "analytics":     "logs-analytics",
    "finance":       "logs-finance",
    "content_engine": "logs-content-engine",
    "community":     "logs-community",
    "product":       "logs-product",
    "strategy":      "logs-strategy",
    "system":        "logs-system",
}

CATEGORY_NAME = "AGENT LOGS"


def _headers() -> dict:
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not set in .env")
    return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}


def _get_guild_channels(guild_id: str) -> list[dict]:
    r = requests.get(f"{BASE_URL}/guilds/{guild_id}/channels", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _create_category(guild_id: str, team_role_id: str) -> str:
    """Create the 'AGENT LOGS' category with team-only permissions."""
    # Permission overwrites:
    #   @everyone (guild_id) → deny VIEW_CHANNEL (0x400)
    #   team role            → allow VIEW_CHANNEL + READ_MESSAGE_HISTORY (0x400 | 0x10000)
    overwrites = [
        {
            "id": guild_id,         # @everyone
            "type": 0,              # role
            "deny": str(1 << 10),   # VIEW_CHANNEL
            "allow": "0",
        },
        {
            "id": team_role_id,
            "type": 0,              # role
            "allow": str((1 << 10) | (1 << 16)),  # VIEW_CHANNEL + READ_MESSAGE_HISTORY
            "deny": "0",
        },
    ]
    payload = {
        "name": CATEGORY_NAME,
        "type": 4,  # GUILD_CATEGORY
        "permission_overwrites": overwrites,
    }
    r = requests.post(
        f"{BASE_URL}/guilds/{guild_id}/channels",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    cat = r.json()
    print(f"  ✅ Created category: {CATEGORY_NAME} ({cat['id']})")
    return cat["id"]


def _create_text_channel(guild_id: str, name: str, category_id: str, topic: str = "") -> dict:
    """Create a text channel under the given category."""
    payload = {
        "name": name,
        "type": 0,  # GUILD_TEXT
        "parent_id": category_id,
        "topic": topic or f"Automated logs for {name.replace('logs-', '')}",
    }
    r = requests.post(
        f"{BASE_URL}/guilds/{guild_id}/channels",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _create_webhook(channel_id: str, name: str) -> str:
    """Create a webhook for a channel, return the webhook URL."""
    payload = {"name": f"Hedge Edge — {name.replace('logs-', '').title()} Logs"}
    r = requests.post(
        f"{BASE_URL}/channels/{channel_id}/webhooks",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    wh = r.json()
    return f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"


def main():
    parser = argparse.ArgumentParser(description="Setup Discord log channels")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without creating")
    args = parser.parse_args()

    guild_id = os.getenv("DISCORD_GUILD_ID", "")
    team_role_id = os.getenv("DISCORD_TEAM_ROLE_ID", "")

    if not guild_id:
        print("❌ DISCORD_GUILD_ID not set in .env")
        sys.exit(1)
    if not team_role_id:
        print("❌ DISCORD_TEAM_ROLE_ID not set in .env — needed to gate channels to team only")
        print("   Set this to the role ID for your Hedge Edge team members.")
        sys.exit(1)

    print("=" * 60)
    print("  Hedge Edge — Discord Log Channel Setup")
    print("=" * 60)
    print(f"  Guild: {guild_id}")
    print(f"  Team Role: {team_role_id}")
    print(f"  Channels: {len(AGENT_CHANNELS)}")
    print()

    if args.dry_run:
        print("  [DRY RUN] Would create:")
        print(f"    Category: {CATEGORY_NAME}")
        for agent, ch_name in sorted(AGENT_CHANNELS.items()):
            print(f"    #{ch_name} → webhook for '{agent}'")
        print("\n  Run without --dry-run to create channels.")
        return

    # Check for existing channels
    existing = _get_guild_channels(guild_id)
    existing_names = {ch["name"] for ch in existing}

    # Find or create the category
    category_id = None
    for ch in existing:
        if ch["type"] == 4 and ch["name"].upper() == CATEGORY_NAME:
            category_id = ch["id"]
            print(f"  ♻️  Using existing category: {CATEGORY_NAME} ({category_id})")
            break

    if not category_id:
        category_id = _create_category(guild_id, team_role_id)

    # Create channels + webhooks
    webhooks = {}
    for agent_key, ch_name in sorted(AGENT_CHANNELS.items()):
        if ch_name in existing_names:
            # Find existing channel ID
            ch_id = next(ch["id"] for ch in existing if ch["name"] == ch_name)
            print(f"  ♻️  #{ch_name} already exists ({ch_id})")
        else:
            ch = _create_text_channel(guild_id, ch_name, category_id)
            ch_id = ch["id"]
            print(f"  ✅ Created #{ch_name} ({ch_id})")

        # Create webhook for the channel
        wh_url = _create_webhook(ch_id, ch_name)
        webhooks[agent_key] = wh_url
        print(f"     🔗 Webhook created for {agent_key}")

    # Output the LOG_WEBHOOKS JSON
    print()
    print("=" * 60)
    print("  Add this to your .env file:")
    print("=" * 60)
    print()
    webhooks_json = json.dumps(webhooks, indent=2)
    # Also output single-line for .env
    webhooks_oneline = json.dumps(webhooks)
    print(f"LOG_WEBHOOKS='{webhooks_oneline}'")
    print()
    print("  (Expanded for readability):")
    print(webhooks_json)
    print()

    # Save to file for reference
    out_path = os.path.join(_ws_root, "logs", "webhook_urls.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(webhooks, f, indent=2)
    print(f"  Saved to {out_path}")


if __name__ == "__main__":
    main()
