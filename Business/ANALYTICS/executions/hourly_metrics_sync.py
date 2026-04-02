"""
Hedge Edge — Hourly Metrics Sync
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pulls external metrics from GA4, Resend, Supabase, Creem,
and Short.io every hour and upserts them into the relevant Notion databases:

  • kpi_snapshots    — top-line KPIs (MRR, users, traffic, email performance)
  • funnel_metrics   — stage-by-stage breakdown (email + signup funnel)
  • email_sends      — enrich with Resend delivery status
  • email_sequences  — aggregated per-sequence open/click/unsub rates
  • link_tracking    — Short.io click stats refresh
  • mrr_tracker      — MRR from active Creem subscriptions
  • campaigns        — GA4 UTM campaign performance

Designed to run every hour via Railway cron (0 * * * *).

Usage:
    python scripts/hourly_metrics_sync.py           # run once now
    python scripts/hourly_metrics_sync.py --loop     # run in a loop every hour
"""

import os
import sys
import time
import argparse

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import traceback
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _WS)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS, ".env"), override=True)

import requests
from shared.notion_client import (
    DATABASES, add_row, query_db, update_row, log_task, get_notion,
    notion_request, notion_rate_limiter_stats,
)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
RESEND_AUDIENCE_ID = "17895b10-363b-47d7-9784-477131568f7f"


def _notion_headers() -> dict:
    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _resend_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
        "Content-Type": "application/json",
    }


def _find_today_row(db_key: str, date_prop: str, today_iso: str) -> Optional[dict]:
    """Find an existing row for today in a Notion database."""
    try:
        rows = query_db(db_key, filter={
            "property": date_prop,
            "date": {"equals": today_iso},
        }, page_size=1)
        return rows[0] if rows else None
    except Exception:
        return None


def _find_today_row_by_name(db_key: str, name_prefix: str) -> Optional[dict]:
    """Find an existing row by Name prefix match."""
    try:
        rows = query_db(db_key, filter={
            "property": "Name",
            "title": {"starts_with": name_prefix},
        }, page_size=1)
        return rows[0] if rows else None
    except Exception:
        return None


def _safe(fn, label: str, default=None):
    """Run a collector function safely, catching and logging errors."""
    try:
        return fn()
    except Exception as e:
        print(f"  ⚠️  {label} failed: {e}")
        return default


def _truncate_notes(text: str, limit: int = 1500) -> str:
    """Keep only the last `limit` chars of notes to prevent Notion 2000-char overflow."""
    if len(text) <= limit:
        return text
    return "…" + text[-(limit - 1):]


