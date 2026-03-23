---
name: google-analytics
description: |
  Reads and surfaces website traffic and engagement data from Google Analytics 4
  (GA4) via the Data API. Provides daily summaries, traffic source analysis,
  landing page performance, device/geo breakdowns, UTM campaign attribution,
  daily trend data, and acquisition channel grouping.
  
  IMPORTANT: GA4 is used for traffic and behavioural analytics ONLY.
  Conversions are tracked via Supabase user_attribution (see conversion_tracker.py).
  The GA4 sign_up event is unreliable and must never be used as a conversion count.
---

# Google Analytics (GA4) Directive

## Conversion Source of Truth

> **GA4 `sign_up` is NOT a valid conversion indicator.**
>
> The GA4 `sign_up` event fires from client-side JavaScript in `Home.tsx → handleBetaAccept`.
> It is unreliable because:
> - Ad-blockers and privacy browsers suppress gtag.js entirely.
> - A stale `sign_up` call exists in `Auth.tsx` (not routed, but still in the bundle).
> - GA4 consistently undercounts vs server-side Supabase records.
>
> **Always use `conversion_tracker.py` → Supabase `user_attribution`** for conversion counts.
> GA4 `sign_up` data may be shown for funnel-shape analysis only, and must be labelled
> "GA4 (indicative only, undercounts)" whenever displayed.

## What GA4 IS Used For

| Use Case | GA4 Functions | Notes |
|----------|--------------|-------|
| Traffic volume | `get_sessions`, `get_visitors`, `get_page_views` | Reliable |
| User engagement | `get_bounce_rate`, `get_avg_session_duration` | Reliable |
| Traffic sources | `get_traffic_sources`, `get_utm_campaigns` | Reliable |
| Landing page performance | `get_top_pages` | Reliable |
| Device/geo analysis | `get_device_breakdown`, `get_geo_breakdown` | Reliable |
| Channel grouping | `run_report` with `sessionDefaultChannelGrouping` | Reliable |
| Daily trends | `run_report` with `date` dimension | Reliable |
| **Conversion counts** | ~~`get_conversions`~~ | **DO NOT USE** — use Supabase instead |

## Execution Scripts

All data-access scripts live in:
`Hedge Edge Business/IDE 1/agents/ANALYTICS/.agents/GROWTH ANALYTICS/Google Analytics/execution/`

| File | Purpose |
|------|---------|
| `config.py` | Path setup; loads `.env` and re-exports GA4 client functions |
| `report.py` | Pulls and prints a comprehensive GA4 website analytics report |
| `trends.py` | Pulls daily trend data over configurable date ranges |

---

## How to Access Metrics

### Shared client

All scripts import from `config.py` which re-exports functions from the
GA4 client located in the landing-page-optimization skill (the canonical copy).

```python
from execution.config import get_daily_website_summary, run_report
summary = get_daily_website_summary('2026-03-08')
```

---

### Available Functions

| Function | Returns | Notes |
|----------|---------|-------|
| `get_page_views(start, end)` | `int` | Total page views |
| `get_sessions(start, end)` | `int` | Total sessions |
| `get_visitors(start, end)` | `int` | Unique visitors (totalUsers) |
| `get_new_users(start, end)` | `int` | New users |
| `get_avg_session_duration(start, end)` | `float` | Avg session duration (seconds) |
| `get_bounce_rate(start, end)` | `float` | Bounce rate (0–1) |
| `get_conversions(start, end)` | `int` | Conversion events |
| `get_top_pages(start, end, limit)` | `list[dict]` | Top pages by pageviews |
| `get_traffic_sources(start, end, limit)` | `list[dict]` | Source/medium breakdown |
| `get_utm_campaigns(start, end, limit)` | `list[dict]` | UTM campaign breakdown |
| `get_device_breakdown(start, end)` | `list[dict]` | Desktop/mobile/tablet split |
| `get_geo_breakdown(start, end, limit)` | `list[dict]` | Country breakdown |
| `get_campaign_breakdown(start, end, limit)` | `list[dict]` | Campaigns × source/medium |
| `get_daily_website_summary(date)` | `dict` | Full daily snapshot |
| `get_realtime(dims, metrics)` | `list[dict]` | Real-time active users |
| `run_report(dims, metrics, ...)` | `list[dict]` | Generic GA4 Data API report |
| `send_event(name, params, ...)` | `bool` | Send event via Measurement Protocol |
| `ping()` | `dict` | Health check |

