"""
Hedge Edge ERP — Shared Notion Client
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Single source of truth for all database IDs and Notion API access.
Every agent's execution script imports from here.

Usage:
    from shared.notion_client import get_notion, DATABASES, add_row, query_db
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime, date
from typing import Any, Optional

import requests as _requests_lib
from notion_client import Client
from shared.env_loader import load_env_for_source

# Load root .env first, then department and subdepartment resource overrides if available.
load_env_for_source()


logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Notion Rate Limiter (3 req/s per integration)
# ──────────────────────────────────────────────
class _NotionRateLimiter:
    """
    Token-bucket rate limiter for Notion API.
    Notion allows 3 requests/second per integration token.
    We target 2.8 req/s to maintain a small safety margin.
    Thread-safe for concurrent usage.
    """
    _MAX_RPS = 2.8           # Requests per second (safety margin below 3)
    _MIN_INTERVAL = 1.0 / _MAX_RPS  # ~0.357 s between requests
    _RETRY_MAX = 5           # Max retries on 429
    _RETRY_BASE = 1.0        # Base backoff seconds

    def __init__(self):
        self._lock = threading.Lock()
        self._last_request_time = 0.0
        self.total_requests = 0
        self.total_retries = 0
        self.total_rate_limits = 0

    def wait(self) -> None:
        """Block until it's safe to make the next Notion API request."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._MIN_INTERVAL:
                sleep_for = self._MIN_INTERVAL - elapsed
                time.sleep(sleep_for)
            self._last_request_time = time.monotonic()
            self.total_requests += 1

    def stats(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "total_retries": self.total_retries,
            "total_rate_limits": self.total_rate_limits,
        }


_rate_limiter = _NotionRateLimiter()


def notion_rate_limiter_stats() -> dict:
    """Return rate limiter statistics for diagnostics."""
    return _rate_limiter.stats()


def notion_request(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    timeout: int = 30,
) -> _requests_lib.Response:
    """
    Make a rate-limited HTTP request to the Notion API.
    Automatically retries on 429 (Too Many Requests) with exponential backoff
    using the Retry-After header when provided.

    Args:
        method: HTTP method ('get', 'post', 'patch', 'delete')
        url: Full Notion API URL
        headers: Request headers (Authorization + Notion-Version)
        json: Request body
        timeout: Request timeout in seconds

    Returns:
        requests.Response object

    Raises:
        requests.HTTPError: After exhausting retries or on non-429 errors
    """
    for attempt in range(_rate_limiter._RETRY_MAX):
        _rate_limiter.wait()
        try:
            resp = getattr(_requests_lib, method.lower())(
                url, headers=headers, json=json, timeout=timeout,
            )
        except (_requests_lib.exceptions.ReadTimeout, _requests_lib.exceptions.ConnectionError) as exc:
            if attempt < _rate_limiter._RETRY_MAX - 1:
                backoff = _rate_limiter._RETRY_BASE * (2 ** attempt)
                logger.warning(
                    "Notion timeout/connection error (attempt %d/%d) — retrying in %.1fs: %s",
                    attempt + 1, _rate_limiter._RETRY_MAX, backoff, exc,
                )
                print(f"  ⏳ Notion timeout — waiting {backoff:.1f}s (attempt {attempt + 1}/{_rate_limiter._RETRY_MAX})")
                time.sleep(backoff)
                continue
            raise

        if resp.status_code != 429:
            return resp

        # ── Handle 429 rate limit ──
        _rate_limiter.total_rate_limits += 1
        _rate_limiter.total_retries += 1
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                backoff = float(retry_after)
            except ValueError:
                backoff = _rate_limiter._RETRY_BASE * (2 ** attempt)
        else:
            backoff = _rate_limiter._RETRY_BASE * (2 ** attempt)

        logger.warning(
            "Notion 429 rate-limited (attempt %d/%d) — retrying in %.1fs",
            attempt + 1, _rate_limiter._RETRY_MAX, backoff,
        )
        print(f"  ⏳ Notion rate limit hit — waiting {backoff:.1f}s (attempt {attempt + 1}/{_rate_limiter._RETRY_MAX})")
        time.sleep(backoff)

    # Exhausted retries — raise the last 429
    resp.raise_for_status()
    return resp  # unreachable, but keeps type checkers happy


