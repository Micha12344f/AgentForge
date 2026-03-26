"""
Google Analytics 4 (GA4) Data API client.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides GA4 reporting, real-time, and Measurement Protocol functions.

Uses:
    - GA4 Data API (google-analytics-data) for reporting
    - GA4 Measurement Protocol for event sending

Env vars:
    GA4_PROPERTY_ID          — numeric property ID
    GA4_MEASUREMENT_ID       — G-XXXXXXXXXX
    GA4_API_SECRET           — Measurement Protocol secret
    GOOGLE_SERVICE_ACCOUNT_JSON — service account JSON blob
"""

import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")
_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
_API_SECRET = os.getenv("GA4_API_SECRET", "")

# ── Service-account auth via google.oauth2 ─────────────────────────
_credentials = None


def _get_credentials():
    global _credentials
    if _credentials is not None:
        return _credentials
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON must be set in .env "
            "(full JSON blob or file path)"
        )
    # Allow value to be a file path
    if os.path.isfile(raw):
        with open(raw) as f:
            raw = f.read()
    try:
        from google.oauth2 import service_account
        info = json.loads(raw)
        _credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        return _credentials
    except ImportError:
        raise ImportError(
            "pip install google-auth google-analytics-data — "
            "required for GA4 reporting"
        )


def _get_client():
    """Return a cached BetaAnalyticsDataClient."""
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except ImportError:
        raise ImportError(
            "pip install google-analytics-data — required for GA4 reporting"
        )
    return BetaAnalyticsDataClient(credentials=_get_credentials())


def _property_path() -> str:
    if not _PROPERTY_ID:
        raise RuntimeError("GA4_PROPERTY_ID must be set in .env")
    return f"properties/{_PROPERTY_ID}"


# ── Core Reporting ────────────────────────────────────────────────

