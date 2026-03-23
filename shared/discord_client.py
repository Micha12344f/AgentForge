"""
Hedge Edge — Discord Client
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bot messaging, channel management, and webhook posting.

Usage:
    from shared.discord_client import send_message, send_embed, get_guild_info
"""

import os
import requests
from typing import Optional
from shared.env_loader import load_env_for_source

load_env_for_source()

BASE_URL = "https://discord.com/api/v10"


def _headers() -> dict:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN must be set in .env")
    return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}


def send_message(channel_id: str, content: str) -> dict:
    """Send a text message to a Discord channel."""
    r = requests.post(
        f"{BASE_URL}/channels/{channel_id}/messages",
        headers=_headers(),
        json={"content": content},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def send_embed(channel_id: str, title: str, description: str,
               color: int = 0x00D4AA, fields: Optional[list[dict]] = None) -> dict:
    """Send a rich embed to a Discord channel."""
    embed = {"title": title, "description": description, "color": color}
    if fields:
        embed["fields"] = fields
    r = requests.post(
        f"{BASE_URL}/channels/{channel_id}/messages",
        headers=_headers(),
        json={"embeds": [embed]},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_guild_info(guild_id: str) -> dict:
    """Get guild (server) information."""
    r = requests.get(f"{BASE_URL}/guilds/{guild_id}", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def get_guild_channels(guild_id: str) -> list[dict]:
    """List all channels in a guild."""
    r = requests.get(f"{BASE_URL}/guilds/{guild_id}/channels", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def get_guild_members(guild_id: str, limit: int = 100) -> list[dict]:
    """List guild members."""
    r = requests.get(
        f"{BASE_URL}/guilds/{guild_id}/members",
        headers=_headers(),
        params={"limit": limit},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    after: Optional[str] = None,
) -> list[dict]:
    """Fetch recent messages from a Discord channel.

    Args:
        channel_id: The channel to read from.
        limit:      Number of messages (1-100, default 50).
        before:     Get messages before this message ID.
        after:      Get messages after this message ID.

    Returns:
        List of message objects (newest first), each containing:
        id, content, author, timestamp, embeds, etc.
    """
    params: dict = {"limit": min(max(limit, 1), 100)}
    if before:
        params["before"] = before
    if after:
        params["after"] = after
    r = requests.get(
        f"{BASE_URL}/channels/{channel_id}/messages",
        headers=_headers(),
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def search_channel_messages(
    channel_id: str,
    keyword: str = "",
    limit: int = 50,
    error_only: bool = False,
) -> list[dict]:
    """Fetch messages and optionally filter by keyword or error severity.

    This is a client-side filter on top of get_channel_messages (Discord
    does not expose a search API for bots). Good enough for #bot-alerts
    where volume is manageable.

    Args:
        channel_id: Channel to read.
        keyword:    Case-insensitive substring to match in content or embed text.
        limit:      Max messages to scan (may paginate up to this many).
        error_only: If True, only return messages whose embeds have red-ish
                    colour (0xFF3333 / 0xFFA500) — i.e. warn + critical alerts.

    Returns:
        Filtered list of message dicts.
    """
    _ALERT_COLORS = {0xFF3333, 0xFFA500, 16711475, 16753920}  # red, orange (decimal too)
    collected: list[dict] = []
    before_id: Optional[str] = None
    fetched = 0

    while fetched < limit:
        batch_size = min(100, limit - fetched)
        msgs = get_channel_messages(channel_id, limit=batch_size, before=before_id)
        if not msgs:
            break
        for m in msgs:
            text_blob = (m.get("content") or "").lower()
            for emb in m.get("embeds", []):
                text_blob += " " + (emb.get("title") or "").lower()
                text_blob += " " + (emb.get("description") or "").lower()

            if keyword and keyword.lower() not in text_blob:
                continue
            if error_only:
                colors = {emb.get("color", 0) for emb in m.get("embeds", [])}
                if not colors & _ALERT_COLORS:
                    continue
            collected.append(m)
        fetched += len(msgs)
        before_id = msgs[-1]["id"]
    return collected


def post_webhook(webhook_url: str, content: str, username: str = "Hedge Edge") -> dict:
    """Post via a Discord webhook URL."""
    r = requests.post(
        webhook_url,
        json={"content": content, "username": username},
        timeout=10,
    )
    r.raise_for_status()
    return {"status": "sent"}