# ──────────────────────────────────────────────
# Notion Client Singleton
# ──────────────────────────────────────────────
_client: Optional[Client] = None
_NOTION_VERSION = "2022-06-28"
_API_BASE = "https://api.notion.com/v1"

def get_notion() -> Client:
    """Return a cached Notion client. Reads NOTION_API_KEY from .env."""
    global _client
    if _client is None:
        token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        if not token:
            # Fallback: read from mcp.json
            mcp_path = os.path.join(_ws_root, ".vscode", "mcp.json")
            if os.path.exists(mcp_path):
                with open(mcp_path) as f:
                    mcp = json.load(f)
                token = (
                    mcp.get("servers", {})
                    .get("makenotion/notion-mcp-server", {})
                    .get("env", {})
                    .get("NOTION_TOKEN")
                )
            if not token:
                raise RuntimeError(
                    "No Notion token found. Set NOTION_API_KEY in .env "
                    "or NOTION_TOKEN in .vscode/mcp.json"
                )
        # Pin to 2022-06-28 — the 2025-09-03 version removes properties from
        # databases.retrieve(), breaking schema-aware add_row/update_row.
        import httpx as _httpx
        _client = Client(
            auth=token,
            notion_version="2022-06-28",
            client=_httpx.Client(timeout=30.0),
        )
    return _client


# ──────────────────────────────────────────────
# Database ID Registry
# ──────────────────────────────────────────────
DATABASES = {
    # Strategy & OKRs — Business Strategist Agent
    "okrs":                  "a4223c40-d665-46d8-811f-7997e968186c",
    "competitors":           "f9d5ed01-bf99-407d-a653-fc6385627fcf",
    "strategic_initiatives": "509fe321-8b9c-4b7c-95ba-553149c364fb",

    # Finance — Finance Agent
    "mrr_tracker":           "de91e0f1-6ab8-4969-906b-c913b3853415",
    "expense_log":           "8252c8ec-96bb-4700-8944-b817061d7042",
    "ib_commissions":        "b7185477-1109-478b-8aae-dd200f1a9de9",
    "pnl_snapshots":         "468c0b6b-5f07-4e39-802c-7515e9b7d266",

    # Sales Pipeline — Sales Agent
    "leads_crm":             "30b652ea-6c6d-81e5-838b-c71135e14982",
    "demo_log":              "88ab6647-2bb2-41b0-a422-d304f0bd4ccd",
    "proposals":             "85177f10-8b2b-43ae-8adc-992468f48ebe",

    # Marketing — Marketing Agent
    "campaigns":             "38566e9d-6078-4d4c-af89-fca0c97613e1",
    "email_sequences":       "2258cf16-a77a-4ee5-a710-ce83b2ba792c",
    "email_templates":       "2258cf16-a77a-4ee5-a710-ce83b2ba792c",   # alias → email_sequences
    "templates_archive":     "31c652ea-6c6d-809b-ad9f-e7e3a8d6b0a4",
    "email_sends":           "30b652ea-6c6d-81e5-838b-c71135e14982",
    "email_leads":           "30b652ea-6c6d-81e5-838b-c71135e14982",   # alias → email_sends
    "seo_keywords":          "4927cd6f-dad4-4023-97c7-93d4e3c78ac9",
    "landing_page_tests":    "8bc02ab1-6ba4-4b38-9b1d-69ea61a5040b",
    "email_logs":            "312652ea-6c6d-8168-9180-dd5996a838a8",
    "lead_replies":          "311652ea-6c6d-810d-9952-cfb7d2fa71d3",
    "link_tracking":         "313652ea-6c6d-8116-89e4-d03921377a35",
    "beta_waitlist":         "329652ea-6c6d-81be-8576-db98a68efd70",

    # Content — Content Engine Agent
    "content_calendar":      "8d6444ad-6423-49e6-9d38-23237cb9a7d9",
    "video_pipeline":        "262db30b-63e6-4d0b-81c9-1bcbc99b4bf5",

    # Product — Product Agent
    "feature_roadmap":       "fdf70275-86c0-48e3-ae32-ddd9e1f3c2ad",
    "bug_tracker":           "43cd27e0-0b6f-41b6-9e8d-08e7bc92eb81",
    "release_log":           "1bd5e214-bed4-4430-b9a9-e0faee499183",

    # Community — Community Manager Agent
    "feedback":              "e853ffdc-d6dc-4605-a777-839c58827494",
    "support_tickets":       "af770b06-1cc5-4b9a-92bf-283d94bd08b6",
    "community_events":      "aed661c2-2be1-464d-a305-0816691a30f2",

    # Analytics — Analytics Agent
    "kpi_snapshots":         "bd20dc16-ab02-4559-a77c-68210d41a5de",
    "funnel_metrics":        "7967541b-3ff5-4ab8-9c98-6c6a3d87e79e",

    # Partnerships — Business Strategist Agent
    "partnerships":          "0638ff88-4ab5-4260-9a63-91f23f7d89f0",

    # Orchestrator — Task Log
    "task_log":              "d4a7ce17-b1ff-44ee-9e99-e09bd922ff28",
}


