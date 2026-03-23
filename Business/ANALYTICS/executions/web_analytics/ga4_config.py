"""Path setup and shared imports for Hedge Edge GA4 access."""

import sys

_WS_ROOT = r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

# Re-export everything from the shared GA4 client
from shared.google_analytics_client import (  # noqa: F401
    run_report,
    get_realtime,
    get_page_views,
    get_sessions,
    get_visitors,
    get_new_users,
    get_avg_session_duration,
    get_bounce_rate,
    get_conversions,
    get_top_pages,
    get_traffic_sources,
    get_utm_campaigns,
    get_device_breakdown,
    get_geo_breakdown,
    get_campaign_breakdown,
    get_daily_website_summary,
    send_event,
    send_conversion,
    ping,
)
