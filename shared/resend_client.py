"""
Resend email and audience client.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends emails and manages audiences/contacts via the Resend API.

Env vars:
    RESEND_API_KEY — Resend API key
    UNSUBSCRIBE_SECRET — HMAC secret for one-click unsubscribe URLs
    UNSUBSCRIBE_BASE_URL — Optional override for the one-click unsubscribe endpoint
"""

import hashlib
import hmac
import os
import re
from typing import Any, Optional
from urllib.parse import quote

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

BASE_URL = "https://api.resend.com"
DEFAULT_UNSUBSCRIBE_BASE_URL = "https://hedgedge.info/api/handle-unsubscribe"


class RecipientUnsubscribedError(RuntimeError):
    """Raised when a recipient is blocked by the local unsubscribe source of truth."""


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


def _normalize_recipients(recipients: str | list[str]) -> list[str]:
    values = [recipients] if isinstance(recipients, str) else recipients
    return [_normalize_email(value) for value in values if str(value).strip()]


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


def _request(
    method: str,
    path: str,
    *,
    json: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
    timeout: int = 15,
) -> requests.Response:
    return requests.request(
        method,
        f"{BASE_URL}{path}",
        headers=_headers(),
        json=json,
        params=params,
        timeout=timeout,
    )


def _unsubscribe_secret() -> str:
    secret = os.getenv("UNSUBSCRIBE_SECRET", "")
    if not secret:
        raise RuntimeError("UNSUBSCRIBE_SECRET must be set in .env")
    return secret


def _unsubscribe_base_url() -> str:
    return os.getenv("UNSUBSCRIBE_BASE_URL", DEFAULT_UNSUBSCRIBE_BASE_URL).rstrip("/")


