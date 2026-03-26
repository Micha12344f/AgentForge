"""
Resend Email Client
━━━━━━━━━━━━━━━━━━━
Sends emails via Resend API.
"""

import os
import re
import requests
from typing import Optional
from dotenv import load_dotenv

_ws_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ws_root, ".env"))

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


def _headers() -> dict:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        raise RuntimeError("RESEND_API_KEY must be set in .env")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    from_addr: str = "Hedge Edge <hello@hedgedge.info>",
    reply_to: Optional[str] = None,
    tags: Optional[list[dict]] = None,
) -> dict:
    """Send a single email via Resend."""
    payload = {
        "from": from_addr,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = _sanitize_tags(tags)
    r = requests.post(f"{BASE_URL}/emails", headers=_headers(), json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