# ──────────────────────────────────────────────
# 1. Email Stats (from Notion email_sends)
# ──────────────────────────────────────────────
def collect_email_stats() -> dict:
    """Count email statuses from Notion email_sends DB."""
    print("  [1/7] Collecting email stats from Notion email_sends …")
    db_id = DATABASES["email_sends"]
    h = _notion_headers()

    all_rows = []
    cursor = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = notion_request(
            "post",
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=h, json=body, timeout=60,
        )
        data = r.json()
        all_rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]

    counts = {
        "total": 0, "sent": 0, "delivered": 0, "opened": 0,
        "clicked": 0, "bounced": 0, "complained": 0, "replied": 0,
    }
    by_email: dict[str, dict] = {}

    for row in all_rows:
        props = row.get("properties", {})
        status_sel = props.get("Last Email Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        has_replied = props.get("Has Replied", {}).get("checkbox", False)
        drip_sel = props.get("Drip Stage", {}).get("select")
        drip_stage = drip_sel.get("name", "Unknown") if drip_sel else "Unknown"

        if has_replied:
            counts["replied"] += 1
        counts["total"] += 1
        status_lower = status.lower()
        if status_lower in counts:
            counts[status_lower] += 1

        if drip_stage not in by_email:
            by_email[drip_stage] = {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "bounced": 0}
        if status_lower in by_email[drip_stage]:
            by_email[drip_stage][status_lower] += 1

    print(f"    Emails: {counts['total']} total | {counts['delivered']} delivered | "
          f"{counts['opened']} opened | {counts['clicked']} clicked | {counts['replied']} replied")
    return {"counts": counts, "by_email": by_email, "all_rows": all_rows}


# ──────────────────────────────────────────────
# 2. Resend Enrichment (enrich email_sends from Resend API)
# ──────────────────────────────────────────────
def enrich_email_sends_from_resend() -> None:
    """Pull latest delivery events from Resend and update Notion email_sends."""
    print("  [2/7] Enriching email_sends from Resend delivery data …")
    _EMAIL_SYSTEM_DIR = os.path.join(
        _WS, "Business", "GROWTH", "executions", "Marketing", "email_marketing",
    )
    try:
        sys.path.insert(0, _EMAIL_SYSTEM_DIR)
        from email_system import enrich_notion_from_resend
        enrich_notion_from_resend()
        print("    ✅ Resend enrichment complete")
    except Exception as e:
        print(f"    ⚠️  Resend enrichment failed (non-fatal): {e}")
    finally:
        if _EMAIL_SYSTEM_DIR in sys.path:
            sys.path.remove(_EMAIL_SYSTEM_DIR)


def sync_resend_unsubs_to_notion() -> None:
    """Sync Resend audience unsubscribe flags → Notion email_sends.

    The per-email enrichment above only tracks delivery events; audience-level
    unsubscribes are a separate flag that must be synced independently.
    """
    print("  [2b/7] Syncing Resend audience unsubscribes → Notion …")
    _EMAIL_SYSTEM_DIR = os.path.join(
        _WS, "Business", "GROWTH", "executions", "Marketing", "email_marketing",
    )
    try:
        sys.path.insert(0, _EMAIL_SYSTEM_DIR)
        from email_system import sync_resend_unsubs_to_notion as _sync_unsubs
        _sync_unsubs()
        print("    ✅ Resend unsub sync complete")
    except Exception as e:
        print(f"    ⚠️  Resend unsub sync failed (non-fatal): {e}")
    finally:
        if _EMAIL_SYSTEM_DIR in sys.path:
            sys.path.remove(_EMAIL_SYSTEM_DIR)


def get_resend_unsub_stats() -> dict:
    """Fetch unsubscribe stats from Resend audience."""
    try:
        r = requests.get(
            f"https://api.resend.com/audiences/{RESEND_AUDIENCE_ID}/contacts",
            headers=_resend_headers(), timeout=15,
        )
        contacts = r.json().get("data", [])
        total = len(contacts)
        unsubscribed = sum(1 for c in contacts if c.get("unsubscribed"))
        return {"total": total, "unsubscribed": unsubscribed}
    except Exception as e:
        print(f"    ⚠️  Resend audience fetch failed: {e}")
        return {"total": 0, "unsubscribed": 0}


# ──────────────────────────────────────────────
# 3. Supabase Users
# ──────────────────────────────────────────────
def collect_supabase_stats() -> dict:
    """Get total users and recent signups from Supabase."""
    print("  [3/7] Collecting Supabase user stats …")
    try:
        from shared.supabase_client import get_supabase
        sb = get_supabase(use_service_role=True)

        result = sb.table("profiles").select("id", count="exact").execute()
        total_users = result.count or len(result.data)

        all_profiles = sb.table("profiles").select("id, created_at").execute().data
        now = datetime.now(timezone.utc)
        recent_24h = sum(
            1 for p in all_profiles
            if p.get("created_at") and
            (now - datetime.fromisoformat(
                p["created_at"].replace("Z", "+00:00")
            )).total_seconds() < 86400
        )

        print(f"    Users: {total_users} total | {recent_24h} new (24h)")
        return {"total_users": total_users, "new_signups_24h": recent_24h}
    except Exception as e:
        print(f"    ⚠️  Supabase unavailable: {e}")
        return {"total_users": 0, "new_signups_24h": 0}


# ──────────────────────────────────────────────
# 4. GA4 Analytics
# ──────────────────────────────────────────────
def collect_ga4_stats(report_date: str) -> dict:
    """Pull website analytics from GA4."""
    print("  [4/7] Collecting GA4 website analytics …")
    try:
        from shared.google_analytics_client import get_daily_website_summary
        ga = get_daily_website_summary(report_date)

        by_source: dict[str, int] = {}
        for src in ga.get("traffic_sources", []):
            key = src.get("sessionSource", "direct")
            by_source[key] = by_source.get(key, 0) + src.get("sessions", 0)

        result = {
            "pageviews": ga.get("pageviews", 0),
            "sessions": ga.get("sessions", 0),
            "visitors": ga.get("visitors", 0),
            "new_users": ga.get("new_users", 0),
            "avg_session_duration": ga.get("avg_session_duration", 0.0),
            "bounce_rate": ga.get("bounce_rate", 0.0),
            "conversions": ga.get("conversions", 0),
            "by_source": by_source,
            "utm_campaigns": ga.get("utm_campaigns", []),
            "source": "ga4",
        }
        print(f"    GA4: {result['pageviews']} pageviews | {result['sessions']} sessions | "
              f"{result['visitors']} visitors | {result['conversions']} conversions")
        return result
    except Exception as e:
        print(f"    ⚠️  GA4 unavailable: {e}")
        # Fallback to Supabase page_views
        return _collect_supabase_pageviews(report_date)


def _collect_supabase_pageviews(report_date: str) -> dict:
    """Fallback: pull pageview data from Supabase page_views table."""
    try:
        from shared.supabase_client import get_supabase
        sb = get_supabase(use_service_role=True)
        start = f"{report_date}T00:00:00+00:00"
        end = f"{report_date}T23:59:59+00:00"
        result = sb.table("page_views") \
            .select("id, path, utm_source, user_agent") \
            .gte("created_at", start).lte("created_at", end).execute()
        rows = result.data or []
        pageviews = len(rows)
        unique_agents = {r.get("user_agent", "") for r in rows if r.get("user_agent")}
        by_source: dict[str, int] = {}
        for r in rows:
            src = r.get("utm_source") or "direct"
            by_source[src] = by_source.get(src, 0) + 1
        return {
            "pageviews": pageviews, "sessions": 0, "visitors": len(unique_agents),
            "new_users": 0, "avg_session_duration": 0.0, "bounce_rate": 0.0,
            "conversions": 0, "by_source": by_source, "utm_campaigns": [],
            "source": "supabase",
        }
    except Exception:
        return {
            "pageviews": 0, "sessions": 0, "visitors": 0, "new_users": 0,
            "avg_session_duration": 0.0, "bounce_rate": 0.0, "conversions": 0,
            "by_source": {}, "utm_campaigns": [], "source": "none",
        }


# ──────────────────────────────────────────────
# 5. MRR / Subscription Revenue (Creem)
# ──────────────────────────────────────────────
def collect_mrr_stats() -> dict:
    """Calculate MRR from active Creem subscriptions."""
    print("  [5/7] Collecting MRR / subscription stats …")
    mrr = 0.0
    active_subs = 0
    churned_subs = 0
    sources: list[str] = []

    # Creem subscriptions
    try:
        from shared.creem_client import list_subscriptions
        subs = list_subscriptions(use_test=False)
        for sub in subs:
            status = sub.get("status", "").lower()
            if status in ("active", "trialing"):
                # Creem amounts are typically in cents
                amount = sub.get("amount", 0) or sub.get("price", 0) or 0
                interval = sub.get("interval", "month").lower()
                monthly = amount / 100.0
                if interval == "year":
                    monthly = monthly / 12
                elif interval == "week":
                    monthly = monthly * 4.33
                mrr += monthly
                active_subs += 1
            elif status in ("canceled", "cancelled", "expired"):
                churned_subs += 1
        sources.append("creem")
        print(f"    Creem: {active_subs} active subs, £{mrr:.2f} MRR")
    except Exception as e:
        print(f"    ⚠️  Creem unavailable: {e}")

    # Supabase active subscriptions count
    try:
        from shared.supabase_client import count_active_subs
        sb_active = count_active_subs()
        if sb_active > active_subs:
            active_subs = sb_active  # use the higher count
        print(f"    Supabase subs: {sb_active} active")
    except Exception as e:
        print(f"    ⚠️  Supabase subs unavailable: {e}")

    result = {
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "active_subs": active_subs,
        "churned_subs": churned_subs,
        "churn_rate": round(churned_subs / max(active_subs + churned_subs, 1) * 100, 2),
        "sources": sources,
    }
    print(f"    MRR: £{result['mrr']:.2f} | ARR: £{result['arr']:.2f} | "
          f"Active: {active_subs} | Churned: {churned_subs}")
    return result


# ──────────────────────────────────────────────
# 6. Short.io Link Tracking
# ──────────────────────────────────────────────
def _extract_utm_campaign(destination_url: str) -> str:
    """Extract utm_campaign from a destination URL's query string."""
    if not destination_url:
        return ""
    from urllib.parse import urlparse, parse_qs
    try:
        qs = parse_qs(urlparse(str(destination_url)).query)
        vals = qs.get("utm_campaign", [])
        return vals[0] if vals else ""
    except Exception:
        return ""


def _normalise_campaign_key(value: str) -> str:
    """Normalise campaign names so small formatting drift still matches."""
    if not value:
        return ""
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def refresh_link_tracking_stats() -> int:
    """Refresh click counts for all tracked links in Notion link_tracking DB.

    Clicks       = Short.io totalClicks (raw click count).
    Human Clicks = Short.io humanClicks (bot-filtered).
    Conversions  = real signups from Supabase user_attribution matching utm_campaign.

    Also auto-discovers Short.io links not yet tracked in Notion and adds them.
    """
    print("  [6/7] Refreshing Short.io link click stats …")
    updated = 0
    discovered = 0
    try:
        from shared.shortio_client import get_link_stats, list_links
        from shared.supabase_client import get_supabase

        # Build conversion counts per utm_campaign from Supabase
        sb = get_supabase(use_service_role=True)
        attr_rows = sb.table("user_attribution").select("utm_campaign").execute().data or []
        conversion_counts: dict[str, int] = {}
        for ar in attr_rows:
            camp = ar.get("utm_campaign")
            if camp:
                normalised = _normalise_campaign_key(camp)
                if normalised:
                    conversion_counts[normalised] = conversion_counts.get(normalised, 0) + 1

        rows = query_db("link_tracking", page_size=100)
        tracked_link_ids = set()

        for row in rows:
            link_id = row.get("Link ID") or row.get("Short.io ID")
            if not link_id:
                continue
            tracked_link_ids.add(str(link_id))
            try:
                stats = get_link_stats(str(link_id), period="total")
                total_clicks = stats.get("totalClicks", 0)
                human_clicks = stats.get("humanClicks", 0)

                # Real conversions from user_attribution
                campaign = row.get("UTM Campaign") or ""
                # Backfill: if UTM Campaign is empty, extract from Destination URL
                if not campaign:
                    campaign = _extract_utm_campaign(
                        row.get("Destination URL", "")
                    )
                real_conversions = conversion_counts.get(
                    _normalise_campaign_key(campaign),
                    0,
                )

                page_id = row.get("_id")
                if page_id:
                    props: dict[str, Any] = {
                        "Clicks": total_clicks,
                        "Human Clicks": human_clicks,
                        "Conversions": real_conversions,
                        "Last Clicked": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d"
                        ),
                    }
                    # Backfill UTM Campaign if it was missing in Notion
                    if campaign and not row.get("UTM Campaign"):
                        props["UTM Campaign"] = campaign
                    update_row(page_id, "link_tracking", props)
                    updated += 1
            except Exception as exc:
                short_url = row.get("Short URL", "?")
                print(f"    ⚠️  Failed to update {short_url}: {exc}")
                continue

        # ── Auto-discover untracked Short.io links ──
        try:
            all_links = list_links(limit=150)
            for lnk in all_links:
                lid = lnk.get("idString") or lnk.get("id") or ""
                if not lid or lid in tracked_link_ids:
                    continue
                short_url = lnk.get("shortURL", "")
                original_url = lnk.get("originalURL", "")
                campaign = _extract_utm_campaign(original_url)

                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(original_url).query)
                source = (qs.get("utm_source", [""])[0] or "").lower()
                medium = (qs.get("utm_medium", [""])[0] or "").lower()

                try:
                    stats = get_link_stats(str(lid), period="total")
                    total_clicks = stats.get("totalClicks", 0)
                    human_clicks = stats.get("humanClicks", 0)
                except Exception:
                    total_clicks = 0
                    human_clicks = 0

                real_conversions = conversion_counts.get(
                    _normalise_campaign_key(campaign),
                    0,
                )

                try:
                    add_row("link_tracking", {
                        "Short URL": short_url,
                        "Destination URL": original_url,
                        "Link ID": str(lid),
                        "Clicks": total_clicks,
                        "Human Clicks": human_clicks,
                        "Conversions": real_conversions,
                        "UTM Source": source or "unknown",
                        "UTM Medium": medium or "unknown",
                        "UTM Campaign": campaign,
                        "Status": "Active",
                        "Created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "Last Clicked": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d"
                        ),
                    })
                    discovered += 1
                    tracked_link_ids.add(lid)
                except Exception as exc:
                    print(f"    ⚠️  Failed to add {short_url}: {exc}")
        except Exception as exc:
            print(f"    ⚠️  Auto-discovery failed: {exc}")

        msg = f"    ✅ {updated}/{len(rows)} links updated"
        if discovered:
            msg += f", {discovered} new links discovered"
        print(msg)
    except Exception as e:
        print(f"    ⚠️  Link tracking refresh failed: {e}")
        traceback.print_exc()
    return updated + discovered