def _build_unsubscribe_token(email: str) -> str:
    clean_email = _normalize_email(email)
    return hmac.new(
        _unsubscribe_secret().encode("utf-8"),
        clean_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_unsubscribe_url(email: str) -> str:
    clean_email = _normalize_email(email)
    token = _build_unsubscribe_token(clean_email)
    return f"{_unsubscribe_base_url()}?email={quote(clean_email)}&token={token}"


def build_unsubscribe_headers(email: str) -> dict[str, str]:
    unsubscribe_url = build_unsubscribe_url(email)
    return {
        "List-Unsubscribe": f"<{unsubscribe_url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def _append_unsubscribe_html(html: Optional[str], unsubscribe_url: str) -> Optional[str]:
    if not html:
        return html
    if "unsubscribe" in html.lower():
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
    if not text:
        return text
    if "unsubscribe" in text.lower():
        return text
    return f"{text}\n\n---\nUnsubscribe: {unsubscribe_url}"


def _notion_has_unsubscribed_recipient(email: str) -> bool:
    from shared.notion_client import query_db

    rows = query_db(
        "leads_crm",
        filter={
            "and": [
                {"property": "Email", "email": {"equals": _normalize_email(email)}},
                {"property": "Unsubscribed", "checkbox": {"equals": True}},
            ]
        },
        page_size=1,
    )
    return bool(rows)


def _raise_if_blocked(recipients: list[str], respect_notion_unsubscribe: bool) -> None:
    if not respect_notion_unsubscribe:
        return

    blocked = [email for email in recipients if _notion_has_unsubscribed_recipient(email)]
    if blocked:
        if len(blocked) == 1:
            raise RecipientUnsubscribedError(f"Recipient is unsubscribed in Notion: {blocked[0]}")
        raise RecipientUnsubscribedError(
            f"Recipients are unsubscribed in Notion: {', '.join(blocked)}"
        )


def _contact_identifier(value: str) -> str:
    return quote(value, safe="")


def get_contact(identifier: str) -> Optional[dict[str, Any]]:
    """Get a contact by id or email. Returns None when the contact does not exist."""
    response = _request("GET", f"/contacts/{_contact_identifier(identifier)}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def create_contact_global(
    email: str,
    first_name: str = "",
    last_name: str = "",
    unsubscribed: bool = False,
) -> dict[str, Any]:
    """Create a global Resend contact."""
    payload: dict[str, Any] = {
        "email": _normalize_email(email),
        "unsubscribed": unsubscribed,
    }
    if first_name:
        payload["firstName"] = first_name
    if last_name:
        payload["lastName"] = last_name

    response = _request("POST", "/contacts", json=payload)
    if response.status_code == 409:
        existing = get_contact(payload["email"])
        if existing is not None:
            return existing
    response.raise_for_status()
    return response.json()


def update_contact_global(
    *,
    email: Optional[str] = None,
    contact_id: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    unsubscribed: Optional[bool] = None,
) -> dict[str, Any]:
    """Update a global Resend contact, resolving by email when an id is not provided."""
    resolved_id = contact_id
    existing = None

    if not resolved_id and email:
        existing = get_contact(email)
        if existing is not None:
            resolved_id = existing.get("id")

    if not resolved_id:
        if not email:
            raise ValueError("Either email or contact_id must be provided")
        return create_contact_global(
            email=email,
            first_name=first_name or "",
            last_name=last_name or "",
            unsubscribed=bool(unsubscribed),
        )

    payload: dict[str, Any] = {}
    if first_name is not None:
        payload["firstName"] = first_name
    if last_name is not None:
        payload["lastName"] = last_name
    if unsubscribed is not None:
        payload["unsubscribed"] = unsubscribed

    if not payload:
        return existing or get_contact(resolved_id) or {"id": resolved_id}

    response = _request("PATCH", f"/contacts/{resolved_id}", json=payload)
    response.raise_for_status()
    return response.json()


def sync_unsubscribe_contact(
    email: str,
    *,
    unsubscribed: bool = True,
    first_name: str = "",
    last_name: str = "",
) -> dict[str, Any]:
    """Ensure a Resend contact exists and reflect global unsubscribe state."""
    return update_contact_global(
        email=_normalize_email(email),
        first_name=first_name or None,
        last_name=last_name or None,
        unsubscribed=unsubscribed,
    )


# ── Email Sending ─────────────────────────────────────────

def send_email(
    to: str | list[str],
    subject: str,
    html: Optional[str] = None,
    from_addr: str = "Hedge Edge <hello@hedgedge.info>",
    reply_to: Optional[str] = None,
    tags: Optional[list[dict]] = None,
    text: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    include_unsubscribe: bool = True,
    respect_notion_unsubscribe: bool = False,
) -> dict[str, Any]:
    """Send a single email via Resend with one-click unsubscribe support."""
    recipients = _normalize_recipients(to)
    if not recipients:
        raise ValueError("At least one recipient is required")
    if not html and not text:
        raise ValueError("Either html or text content must be provided")

    _raise_if_blocked(recipients, respect_notion_unsubscribe)

    payload: dict[str, Any] = {
        "from": from_addr,
        "to": recipients,
        "subject": subject,
    }

    merged_headers = dict(headers or {})
    rendered_html = html
    rendered_text = text

    if include_unsubscribe:
        if len(recipients) != 1:
            raise ValueError("Unsubscribe-enabled sends must target exactly one recipient")
        unsubscribe_url = build_unsubscribe_url(recipients[0])
        rendered_html = _append_unsubscribe_html(rendered_html, unsubscribe_url)
        rendered_text = _append_unsubscribe_text(rendered_text, unsubscribe_url)

        lower_headers = {key.lower(): key for key in merged_headers}
        if "list-unsubscribe" not in lower_headers:
            merged_headers.update(build_unsubscribe_headers(recipients[0]))

    if rendered_html:
        payload["html"] = rendered_html
    if rendered_text:
        payload["text"] = rendered_text
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = _sanitize_tags(tags)
    if merged_headers:
        payload["headers"] = merged_headers

    response = _request("POST", "/emails", json=payload)
    response.raise_for_status()
    return response.json()


def get_email(email_id: str) -> dict[str, Any]:
    """Get details of a sent email by ID."""
    response = _request("GET", f"/emails/{email_id}")
    response.raise_for_status()
    return response.json()


def list_emails(limit: int = 100, *, timeout: int = 30) -> list[dict[str, Any]]:
    """List sent emails from Resend, following pagination until `limit` rows are collected."""
    if limit <= 0:
        return []

    collected: list[dict[str, Any]] = []
    next_cursor: Optional[str] = None

    while len(collected) < limit:
        batch_size = min(100, limit - len(collected))
        params: dict[str, Any] = {"limit": batch_size}
        if next_cursor:
            params["next"] = next_cursor

        response = _request("GET", "/emails", params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        batch = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(batch, list) or not batch:
            break

        collected.extend(batch)
        if not isinstance(data, dict) or not data.get("has_more"):
            break

        next_cursor = data.get("next")
        if not next_cursor:
            break

    return collected[:limit]


# ── Audiences ─────────────────────────────────────────────

def list_audiences() -> list[dict[str, Any]]:
    """List all audiences."""
    response = _request("GET", "/audiences")
    response.raise_for_status()
    data = response.json()
    return data.get("data", data) if isinstance(data, dict) else data


# ── Contacts (legacy audience helpers) ───────────────────

def list_contacts(audience_id: str) -> list[dict[str, Any]]:
    """List all contacts in an audience."""
    response = _request("GET", f"/audiences/{audience_id}/contacts", timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", data) if isinstance(data, dict) else data


def create_contact(
    audience_id: str,
    email: str,
    first_name: str = "",
    last_name: str = "",
    unsubscribed: bool = False,
) -> dict[str, Any]:
    """Add a contact to an audience."""
    payload: dict[str, Any] = {"email": _normalize_email(email), "unsubscribed": unsubscribed}
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    response = _request(
        "POST",
        f"/audiences/{audience_id}/contacts",
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def remove_contact(audience_id: str, contact_id: str) -> dict[str, Any]:
    """Remove a contact from an audience."""
    response = _request("DELETE", f"/audiences/{audience_id}/contacts/{contact_id}")
    response.raise_for_status()
    return response.json()


# ── Webhooks ──────────────────────────────────────────────

def list_webhooks() -> list[dict[str, Any]]:
    """List all webhooks."""
    response = _request("GET", "/webhooks")
    response.raise_for_status()
    data = response.json()
    return data.get("data", data) if isinstance(data, dict) else data


def create_webhook(
    url: str,
    events: list[str],
    name: str = "",
) -> dict[str, Any]:
    """Create a new webhook."""
    payload: dict[str, Any] = {"endpoint": url, "events": events}
    response = _request("POST", "/webhooks", json=payload)
    response.raise_for_status()
    return response.json()