---

## Date Formats

- Absolute: `'YYYY-MM-DD'` (e.g. `'2026-03-08'`)
- Relative: `'today'`, `'yesterday'`, `'7daysAgo'`, `'30daysAgo'`

---

## Hedge Edge GA4 Event Taxonomy

Events confirmed firing in production (verified via Playwright network interception on localhost):

| Event name | Source | Trigger | Custom params |
|---|---|---|---|
| `page_view` | GTM auto | Every SPA navigation | `dl` (document location), `dt` (title) |
| `scroll` | GTM Enhanced Measurement | 90% scroll depth | `epn.percent_scrolled=90` |
| `form_start` | GTM Enhanced Measurement | First keypress in any form | `ep.form_destination`, `epn.form_length`, `ep.first_field_type` |
| `sign_up` | `Home.tsx → handleBetaAccept` | Successful `/api/claim-beta` POST | `ep.method=email`, `ep.form=beta_claim` |

> **Key fact**: `Auth.tsx` contains a stale `sign_up` call but is **not in any route** in `App.tsx`. The only active conversion event is the one in `Home.tsx → handleBetaAccept`. **Do not use GA4 sign_up as a conversion metric.** Use `conversion_tracker.py` → Supabase `user_attribution` for all conversion reporting.

### Querying `sign_up` for funnel-shape analysis ONLY

If you need to show frontend funnel shape (form_start → sign_up), label the output clearly:

```python
from execution.config import run_report

# Daily sign_up conversions for last 30 days
rows = run_report(
    dimensions=["date", "eventName"],
    metrics=["eventCount"],
    start_date="30daysAgo",
    end_date="today",
    dimension_filter={"fieldName": "eventName", "stringFilter": {"value": "sign_up"}},
)
for r in rows:
    print(r["date"], r["eventCount"])
```

### Querying `form_start` → `sign_up` funnel

```python
# Top-of-funnel: how many started the beta form
form_starts = run_report(
    dimensions=["date"],
    metrics=["eventCount"],
    start_date="30daysAgo",
    end_date="today",
    dimension_filter={"fieldName": "eventName", "stringFilter": {"value": "form_start"}},
)

# Bottom of funnel: how many completed
sign_ups = run_report(
    dimensions=["date"],
    metrics=["eventCount"],
    start_date="30daysAgo",
    end_date="today",
    dimension_filter={"fieldName": "eventName", "stringFilter": {"value": "sign_up"}},
)
# Conversion rate = sign_ups / form_starts per day
```

---

## Standard Reporting Patterns

### Daily summary (use in notebooks)

```python
from shared.google_analytics_client import get_daily_website_summary
import datetime

today = datetime.date.today().isoformat()
summary = get_daily_website_summary(today)
# Keys: pageviews, sessions, visitors, new_users, bounce_rate,
#       avg_session_duration, top_pages, traffic_sources
# NOTE: Does NOT include conversion counts — get those from Supabase.
```

### Traffic source breakdown for a period

```python
from shared.google_analytics_client import get_traffic_sources

sources = get_traffic_sources("30daysAgo", "today", limit=10)
# Each row: {"sessionSource": ..., "sessionMedium": ..., "sessions": ..., "conversions": ...}
# NOTE: "conversions" here is GA4 conversion events — for actual conversion counts use Supabase.
```

### UTM campaign attribution