# ──────────────────────────────────────────────
# 7. Lead Pipeline Stats (from Notion CRM)
# ──────────────────────────────────────────────
def collect_lead_stats() -> dict:
    """Count leads by status from Notion CRM."""
    print("  [7/7] Collecting lead pipeline stats …")
    db_id = DATABASES["leads_crm"]
    h = _notion_headers()

    all_leads = []
    cursor = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = notion_request(
            "post",
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=h, json=body, timeout=60,
        )
        data = r.json()
        all_leads.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]

    status_counts: dict[str, int] = {}
    for lead in all_leads:
        props = lead.get("properties", {})
        status_sel = props.get("Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    total = len(all_leads)
    print(f"    Leads: {total} total | Breakdown: {status_counts}")
    return {"total_leads": total, "by_status": status_counts}


# ──────────────────────────────────────────────
# Writers — Upsert into Notion
# ──────────────────────────────────────────────
def upsert_kpi_snapshot(
    today_iso: str,
    email_stats: dict,
    supabase_stats: dict,
    ga4_stats: dict,
    lead_stats: dict,
    mrr_stats: dict,
) -> None:
    """Upsert today's row in kpi_snapshots — update if exists, else create."""
    print("\n  Writing kpi_snapshots …")
    counts = email_stats.get("counts", {})
    open_rate = round(counts.get("opened", 0) / max(counts.get("delivered", 1), 1) * 100, 1)
    click_rate = (
        round(counts.get("clicked", 0) / max(counts.get("opened", 1), 1) * 100, 1)
        if counts.get("opened", 0) > 0 else 0
    )

    now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
    notes = (
        f"[{now_str}] Emails: {counts.get('total', 0)} sent, "
        f"{counts.get('delivered', 0)} delivered, "
        f"{counts.get('opened', 0)} opened ({open_rate}%), "
        f"{counts.get('clicked', 0)} clicked ({click_rate}%), "
        f"{counts.get('bounced', 0)} bounced, {counts.get('replied', 0)} replied | "
        f"Web [{ga4_stats.get('source', '?')}]: {ga4_stats.get('pageviews', 0)} pageviews, "
        f"{ga4_stats.get('sessions', 0)} sessions, {ga4_stats.get('visitors', 0)} visitors, "
        f"bounce {ga4_stats.get('bounce_rate', 0):.1%} | "
        f"Leads: {lead_stats.get('total_leads', 0)} | "
        f"MRR: £{mrr_stats.get('mrr', 0):.2f}"
    )

    row_data = {
        "Name": f"Hourly Snapshot {today_iso}",
        "Date": today_iso,
        "Period": "Hourly",
        "MRR": mrr_stats.get("mrr", 0),
        "Active Users": supabase_stats.get("total_users", 0),
        "New Signups": supabase_stats.get("new_signups_24h", 0),
        "Churn Rate": mrr_stats.get("churn_rate", 0),
        "Notes": _truncate_notes(notes),
    }

    # Try to find existing hourly row for today
    existing = _find_today_row_by_name("kpi_snapshots", f"Hourly Snapshot {today_iso}")
    if existing:
        update_row(existing["_id"], "kpi_snapshots", row_data)
        print(f"    ✅ kpi_snapshots updated (existing row)")
    else:
        add_row("kpi_snapshots", row_data)
        print(f"    ✅ kpi_snapshots created (new row)")


def upsert_funnel_metrics(
    today_iso: str,
    email_stats: dict,
    supabase_stats: dict,
    ga4_stats: dict,
    lead_stats: dict,
) -> None:
    """Upsert today's funnel stage rows — one row per stage."""
    print("  Writing funnel_metrics …")
    counts = email_stats.get("counts", {})

    stages = [
        ("Lead Captured", counts.get("total", 0), "email", None),
        ("Email Delivered", counts.get("delivered", 0), "email",
         round(counts.get("delivered", 0) / max(counts.get("total", 1), 1) * 100, 1)),
        ("Email Opened", counts.get("opened", 0), "email",
         round(counts.get("opened", 0) / max(counts.get("delivered", 1), 1) * 100, 1)),
        ("Email Clicked", counts.get("clicked", 0), "email",
         round(counts.get("clicked", 0) / max(counts.get("opened", 1), 1) * 100, 1)),
        ("Email Replied", counts.get("replied", 0), "email",
         round(counts.get("replied", 0) / max(counts.get("total", 1), 1) * 100, 1)),
        ("Landing Page Visit", ga4_stats.get("pageviews", 0), "website", None),
        ("Sessions", ga4_stats.get("sessions", 0), "website", None),
        ("Unique Visitors", ga4_stats.get("visitors", 0), "website", None),
        ("New Users", ga4_stats.get("new_users", 0), "website",
         round(ga4_stats.get("new_users", 0) / max(ga4_stats.get("visitors", 1), 1) * 100, 1)
         if ga4_stats.get("visitors", 0) > 0 else None),
        ("Signup", supabase_stats.get("total_users", 0), "website",
         round(supabase_stats.get("total_users", 0) / max(ga4_stats.get("visitors", 1), 1) * 100, 1)
         if ga4_stats.get("visitors", 0) > 0 else None),
    ]

    written = 0
    for stage_name, count, source, conv_rate in stages:
        row_name = f"{stage_name} — {today_iso} (hourly)"

        props: dict[str, Any] = {
            "Name": row_name,
            "Date": today_iso,
            "Stage": stage_name,
            "Count": count,
            "Period": "Hourly",
            "Source": source,
        }
        if conv_rate is not None:
            props["Conversion Rate"] = conv_rate

        # Try upsert
        existing = _find_today_row_by_name("funnel_metrics", row_name)
        if existing:
            update_row(existing["_id"], "funnel_metrics", props)
        else:
            add_row("funnel_metrics", props)
        written += 1

    print(f"    ✅ {written} funnel rows upserted")


def upsert_mrr_tracker(today_iso: str, mrr_stats: dict) -> None:
    """Upsert today's MRR row."""
    print("  Writing mrr_tracker …")
    if mrr_stats.get("mrr", 0) == 0 and not mrr_stats.get("sources"):
        print("    Skipping — no MRR data available")
        return

    row_data = {
        "Date": today_iso,
        "MRR": mrr_stats.get("mrr", 0),
        "ARR": mrr_stats.get("arr", 0),
        "New Subs": mrr_stats.get("active_subs", 0),
        "Churned Subs": mrr_stats.get("churned_subs", 0),
        "Churn Rate": mrr_stats.get("churn_rate", 0),
    }

    existing = _find_today_row("mrr_tracker", "Date", today_iso)
    if existing:
        update_row(existing["_id"], "mrr_tracker", row_data)
        print("    ✅ mrr_tracker updated")
    else:
        add_row("mrr_tracker", row_data)
        print("    ✅ mrr_tracker created")


def update_email_sequences(email_stats: dict) -> None:
    """Update email_sequences DB with aggregated per-email delivery stats."""
    print("  Updating email_sequences …")
    h = _notion_headers()
    seq_db_id = DATABASES.get("email_sequences")
    if not seq_db_id:
        print("    ⚠️  email_sequences DB not configured")
        return

    resend_unsub = get_resend_unsub_stats()
    all_rows = email_stats.get("all_rows", [])
    if not all_rows:
        print("    No rows — skipping")
        return

    _STAGE_ORDER = {
        "Welcome": 0, "Email 1": 1, "Email 2": 2, "Email 3": 3,
        "Email 4": 4, "Email 5": 5, "Email 6": 6, "Email 7": 7,
        "Complete": 99,
    }

    # Parse lead data
    lead_data = []
    for row in all_rows:
        props = row.get("properties", {})
        drip_sel = props.get("Drip Stage", {}).get("select")
        drip_stage = drip_sel.get("name", "Unknown") if drip_sel else "Unknown"
        status_sel = props.get("Last Email Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        lead_data.append({
            "drip_stage": drip_stage,
            "status": status,
            "stage_num": _STAGE_ORDER.get(drip_stage, -1),
        })

    # Per-stage stats
    stage_stats: dict[str, dict] = {}
    for stage_name, stage_num in sorted(_STAGE_ORDER.items(), key=lambda x: x[1]):
        if stage_num < 0 or stage_name == "Complete":
            continue
        sent_to = sum(1 for ld in lead_data if ld["stage_num"] >= stage_num and ld["stage_num"] >= 0)
        at_stage = [ld for ld in lead_data if ld["drip_stage"] == stage_name]
        n_at = len(at_stage)
        delivered = sum(1 for ld in at_stage if ld["status"] in ("Delivered", "Opened", "Clicked"))
        opened = sum(1 for ld in at_stage if ld["status"] in ("Opened", "Clicked"))
        clicked = sum(1 for ld in at_stage if ld["status"] == "Clicked")
        bounced = sum(1 for ld in at_stage if ld["status"] == "Bounced")
        stage_stats[stage_name] = {
            "sent_to": sent_to, "at_stage": n_at,
            "delivered": delivered, "opened": opened,
            "clicked": clicked, "bounced": bounced,
        }

    # Fetch sequence pages
    all_seq_pages = []
    cursor = None
    while True:
        payload: dict[str, Any] = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        r = notion_request(
            "post",
            f"https://api.notion.com/v1/databases/{seq_db_id}/query",
            headers=h, json=payload, timeout=60,
        )
        data = r.json()
        all_seq_pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0

    for page in all_seq_pages:
        page_id = page["id"]
        props = page.get("properties", {})

        title = ""
        for k, v in props.items():
            if v.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                break

        title_lower = title.lower().strip()
        stage_name = None

        if title_lower.startswith("email ") and title_lower[6:].strip().isdigit():
            stage_name = f"Email {int(title.split()[-1])}"
        elif "welcome" in title_lower:
            stage_name = "Welcome"
        else:
            continue

        stats = stage_stats.get(stage_name, {
            "sent_to": 0, "at_stage": 0, "delivered": 0,
            "opened": 0, "clicked": 0, "bounced": 0,
        })

        denom = max(stats["at_stage"], 1)
        open_rate = round(stats["opened"] / denom * 100, 1)
        click_rate = round(stats["clicked"] / denom * 100, 1)
        unsub_total = max(resend_unsub["total"], 1)
        unsub_rate = round(resend_unsub["unsubscribed"] / unsub_total * 100, 1)

        seq_status = "Active" if stats["at_stage"] > 0 else ("Completed" if stats["sent_to"] > 0 else "Waiting")

        notes_text = (
            f"Sent to: {stats['sent_to']} | At stage: {stats['at_stage']} | "
            f"Delivered: {stats['delivered']} | Opened: {stats['opened']} ({open_rate}%) | "
            f"Clicked: {stats['clicked']} ({click_rate}%) | Bounced: {stats['bounced']}"
        )
        update_props = {
            "Emails Count": {"number": stats["sent_to"]},
            "Status": {"select": {"name": seq_status}},
            "Last Updated": {"date": {"start": today_iso}},
            "Notes": {"rich_text": [{"text": {"content": _truncate_notes(notes_text)}}]},
        }

        try:
            resp = notion_request(
                "patch",
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=h, json={"properties": update_props}, timeout=60,
            )
            if resp.status_code == 200:
                updated += 1
        except Exception:
            pass
        # Rate limiting handled by notion_request/rate limiter

    print(f"    ✅ {updated} email sequences updated")


