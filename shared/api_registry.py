"""
API Registry — declares available external APIs per agent.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Used by agent dispatchers (run.py) for status checks.
"""

import os
from shared.env_loader import load_env_for_source

load_env_for_source()

# Maps agent_key → { api_name: "ready" | "missing" }
_REGISTRY: dict[str, dict[str, list[str]]] = {
    "analytics": {
        "env_keys": [
            "NOTION_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "GA4_PROPERTY_ID",
            "GOOGLE_SERVICE_ACCOUNT_JSON",
            "RESEND_API_KEY",
            "SHORTIO_API_KEY",
            "CREEM_LIVE_API_KEY",
        ],
    },
    "growth": {
        "env_keys": [
            "NOTION_API_KEY",
            "RESEND_API_KEY",
            "DISCORD_BOT_TOKEN",
            "TWITTER_BEARER_TOKEN",
        ],
    },
    "finance": {
        "env_keys": [
            "NOTION_API_KEY",
            "SUPABASE_URL",
            "CREEM_LIVE_API_KEY",
        ],
    },
    "strategy": {
        "env_keys": [
            "NOTION_API_KEY",
            "SUPABASE_URL",
        ],
    },
    "orchestrator": {
        "env_keys": [
            "NOTION_API_KEY",
            "DISCORD_BOT_TOKEN",
            "GITHUB_TOKEN",
            "VERCEL_TOKEN",
            "RAILWAY_TOKEN",
        ],
    },
}


def get_agent_apis(agent_key: str) -> dict[str, str]:
    """Return {api_name: "ready"|"missing"} for the given agent.

    Unknown agents get an empty dict (no failure).
    """
    config = _REGISTRY.get(agent_key, {})
    env_keys = config.get("env_keys", [])
    result: dict[str, str] = {}
    for key in env_keys:
        # Use a friendly name: NOTION_API_KEY → Notion, GA4_PROPERTY_ID → GA4, etc.
        nice = key.split("_")[0].capitalize()
        result[nice] = "ready" if os.getenv(key) else "missing"
    return result
