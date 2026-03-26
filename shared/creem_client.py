"""
Creem.io subscription and payment client.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides subscription listing and payment webhook helpers.

Env vars:
    CREEM_LIVE_API_KEY   — production API key
    CREEM_LIVE_API_URL   — production base URL
    CREEM_TEST_API_KEY   — test/sandbox API key
    CREEM_TEST_API_URL   — test/sandbox base URL
"""

import os
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()


def _config(use_test: bool = False) -> tuple[str, str]:
    """Return (base_url, api_key) for the requested environment."""
    if use_test:
        url = os.getenv("CREEM_TEST_API_URL", "")
        key = os.getenv("CREEM_TEST_API_KEY", "")
        if not url or not key:
            raise RuntimeError("CREEM_TEST_API_URL and CREEM_TEST_API_KEY must be set in .env")
    else:
        url = os.getenv("CREEM_LIVE_API_URL", "")
        key = os.getenv("CREEM_LIVE_API_KEY", "")
        if not url or not key:
            raise RuntimeError("CREEM_LIVE_API_URL and CREEM_LIVE_API_KEY must be set in .env")
    return url.rstrip("/"), key


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def list_subscriptions(
    use_test: bool = False,
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List subscriptions from Creem.

    Args:
        use_test: If True, hits the test environment.
        status:   Optional filter — "active", "canceled", "past_due", etc.
        limit:    Max results to return.

    Returns list of subscription dicts with keys like:
        id, customer_id, product_id, status, current_period_start,
        current_period_end, cancel_at_period_end, created_at, etc.
    """
    base, key = _config(use_test)
    url = f"{base}/subscriptions"
    params: dict[str, Any] = {"limit": limit}
    if status:
        params["status"] = status

    resp = requests.get(url, headers=_headers(key), params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", data.get("data", data)) if isinstance(data, dict) else data


def get_subscription(
    subscription_id: str,
    use_test: bool = False,
) -> dict[str, Any]:
    """Get a single subscription by ID."""
    base, key = _config(use_test)
    url = f"{base}/subscriptions/{subscription_id}"
    resp = requests.get(url, headers=_headers(key), timeout=30)
    resp.raise_for_status()
    return resp.json()