def update_campaign_stats(today_iso: str, ga4_stats: dict) -> None:
    """Update campaigns DB with GA4 UTM campaign performance."""
    utm_campaigns = ga4_stats.get("utm_campaigns", [])
    if not utm_campaigns:
        print("  Skipping campaign stats — no UTM data")
        return

    print(f"  Updating campaign stats ({len(utm_campaigns)} campaigns) …")
    written = 0

    try:
        existing_campaigns = query_db("campaigns", page_size=100)
    except Exception:
        existing_campaigns = []

    campaign_lookup = {}
    for row in existing_campaigns:
        name = (row.get("Name") or "").strip()
        if name:
            campaign_lookup[name.lower()] = row

    for camp in utm_campaigns:
        camp_name = camp.get("sessionCampaignName", "(not set)")
        if camp_name == "(not set)":
            continue

        sessions = camp.get("sessions", 0)
        users = camp.get("totalUsers", 0)
        pageviews = camp.get("screenPageViews", 0)
        conversions = camp.get("conversions", 0)
        notes_text = (
            f"[{today_iso}] GA4: {sessions} sessions, {users} users, "
            f"{pageviews} pageviews, {conversions} conversions"
        )

        existing = campaign_lookup.get(camp_name.lower())
        if existing:
            # Skip campaigns with End Date in the past and not Active
            end_date = existing.get("End Date") or ""
            camp_status = existing.get("Status") or ""
            if end_date and end_date < today_iso and camp_status != "Active":
                continue
            page_id = existing.get("_id")
            old_notes = existing.get("Notes") or ""
            if today_iso not in old_notes:
                new_notes = _truncate_notes(f"{notes_text}\n{old_notes}".strip())
                try:
                    update_row(page_id, "campaigns", {"Notes": new_notes})
                    written += 1
                except Exception:
                    pass
        else:
            try:
                add_row("campaigns", {
                    "Name": camp_name,
                    "Status": "Active",
                    "Channel": "GA4 Auto",
                    "Type": "UTM Tracking",
                    "Created At": datetime.now().isoformat(),
                    "Goal": f"Track traffic from utm_campaign={camp_name}",
                    "Notes": _truncate_notes(notes_text),
                })
                written += 1
            except Exception:
                pass

    print(f"    ✅ {written} campaigns updated/created")