# ──────────────────────────────────────────────
# Agent Access Control
# ──────────────────────────────────────────────
AGENT_ACCESS = {
    "business_strategist": {
        "write": ["okrs", "competitors", "strategic_initiatives", "partnerships"],
        "read":  ["kpi_snapshots", "mrr_tracker", "partnerships", "funnel_metrics"],
    },
    "finance": {
        "write": ["mrr_tracker", "expense_log", "ib_commissions", "pnl_snapshots"],
        "read":  ["leads_crm", "kpi_snapshots"],
    },
    "sales": {
        "write": ["leads_crm", "demo_log", "proposals", "link_tracking"],
        "read":  ["mrr_tracker", "feedback", "beta_waitlist"],
    },
    "marketing": {
        "write": ["campaigns", "email_sequences", "templates_archive", "email_sends", "seo_keywords", "landing_page_tests", "email_logs", "lead_replies", "link_tracking", "beta_waitlist"],
        "read":  ["leads_crm", "kpi_snapshots", "content_calendar"],
    },
    "content_engine": {
        "write": ["content_calendar", "video_pipeline", "link_tracking"],
        "read":  ["seo_keywords", "campaigns", "release_log"],
    },
    "product": {
        "write": ["feature_roadmap", "bug_tracker", "release_log"],
        "read":  ["feedback", "support_tickets", "kpi_snapshots"],
    },
    "community_manager": {
        "write": ["feedback", "support_tickets", "community_events", "link_tracking"],
        "read":  ["release_log", "content_calendar"],
    },
    "analytics": {
        "write": ["kpi_snapshots", "funnel_metrics", "link_tracking"],
        "read":  list(DATABASES.keys()),  # Analytics reads everything
    },
    "orchestrator": {
        "write": ["task_log"],
        "read":  list(DATABASES.keys()),  # Orchestrator reads everything
    },
}


# ──────────────────────────────────────────────
# Helper: Property Builders
# ──────────────────────────────────────────────

def _prop_title(value: str) -> dict:
    return {"title": [{"text": {"content": str(value)}}]}

def _prop_rich_text(value: str) -> dict:
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}

def _prop_number(value: float) -> dict:
    return {"number": value}

def _prop_select(value: str) -> dict:
    return {"select": {"name": str(value)}}

def _prop_status(value: str) -> dict:
    return {"status": {"name": str(value)}}

def _prop_multi_select(values: list[str]) -> dict:
    return {"multi_select": [{"name": str(v)} for v in values]}

def _prop_date(value) -> dict | None:
    """Accept ISO date string like '2026-02-15' or datetime object. Returns None for empty/falsy values."""
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    if not value:
        return None  # Notion rejects empty date strings
    return {"date": {"start": str(value)}}