```python
from shared.google_analytics_client import get_utm_campaigns

campaigns = get_utm_campaigns("30daysAgo", "today", limit=20)
# Each row: {"sessionCampaignName": ..., "sessionSource": ..., "sessionMedium": ..., "sessions": ..., ...}
```

### Return-Value Key Reference

GA4 client functions return dicts with these exact keys (not aliases):

| Function | Dict Keys |
|----------|-----------|
| `get_top_pages` | `pagePath`, `screenPageViews` |
| `get_traffic_sources` | `sessionSource`, `sessionMedium`, `sessions`, `conversions` |
| `get_utm_campaigns` | `sessionCampaignName`, `sessionSource`, `sessionMedium`, `sessions`, `totalUsers`, `screenPageViews`, `conversions` |
| `get_device_breakdown` | `deviceCategory`, `sessions`, `totalUsers` |
| `get_geo_breakdown` | `country`, `sessions`, `totalUsers` |
| `get_campaign_breakdown` | `sessionCampaignName`, `sessionSource`, `sessionMedium`, `sessions`, `totalUsers`, `screenPageViews`, `conversions`, `bounceRate` |

### Real-time active users

```python
from shared.google_analytics_client import get_realtime

active = get_realtime(
    dims=["minutesAgo", "country"],
    metrics=["activeUsers"],
)
# Returns users active in last 30 min, broken by minute + country
```

---

## Insights & Improvements Requirement

Every GA4 report output must end with:
1. **Insights** — 3–5 bullet points interpreting the data (trends, anomalies, comparisons).
2. **Improvements** — Concrete recommendations backed by specific metrics, tagged with owning department.

See SKILL.md §11 for the full SOP and formatting template.

---

## Measurement Protocol (server-side events)

Use `send_event()` to fire GA4 events from the backend (e.g. after a Supabase insert, Resend webhook, or `/api/claim-beta` confirmation):

```python
from execution.config import send_event

# Fire sign_up from server when /api/claim-beta returns 200
send_event(
    name="sign_up",
    params={"method": "email", "form": "beta_claim"},
    client_id="<user-cid>",   # Pass through from the frontend cookie _ga
)
```

> Measurement Protocol events do NOT require a browser. They appear in GA4 within ~1 minute but are NOT captured by browser-side interception tools (Playwright `page.on("request")`).

---

## Testing GA4 Events End-to-End

Use the Playwright harness in `Website/playwright_test.py` to verify events fire on localhost before deploying:

```bash
# From the Website/ folder with .venv active:
python playwright_test.py "http://localhost:3000" "test@hedgedge.info" "TestUser"
```

**Expected output for a full beta claim flow:**
```
GA4 network hits: 4
  GA4 en=page_view
  GA4 en=scroll
  GA4 en=form_start
  GA4 en=sign_up
beta_claim API fired: True
sign_up via GA4 network: True
```

The script intercepts `https://region1.google-analytics.com/g/collect` requests via `page.on("request")` and parses the `?en=` query parameter for the event name.

**Key selector facts** (BetaAccessModal, verified):
- Open modal: `button:has-text('Claim free Windows beta')`
- Checkboxes: `page.locator("input[type='checkbox']").nth(i).check()`
- Continue: `button:has-text('Continue')`
- First name: `[role='dialog'] input[placeholder='First name']`
- Email: `[role='dialog'] input[placeholder='you@example.com']`
- Submit: `[role='dialog'] button:has-text('Claim My Free Beta Access')`

> Always scope modal inputs to `[role='dialog']` — the home page has a separate guide form with email inputs that will match first if unscoped.

---

## GA4 Property Details

| Key | Value |
|---|---|
| Measurement ID | `G-6VJ74PHHZ0` |
| GTM Container | `GTM-45je63h` |
| Enhanced Measurement | Enabled (scroll 90%, form_start, outbound clicks) |
| Data stream | Web — `hedgedge.com` |