# ──────────────────────────────────────────────
# Main Orchestrator
# ──────────────────────────────────────────────
def run_hourly_sync() -> dict:
    """
    Run the full hourly metrics sync cycle.
    Returns a summary dict.
    """
    start = datetime.now(timezone.utc)
    today_iso = start.strftime("%Y-%m-%d")

    print("=" * 60)
    print("  HOURLY METRICS SYNC")
    print(f"  Date:     {today_iso}")
    print(f"  Run time: {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # ── Collect from external sources ──
    print("\n--- COLLECTING EXTERNAL METRICS ---")

    # Step 1: Enrich email_sends from Resend first (so stats are fresh)
    _safe(enrich_email_sends_from_resend, "Resend enrichment")

    # Step 1b: Sync Resend audience-level unsubscribes → Notion
    _safe(sync_resend_unsubs_to_notion, "Resend unsub sync")

    # Step 2: Collect all metrics
    email_stats = _safe(collect_email_stats, "Email stats",
                        {"counts": {}, "by_email": {}, "all_rows": []})
    supabase_stats = _safe(collect_supabase_stats, "Supabase stats",
                           {"total_users": 0, "new_signups_24h": 0})
    ga4_stats = _safe(lambda: collect_ga4_stats(today_iso), "GA4 stats",
                      {"pageviews": 0, "sessions": 0, "visitors": 0, "new_users": 0,
                       "avg_session_duration": 0.0, "bounce_rate": 0.0, "conversions": 0,
                       "by_source": {}, "utm_campaigns": [], "source": "none"})
    mrr_stats = _safe(collect_mrr_stats, "MRR stats",
                      {"mrr": 0, "arr": 0, "active_subs": 0, "churned_subs": 0,
                       "churn_rate": 0, "sources": []})
    lead_stats = _safe(collect_lead_stats, "Lead stats",
                       {"total_leads": 0, "by_status": {}})

    # ── Write to Notion ──
    print("\n--- WRITING TO NOTION ---")

    _safe(lambda: upsert_kpi_snapshot(
        today_iso, email_stats, supabase_stats, ga4_stats, lead_stats, mrr_stats,
    ), "KPI snapshot write")

    _safe(lambda: upsert_funnel_metrics(
        today_iso, email_stats, supabase_stats, ga4_stats, lead_stats,
    ), "Funnel metrics write")

    _safe(lambda: upsert_mrr_tracker(today_iso, mrr_stats), "MRR tracker write")

    _safe(lambda: update_email_sequences(email_stats), "Email sequences update")

    _safe(lambda: update_campaign_stats(today_iso, ga4_stats), "Campaign stats update")

    links_updated = _safe(refresh_link_tracking_stats, "Link tracking refresh", 0)

    # ── Summary ──
    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    rl_stats = notion_rate_limiter_stats()
    summary = {
        "date": today_iso,
        "run_time": start.strftime("%Y-%m-%d %H:%M UTC"),
        "elapsed_seconds": round(elapsed, 1),
        "emails_total": email_stats.get("counts", {}).get("total", 0),
        "emails_opened": email_stats.get("counts", {}).get("opened", 0),
        "emails_clicked": email_stats.get("counts", {}).get("clicked", 0),
        "emails_replied": email_stats.get("counts", {}).get("replied", 0),
        "pageviews": ga4_stats.get("pageviews", 0),
        "sessions": ga4_stats.get("sessions", 0),
        "visitors": ga4_stats.get("visitors", 0),
        "mrr": mrr_stats.get("mrr", 0),
        "total_users": supabase_stats.get("total_users", 0),
        "new_signups": supabase_stats.get("new_signups_24h", 0),
        "total_leads": lead_stats.get("total_leads", 0),
        "links_updated": links_updated or 0,
        "notion_api_calls": rl_stats["total_requests"],
        "notion_rate_limits_hit": rl_stats["total_rate_limits"],
        "notion_retries": rl_stats["total_retries"],
    }

    print("\n" + "=" * 60)
    print("  SYNC COMPLETE")
    for k, v in summary.items():
        print(f"    {k}: {v}")
    print(f"  Completed in {elapsed:.1f}s")
    print("=" * 60)

    return summary


def run_loop(interval_seconds: int = 3600) -> None:
    """Run the sync in a continuous loop (for Railway worker service)."""
    print(f"Starting hourly metrics sync loop (interval: {interval_seconds}s)")
    while True:
        try:
            summary = run_hourly_sync()

            # Log to Notion task log
            try:
                log_task(
                    "Analytics",
                    "Hourly metrics sync",
                    "Complete",
                    "P2",
                    (
                        f"Date: {summary['date']} | "
                        f"Emails: {summary['emails_total']} | "
                        f"Pageviews: {summary['pageviews']} | "
                        f"MRR: £{summary['mrr']:.2f} | "
                        f"Users: {summary['total_users']} | "
                        f"Leads: {summary['total_leads']} | "
                        f"Elapsed: {summary['elapsed_seconds']}s"
                    ),
                )
            except Exception as e:
                print(f"  Task log failed: {e}")

        except Exception as e:
            print(f"\n❌ Hourly sync failed: {e}")
            traceback.print_exc()

            try:
                from shared.alerting import send_cron_failure
                send_cron_failure("Hourly Metrics Sync", e)
            except Exception:
                pass

        # Sleep until next run
        next_run = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
        print(f"\nNext sync at {next_run.strftime('%H:%M UTC')} …")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedge Edge Hourly Metrics Sync")
    parser.add_argument(
        "--loop", action="store_true",
        help="Run in a continuous loop (every hour) instead of one-shot",
    )
    parser.add_argument(
        "--interval", type=int, default=3600,
        help="Interval in seconds between loop runs (default: 3600 = 1 hour)",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop(args.interval)
    else:
        summary = run_hourly_sync()

        # Log to task log for one-shot runs too
        try:
            log_task(
                "Analytics",
                "Hourly metrics sync (manual)",
                "Complete",
                "P2",
                f"Date: {summary['date']} | Elapsed: {summary['elapsed_seconds']}s",
            )
        except Exception:
            pass
