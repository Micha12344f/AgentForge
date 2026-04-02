"""
Resend Email Client
━━━━━━━━━━━━━━━━━━━
Sends emails via Resend API with one-click unsubscribe headers.
"""

import hashlib
import hmac
import os
import re
from typing import Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv

_ws_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ws_root, ".env"))

BASE_URL = "https://api.resend.com"
DEFAULT_UNSUBSCRIBE_BASE_URL = "https://hedgedge.info/api/handle-unsubscribe"


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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _headers() -> dict:
    key = os.getenv("RESEND_API_KEY")
    if not key:
        raise RuntimeError("RESEND_API_KEY must be set in .env")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _unsubscribe_secret() -> str:
    secret = os.getenv("UNSUBSCRIBE_SECRET", "")
    if not secret:
        raise RuntimeError("UNSUBSCRIBE_SECRET must be set in .env")
    return secret


def _unsubscribe_base_url() -> str:
    return os.getenv("UNSUBSCRIBE_BASE_URL", DEFAULT_UNSUBSCRIBE_BASE_URL).rstrip("/")


def _build_unsubscribe_url(email: str) -> str:
    normalized = _normalize_email(email)
    token = hmac.new(
        _unsubscribe_secret().encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{_unsubscribe_base_url()}?email={quote(normalized)}&token={token}"


def _append_unsubscribe_html(html: Optional[str], unsubscribe_url: str) -> Optional[str]:
    if not html or "unsubscribe" in html.lower():
        return html

    footer = (
        '<div style="margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;'
        'font-size:12px;color:#6b7280;line-height:1.6;">'
        f'If you no longer want these emails, <a href="{unsubscribe_url}" '
        'style="color:#6b7280;text-decoration:underline;">unsubscribe here</a>.'
        '</div>'
    )
    body_close = re.search(r"</body>", html, re.IGNORECASE)
    if body_close:
        return f"{html[:body_close.start()]}{footer}{html[body_close.start():]}"
    html_close = re.search(r"</html>", html, re.IGNORECASE)
    if html_close:
        return f"{html[:html_close.start()]}{footer}{html[html_close.start():]}"
    return f"{html}{footer}"


def _append_unsubscribe_text(text: Optional[str], unsubscribe_url: str) -> Optional[str]:
    if not text or "unsubscribe" in text.lower():
        return text
    return f"{text}\n\n---\nUnsubscribe: {unsubscribe_url}"


def send_email(
    to: str | list[str],
    subject: str,
    html: Optional[str] = None,
    from_addr: str = "Hedge Edge <hello@hedgedge.info>",
    reply_to: Optional[str] = None,
    tags: Optional[list[dict]] = None,
    text: Optional[str] = None,
    include_unsubscribe: bool = True,
) -> dict:
    """Send a single email via Resend."""
    recipients = [to] if isinstance(to, str) else to
    if not recipients:
        raise ValueError("At least one recipient is required")
    if not html and not text:
        raise ValueError("Either html or text content must be provided")

    payload = {
        "from": from_addr,
        "to": [_normalize_email(value) for value in recipients],
        "subject": subject,
    }

    merged_headers: dict[str, str] = {}
    rendered_html = html
    rendered_text = text

    if include_unsubscribe:
        if len(recipients) != 1:
            raise ValueError("Unsubscribe-enabled sends must target exactly one recipient")
        unsubscribe_url = _build_unsubscribe_url(recipients[0])
        rendered_html = _append_unsubscribe_html(rendered_html, unsubscribe_url)
        rendered_text = _append_unsubscribe_text(rendered_text, unsubscribe_url)
        merged_headers.update(
            {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }
        )

    if reply_to:
        payload["reply_to"] = reply_to
    if rendered_html:
        payload["html"] = rendered_html
    if rendered_text:
        payload["text"] = rendered_text
    if tags:
        payload["tags"] = _sanitize_tags(tags)
    if merged_headers:
        payload["headers"] = merged_headers

    response = requests.post(f"{BASE_URL}/emails", headers=_headers(), json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