def _prop_checkbox(value: bool) -> dict:
    return {"checkbox": value}

def _prop_url(value: str) -> dict:
    return {"url": str(value)}

def _prop_email(value: str) -> dict:
    return {"email": str(value)}

def _prop_relation(value) -> dict:
    """Accept a page-ID string or list of page-ID strings."""
    if isinstance(value, str):
        return {"relation": [{"id": value}]}
    if isinstance(value, list):
        return {"relation": [{"id": v} for v in value]}
    return {"relation": []}


# Auto-builder: infers property type from Python value type
PROP_BUILDERS = {
    "title":        _prop_title,
    "rich_text":    _prop_rich_text,
    "number":       _prop_number,
    "select":       _prop_select,
    "status":       _prop_status,
    "multi_select": _prop_multi_select,
    "date":         _prop_date,
    "checkbox":     _prop_checkbox,
    "url":          _prop_url,
    "email":        _prop_email,
    "relation":     _prop_relation,
}


# ──────────────────────────────────────────────
# Schema Cache — avoid refetching on every write
# ──────────────────────────────────────────────
_schema_cache: dict[str, dict] = {}       # db_key → properties dict
_schema_cache_ts: dict[str, float] = {}   # db_key → monotonic timestamp
_SCHEMA_TTL = 300  # 5 minutes


def _get_schema(db_key: str) -> dict:
    """Return database schema, using a 5-minute cache to reduce API calls."""
    now = time.monotonic()
    if db_key in _schema_cache and (now - _schema_cache_ts.get(db_key, 0)) < _SCHEMA_TTL:
        return _schema_cache[db_key]

    notion = get_notion()
    db_id = DATABASES.get(db_key)
    if not db_id:
        raise ValueError(f"Unknown database key: {db_key}")

    _rate_limiter.wait()  # Count schema fetch toward rate limit
    schema = notion.databases.retrieve(database_id=db_id)["properties"]
    _schema_cache[db_key] = schema
    _schema_cache_ts[db_key] = now
    return schema


def invalidate_schema_cache(db_key: Optional[str] = None) -> None:
    """Clear cached schema for one or all databases."""
    if db_key:
        _schema_cache.pop(db_key, None)
        _schema_cache_ts.pop(db_key, None)
    else:
        _schema_cache.clear()
        _schema_cache_ts.clear()


# ──────────────────────────────────────────────
# Core API: add_row
# ──────────────────────────────────────────────

def add_row(db_key: str, properties: dict[str, Any]) -> dict:
    """
    Add a row to a Notion database.

    Args:
        db_key: Key from DATABASES dict (e.g., 'mrr_tracker')
        properties: Dict of {property_name: value}
                    Values are auto-wrapped based on the database schema.

    Returns:
        The created Notion page object.

    Example:
        add_row("mrr_tracker", {
            "Date": "2026-02-15",
            "MRR": 1500.00,
            "ARR": 18000.00,
            "New Subs": 12,
            "Churned Subs": 2,
            "Churn Rate": 0.03,
        })
    """
    notion = get_notion()
    db_id = DATABASES.get(db_key)
    if not db_id:
        raise ValueError(f"Unknown database key: {db_key}. Available: {list(DATABASES.keys())}")

    # Use cached schema to avoid an extra API call per write
    schema = _get_schema(db_key)

    notion_props = {}
    for prop_name, value in properties.items():
        if prop_name not in schema:
            print(f"  ⚠️  Skipping unknown property '{prop_name}' in {db_key}")
            continue
        prop_type = schema[prop_name]["type"]
        builder = PROP_BUILDERS.get(prop_type)
        if builder:
            built = builder(value)
            if built is not None:
                notion_props[prop_name] = built
        else:
            print(f"  ⚠️  Unsupported property type '{prop_type}' for '{prop_name}'")

    _rate_limiter.wait()
    page = notion.pages.create(
        parent={"type": "database_id", "database_id": db_id},
        properties=notion_props,
    )
    return page


# ──────────────────────────────────────────────
# Core API: query_db
# ──────────────────────────────────────────────

