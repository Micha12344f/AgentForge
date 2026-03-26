"""
Resend email and audience client.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends emails and manages audiences/contacts via the Resend API.

Env vars:
    RESEND_API_KEY — Resend API key
"""

import os
import re
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

BASE_URL = "https://api.resend.com"


def _sanitize_tag_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    return cleaned or "tag"


def _sanitize_tags(tags: list[dict]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    for tag in tags:
        name = _sanitize_tag_token(str(tag.get("name", "tag")))
        value = _sanitize_tag_token(str(tag.get("value", "tag")))
        sanitized.append({"name": name, "value": value})
    return sanitized


def _api_key() -> str:
    key = os.getenv("RESEND_API_KEY", "")
    if not key:
        raise RuntimeError("RESEND_API_KEY must be set in .env")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


# ── Email Sending ─────────────────────────────────────────

def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    from_addr: str = "Hedge Edge <hello@hedgedge.info>",
    reply_to: Optional[str] = None,
    tags: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Send a single email via Resend."""
    payload: dict[str, Any] = {
        "from": from_addr,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = _sanitize_tags(tags)
    r = requests.post(f"{BASE_URL}/emails", headers=_headers(), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def get_email(email_id: str) -> dict[str, Any]:
    """Get details of a sent email by ID."""
    r = requests.get(f"{BASE_URL}/emails/{email_id}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


# ── Audiences ─────────────────────────────────────────────

def list_audiences() -> list[dict[str, Any]]:
    """List all audiences."""
    r = requests.get(f"{BASE_URL}/audiences", headers=_headers(), timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else data


# ── Contacts ──────────────────────────────────────────────

def list_contacts(audience_id: str) -> list[dict[str, Any]]:
    """List all contacts in an audience."""
    r = requests.get(
        f"{BASE_URL}/audiences/{audience_id}/contacts",
        headers=_headers(),
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else data


def create_contact(
    audience_id: str,
    email: str,
    first_name: str = "",
    last_name: str = "",
    unsubscribed: bool = False,
) -> dict[str, Any]:
    """Add a contact to an audience."""
    payload: dict[str, Any] = {"email": email, "unsubscribed": unsubscribed}
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    r = requests.post(
        f"{BASE_URL}/audiences/{audience_id}/contacts",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def remove_contact(audience_id: str, contact_id: str) -> dict[str, Any]:
    """Remove a contact from an audience."""
    r = requests.delete(
        f"{BASE_URL}/audiences/{audience_id}/contacts/{contact_id}",
        headers=_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


# ── Webhooks ──────────────────────────────────────────────

def list_webhooks() -> list[dict[str, Any]]:
    """List all webhooks."""
    r = requests.get(f"{BASE_URL}/webhooks", headers=_headers(), timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else data


def create_webhook(
    url: str,
    events: list[str],
    name: str = "",
) -> dict[str, Any]:
    """Create a new webhook."""
    payload: dict[str, Any] = {"url": url, "events": events}
    if name:
        payload["name"] = name
    r = requests.post(f"{BASE_URL}/webhooks", headers=_headers(), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()
