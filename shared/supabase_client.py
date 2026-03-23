"""
Hedge Edge — Supabase Client
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shared Supabase access for user data, subscriptions, and auth.

Usage:
    from shared.supabase_client import get_supabase, query_users, get_subscription
"""

import os
from typing import Optional
from shared.env_loader import load_env_for_source

load_env_for_source()

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError("pip install supabase — required for Supabase access")


# Two separate caches — anon key must never bleed into service-role slots and vice-versa.
_anon_client: Optional[Client] = None
_service_client: Optional[Client] = None


def get_supabase(use_service_role: bool = False) -> Client:
    """Return a cached Supabase client.

    SECURITY: two distinct caches ensure anon and service-role clients are
    never confused, regardless of call order.
    """
    global _anon_client, _service_client
    url = os.getenv("SUPABASE_URL")

    if use_service_role:
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        if _service_client is None:
            _service_client = create_client(url, key)
        return _service_client
    else:
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        if _anon_client is None:
            _anon_client = create_client(url, key)
        return _anon_client


def query_users(limit: int = 100, offset: int = 0) -> list[dict]:
    """Query user profiles."""
    sb = get_supabase(use_service_role=True)
    return sb.table("profiles").select("*").range(offset, offset + limit - 1).execute().data


def get_subscription(user_id: str) -> Optional[dict]:
    """Get a user's current subscription."""
    sb = get_supabase(use_service_role=True)
    result = sb.table("subscriptions").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def count_active_subs() -> int:
    """Count active subscriptions."""
    sb = get_supabase(use_service_role=True)
    result = sb.table("subscriptions").select("id", count="exact").eq("status", "active").execute()
    return result.count or 0


def get_user_by_email(email: str) -> Optional[dict]:
    """Lookup an auth user by email using the service-role admin API."""
    sb = get_supabase(use_service_role=True)
    target = email.strip().lower()
    users_resp = sb.auth.admin.list_users()
    users = users_resp if isinstance(users_resp, list) else getattr(users_resp, "users", [])
    for user in users:
        user_email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
        if user_email and user_email.strip().lower() == target:
            if isinstance(user, dict):
                return user
            if hasattr(user, "model_dump"):
                return user.model_dump()
            return {
                "id": getattr(user, "id", None),
                "email": user_email,
                "user_metadata": getattr(user, "user_metadata", None),
                "app_metadata": getattr(user, "app_metadata", None),
                "created_at": getattr(user, "created_at", None),
            }
    return None


# ── UTM / Pageview Helpers ────────────────────────────

def query_page_views(
    days: int = 7,
    utm_source: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:
    """
    Query the page_views table. Columns:
      id, path, referrer, utm_source, utm_medium, utm_campaign,
      user_agent, country, created_at
    """
    from datetime import datetime, timezone, timedelta
    sb = get_supabase(use_service_role=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = sb.table("page_views").select("*").gte("created_at", cutoff)
    if utm_source:
        q = q.eq("utm_source", utm_source)
    if utm_campaign:
        q = q.eq("utm_campaign", utm_campaign)
    return q.order("created_at", desc=True).limit(limit).execute().data or []


def query_user_attribution(
    days: int = 30,
    utm_source: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """
    Query the user_attribution table. Columns:
      id, user_id, utm_source, utm_medium, utm_campaign, utm_content,
      utm_term, ref, landing_url, landed_at, signup_method, signed_up_at, created_at
    """
    from datetime import datetime, timezone, timedelta
    sb = get_supabase(use_service_role=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = sb.table("user_attribution").select("*").gte("created_at", cutoff)
    if utm_source:
        q = q.eq("utm_source", utm_source)
    return q.order("created_at", desc=True).limit(limit).execute().data or []