def query_db(
    db_key: str,
    filter: Optional[dict] = None,
    sorts: Optional[list[dict]] = None,
    page_size: int = 100,
) -> list[dict]:
    """
    Query a Notion database and return rows as simplified dicts.

    Args:
        db_key: Key from DATABASES dict
        filter: Notion filter object (optional)
        sorts: Notion sorts array (optional)
        page_size: Max results per page

    Returns:
        List of dicts with property names as keys and extracted values.
    """
    db_id = DATABASES.get(db_key)
    if not db_id:
        raise ValueError(f"Unknown database key: {db_key}")

    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
    }

    body: dict = {"page_size": page_size}
    if filter:
        body["filter"] = filter
    if sorts:
        body["sorts"] = sorts

    results = []
    while True:
        resp = notion_request(
            "post",
            f"{_API_BASE}/databases/{db_id}/query",
            headers=headers, json=body, timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data["results"]:
            row = {"_id": page["id"], "_url": page["url"]}
            for prop_name, prop_data in page["properties"].items():
                row[prop_name] = _extract_value(prop_data)
            results.append(row)
        if not data.get("has_more"):
            break
        body["start_cursor"] = data["next_cursor"]
    return results


def _extract_value(prop: dict) -> Any:
    """Extract a plain Python value from a Notion property object."""
    t = prop["type"]
    if t == "title":
        return "".join(rt["plain_text"] for rt in prop.get("title", []))
    elif t == "rich_text":
        return "".join(rt["plain_text"] for rt in prop.get("rich_text", []))
    elif t == "number":
        return prop.get("number")
    elif t == "select":
        sel = prop.get("select")
        return sel["name"] if sel else None
    elif t == "multi_select":
        return [s["name"] for s in prop.get("multi_select", [])]
    elif t == "date":
        d = prop.get("date")
        return d["start"] if d else None
    elif t == "checkbox":
        return prop.get("checkbox", False)
    elif t == "url":
        return prop.get("url")
    elif t == "email":
        return prop.get("email")
    elif t == "formula":
        f = prop.get("formula", {})
        return f.get(f.get("type"))
    elif t == "rollup":
        r = prop.get("rollup", {})
        return r.get(r.get("type"))
    elif t == "status":
        s = prop.get("status")
        return s["name"] if s else None
    else:
        return None


# ──────────────────────────────────────────────
# Core API: update_row
# ──────────────────────────────────────────────

def update_row(page_id: str, db_key: str, properties: dict[str, Any]) -> dict:
    """
    Update an existing row in a Notion database.

    Args:
        page_id: The Notion page ID of the row to update
        db_key: Database key (for schema lookup)
        properties: Dict of {property_name: new_value}

    Returns:
        The updated Notion page object.
    """
    notion = get_notion()
    db_id = DATABASES.get(db_key)
    if not db_id:
        raise ValueError(f"Unknown database key: {db_key}")

    # Use cached schema to avoid an extra API call per update
    schema = _get_schema(db_key)

    notion_props = {}
    for prop_name, value in properties.items():
        if prop_name not in schema:
            continue
        prop_type = schema[prop_name]["type"]
        builder = PROP_BUILDERS.get(prop_type)
        if builder:
            notion_props[prop_name] = builder(value)

    _rate_limiter.wait()
    return notion.pages.update(page_id=page_id, properties=notion_props)


# ──────────────────────────────────────────────
# Utility: log_task
# ──────────────────────────────────────────────

def log_task(
    agent: str,
    task: str,
    status: str = "Complete",
    priority: str = "P2",
    output_summary: str = "",
    error: str = "",
) -> dict:
    """Log an agent task execution to the Orchestrator Task Log."""
    return add_row("task_log", {
        "Task":           task,
        "Agent":          agent,
        "Status":         status,
        "Priority":       priority,
        "Created":        datetime.now().isoformat(),
        "Completed":      datetime.now().isoformat() if status == "Complete" else "",
        "Output Summary": output_summary[:2000],
        "Error":          error[:2000],
    })