def run_report(
    date_ranges: list[dict[str, str]],
    dimensions: list[str],
    metrics: list[str],
    *,
    dimension_filter: Optional[dict] = None,
    order_bys: Optional[list[dict]] = None,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    """Execute a GA4 Data API v1beta runReport request."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
    )
    client = _get_client()
    request = RunReportRequest(
        property=_property_path(),
        date_ranges=[DateRange(**dr) for dr in date_ranges],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        limit=limit,
    )
    response = client.run_report(request)
    rows = []
    dim_headers = [h.name for h in response.dimension_headers]
    met_headers = [h.name for h in response.metric_headers]
    for row in response.rows:
        entry = {}
        for i, dv in enumerate(row.dimension_values):
            entry[dim_headers[i]] = dv.value
        for i, mv in enumerate(row.metric_values):
            entry[met_headers[i]] = mv.value
        rows.append(entry)
    return rows


def _simple_metric(
    metric_name: str,
    start: str = "7daysAgo",
    end: str = "today",
) -> int:
    """Pull a single aggregate metric."""
    rows = run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=[],
        metrics=[metric_name],
    )
    if rows and metric_name in rows[0]:
        try:
            return int(rows[0][metric_name])
        except (ValueError, TypeError):
            return 0
    return 0


def get_page_views(start: str = "7daysAgo", end: str = "today") -> int:
    return _simple_metric("screenPageViews", start, end)


def get_sessions(start: str = "7daysAgo", end: str = "today") -> int:
    return _simple_metric("sessions", start, end)


def get_visitors(start: str = "7daysAgo", end: str = "today") -> int:
    return _simple_metric("totalUsers", start, end)


def get_new_users(start: str = "7daysAgo", end: str = "today") -> int:
    return _simple_metric("newUsers", start, end)


def get_avg_session_duration(start: str = "7daysAgo", end: str = "today") -> float:
    rows = run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=[],
        metrics=["averageSessionDuration"],
    )
    if rows:
        try:
            return float(rows[0].get("averageSessionDuration", 0))
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def get_bounce_rate(start: str = "7daysAgo", end: str = "today") -> float:
    rows = run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=[],
        metrics=["bounceRate"],
    )
    if rows:
        try:
            return float(rows[0].get("bounceRate", 0))
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def get_conversions(start: str = "7daysAgo", end: str = "today") -> int:
    return _simple_metric("conversions", start, end)


def get_top_pages(
    start: str = "7daysAgo",
    end: str = "today",
    limit: int = 10,
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["pagePath"],
        metrics=["screenPageViews", "totalUsers"],
        limit=limit,
    )


def get_traffic_sources(
    start: str = "7daysAgo",
    end: str = "today",
    limit: int = 10,
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["sessionSource"],
        metrics=["sessions", "totalUsers"],
        limit=limit,
    )


def get_utm_campaigns(
    start: str = "7daysAgo",
    end: str = "today",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["sessionCampaignName"],
        metrics=["sessions", "totalUsers", "screenPageViews"],
        limit=limit,
    )


def get_device_breakdown(
    start: str = "7daysAgo",
    end: str = "today",
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["deviceCategory"],
        metrics=["sessions", "totalUsers"],
    )


def get_geo_breakdown(
    start: str = "7daysAgo",
    end: str = "today",
    limit: int = 10,
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["country"],
        metrics=["sessions", "totalUsers"],
        limit=limit,
    )


def get_campaign_breakdown(
    start: str = "7daysAgo",
    end: str = "today",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return run_report(
        date_ranges=[{"start_date": start, "end_date": end}],
        dimensions=["sessionCampaignName", "sessionSourceMedium"],
        metrics=["sessions", "totalUsers", "screenPageViews"],
        limit=limit,
    )


# ── Daily Summary (main entry used by analytics scripts) ──────────

def get_daily_website_summary(
    report_date: Optional[date] = None,
) -> dict[str, Any]:
    """Return a high-level summary dict for one day.

    Keys: pageviews, sessions, visitors, new_users, bounce_rate,
          avg_session_duration, top_pages, traffic_sources, utm_campaigns,
          devices, geo
    """
    d = report_date or (datetime.now(timezone.utc) - timedelta(days=1)).date()
    ds = d.isoformat()
    return {
        "date": ds,
        "pageviews": get_page_views(ds, ds),
        "sessions": get_sessions(ds, ds),
        "visitors": get_visitors(ds, ds),
        "new_users": get_new_users(ds, ds),
        "bounce_rate": get_bounce_rate(ds, ds),
        "avg_session_duration": get_avg_session_duration(ds, ds),
        "top_pages": get_top_pages(ds, ds, limit=5),
        "traffic_sources": get_traffic_sources(ds, ds, limit=5),
        "utm_campaigns": get_utm_campaigns(ds, ds, limit=5),
        "devices": get_device_breakdown(ds, ds),
        "geo": get_geo_breakdown(ds, ds, limit=5),
    }


# ── Real-time ─────────────────────────────────────────────────────

def get_realtime() -> dict[str, Any]:
    """Fetch GA4 real-time active users."""
    try:
        from google.analytics.data_v1beta.types import (
            RunRealtimeReportRequest,
            Metric,
        )
        client = _get_client()
        request = RunRealtimeReportRequest(
            property=_property_path(),
            metrics=[Metric(name="activeUsers")],
        )
        response = client.run_realtime_report(request)
        active = 0
        if response.rows:
            active = int(response.rows[0].metric_values[0].value)
        return {"active_users": active}
    except Exception as e:
        return {"active_users": 0, "error": str(e)}


# ── Measurement Protocol (event sending) ──────────────────────────

def _mp_url() -> str:
    return (
        f"https://www.google-analytics.com/mp/collect"
        f"?measurement_id={_MEASUREMENT_ID}&api_secret={_API_SECRET}"
    )


def send_event(
    client_id: str,
    event_name: str,
    params: Optional[dict[str, Any]] = None,
) -> bool:
    """Send a custom event via Measurement Protocol."""
    if not _MEASUREMENT_ID or not _API_SECRET:
        return False
    payload = {
        "client_id": client_id,
        "events": [{"name": event_name, "params": params or {}}],
    }
    try:
        r = requests.post(_mp_url(), json=payload, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False


def send_conversion(
    client_id: str,
    conversion_name: str,
    value: float = 0,
    currency: str = "USD",
) -> bool:
    """Send a conversion event via Measurement Protocol."""
    return send_event(
        client_id,
        conversion_name,
        {"value": value, "currency": currency},
    )


# ── Health check ──────────────────────────────────────────────────

def ping() -> dict[str, Any]:
    """Quick health check — verifies credentials and property access."""
    try:
        pv = get_page_views("1daysAgo", "today")
        return {"status": "ok", "pageviews_today": pv}
    except Exception as e:
        return {"status": "error", "error": str(e)}
