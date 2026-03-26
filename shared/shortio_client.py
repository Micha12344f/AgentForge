"""
Short.io link analytics client.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides link listing and click/stats retrieval from Short.io.

Env vars:
    SHORTIO_API_KEY   — Short.io API key
    SHORTIO_DOMAIN    — managed domain (e.g. link.hedgedge.info)
"""

import os
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

_BASE_URL = "https://api.short.io/api"
_STATISTICS_URL = "https://statistics.short.io"
_DOMAIN = os.getenv("SHORTIO_DOMAIN", "link.hedgedge.info")


def _api_key() -> str:
    key = os.getenv("SHORTIO_API_KEY", "")
    if not key:
        raise RuntimeError("SHORTIO_API_KEY must be set in .env")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": _api_key(),
        "Content-Type": "application/json",
    }


def list_links(
    limit: int = 150,
    *,
    domain: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List all short links for the domain.

    Returns list of dicts with keys: idString, originalURL, shortURL,
    title, clicks, createdAt, etc.
    """
    d = domain or _DOMAIN
    url = f"{_BASE_URL}/links"
    params = {
        "domain_id": 0,
        "domain": d,
        "limit": limit,
    }
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("links", data) if isinstance(data, dict) else data


def get_link_stats(
    link_id: str,
    period: str = "total",
) -> dict[str, Any]:
    """Get click statistics for a specific link.

    Args:
        link_id: The Short.io link ID (idString).
        period:  "total", "month", "week", "day", "last24hours".

    Returns dict with keys: totalClicks, humanClicks, browser[], country[], referer[].
    """
    url = f"{_STATISTICS_URL}/statistics/link/{link_id}"
    params = {"period": period}
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
