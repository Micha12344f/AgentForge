"""
Resend Email Client
━━━━━━━━━━━━━━━━━━━
Sends emails via Resend API.
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

_ws_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ws_root, ".env"))

BASE_URL = "https://api.resend.com"


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
        payload["tags"] = tags
    r = requests.post(f"{BASE_URL}/emails", headers=_headers(), json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
