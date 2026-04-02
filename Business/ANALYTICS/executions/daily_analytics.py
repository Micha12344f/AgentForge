"""
Hedge Edge — Daily Analytics Collector
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pulls daily metrics from GA4, Resend, Supabase, and Vercel, then writes
summary rows into Notion databases:
  • kpi_snapshots  — top-line daily numbers
  • funnel_metrics — stage-by-stage breakdown (email funnel + signup funnel)

Designed to run daily at 09:00 UTC via Railway cron.

Usage:
    python scripts/daily_analytics.py          # pull yesterday's data
    python scripts/daily_analytics.py --today   # pull today-so-far
"""

import os
import sys
import time
import argparse

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timezone, timedelta
from typing import Any

_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _WS)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS, ".env"), override=True)

import requests
from shared.notion_client import DATABASES, add_row, query_db, log_task, notion_request


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
RESEND_AUDIENCE_ID = "17895b10-363b-47d7-9784-477131568f7f"


def _resend_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
        "Content-Type": "application/json",
    }


def _notion_headers() -> dict:
    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _truncate_notes(text: str, limit: int = 1500) -> str:
    """Keep only the last `limit` chars of notes to prevent Notion 2000-char overflow."""
    if len(text) <= limit:
        return text
    return "…" + text[-(limit - 1):]


def _get_resend_unsub_stats() -> dict:
    """Fetch total and unsubscribed contact counts from the Resend audience."""
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
        print(f"    Warning: could not fetch Resend audience unsub data: {e}")
        return {"total": 0, "unsubscribed": 0}


# ──────────────────────────────────────────────
# 1. Email Analytics (from Notion email_sends)
# ──────────────────────────────────────────────
def get_email_stats(report_date: str) -> dict:
    """
    Count email statuses from Notion Leads DB (one row per lead).
    Returns {total, sent, delivered, opened, clicked, bounced, replied}.
    """
    print("  [1/4] Pulling email stats from Notion Leads DB ...")
    db_id = DATABASES["email_sends"]
    h = _notion_headers()

    # Pull ALL lead rows (paginate)
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
        time.sleep(0.3)

    # Count statuses from lead rows
    counts = {"total": 0, "sent": 0, "delivered": 0, "opened": 0,
              "clicked": 0, "bounced": 0, "complained": 0, "replied": 0}
    by_email = {}  # per-drip-stage stats
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

        # Track by drip stage for funnel
        if drip_stage not in by_email:
            by_email[drip_stage] = {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "bounced": 0}
        if status_lower in by_email[drip_stage]:
            by_email[drip_stage][status_lower] += 1

    print(f"    Total leads: {counts['total']}  |  Delivered: {counts['delivered']}  |  "
          f"Opened: {counts['opened']}  |  Clicked: {counts['clicked']}  |  "
          f"Bounced: {counts['bounced']}  |  Replied: {counts['replied']}")
    return {"counts": counts, "by_email": by_email, "all_rows": all_rows}


# ──────────────────────────────────────────────
# 1b. Update Email Sequences DB from Leads data
# ──────────────────────────────────────────────

# Drip stage ordering — higher number means the lead received all prior emails
_STAGE_ORDER = {"Welcome": 0, "Email 1": 1, "Email 2": 2, "Email 3": 3,
                "Email 4": 4, "Email 5": 5, "Email 6": 6, "Email 7": 7,
                "Complete": 99}


def _extract_subject_from_page(page_id: str, headers: dict) -> str:
    """Read a Notion page's code block content and extract the Subject: line."""
    try:
        r = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=50",
            headers=headers, timeout=10,
        )
        if r.status_code != 200:
            return ""
        for block in r.json().get("results", []):
            if block.get("type") == "code":
                code_text = "".join(
                    t.get("plain_text", "")
                    for t in block["code"].get("rich_text", [])
                )
                for line in code_text.splitlines():
                    if line.strip().lower().startswith("subject:"):
                        return line.split(":", 1)[1].strip()
        return ""
    except Exception:
        return ""


def update_email_sequence_stats(email_stats: dict) -> None:
    """Aggregate per-email delivery stats from Leads DB and update email_sequences.

    For each Email N in the sequences DB:
      - Emails Count     = how many leads received that email (at stage N or higher)
      - Open Rate        = % of leads at that stage whose status is Opened or Clicked
      - Click Rate       = % of leads at that stage whose status is Clicked
      - Unsubscribe Rate = % of contacts who unsubscribed from Resend audience
      - Status           = Active / Completed / Waiting (based on current lead counts)
      - Subject Line     = extracted from the page's code-block template
      - Last Updated     = today
      - Notes            = human-readable summary of all counts
      - Rename "Lead email N" → "Email N" if using legacy naming

    Data comes from email_sends rows (enriched from Resend in step 0).
    """
    print("  [1b/4] Updating Email Sequences DB with delivery stats …")

    h = _notion_headers()
    seq_db_id = DATABASES.get("email_sequences")
    if not seq_db_id:
        print("    ⚠️  email_sequences DB not configured — skipping")
        return
    # Pull real unsubscribe count from Resend audience
    resend_unsub = _get_resend_unsub_stats()
    print(f"    Resend audience: {resend_unsub['total']} contacts, {resend_unsub['unsubscribed']} unsubscribed")
    all_rows = email_stats.get("all_rows", [])
    if not all_rows:
        print("    No lead rows found — skipping sequence stats")
        return

    # ── Parse each lead row into structured data ──
    lead_data = []
    for row in all_rows:
        props = row.get("properties", {})
        drip_sel = props.get("Drip Stage", {}).get("select")
        drip_stage = drip_sel.get("name", "Unknown") if drip_sel else "Unknown"
        status_sel = props.get("Last Email Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        emails_sent = props.get("Emails Sent", {}).get("number") or 0
        has_replied = props.get("Has Replied", {}).get("checkbox", False)
        lead_data.append({
            "drip_stage": drip_stage,
            "status": status,
            "emails_sent": emails_sent,
            "has_replied": has_replied,
            "stage_num": _STAGE_ORDER.get(drip_stage, -1),
        })

    # ── Calculate per-email-stage stats ──
    # Leads at stage N or higher have received Email N
    # But we only know delivery status for leads CURRENTLY at stage N
    stage_stats: dict[str, dict] = {}  # "Email N" → {sent_to, at_stage, delivered, opened, clicked, bounced, complained}
    for stage_name, stage_num in sorted(_STAGE_ORDER.items(), key=lambda x: x[1]):
        if stage_num < 0 or stage_name == "Complete":
            continue

        # Total leads who received this email = leads at this stage or higher
        sent_to = sum(1 for ld in lead_data if ld["stage_num"] >= stage_num and ld["stage_num"] >= 0)

        # Delivery stats — only for leads currently AT this stage
        at_stage = [ld for ld in lead_data if ld["drip_stage"] == stage_name]
        n_at_stage = len(at_stage)
        delivered = sum(1 for ld in at_stage if ld["status"] in ("Delivered", "Opened", "Clicked"))
        opened = sum(1 for ld in at_stage if ld["status"] in ("Opened", "Clicked"))
        clicked = sum(1 for ld in at_stage if ld["status"] == "Clicked")
        bounced = sum(1 for ld in at_stage if ld["status"] == "Bounced")
        complained = sum(1 for ld in at_stage if ld["status"] == "Complained")

        stage_stats[stage_name] = {
            "sent_to": sent_to,
            "at_stage": n_at_stage,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "complained": complained,
        }

    # ── Fetch existing email_sequences pages ──
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
        time.sleep(0.3)

    # ── Map page IDs and detect naming ──
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0

    for page in all_seq_pages:
        page_id = page["id"]
        props = page.get("properties", {})

        # Get title
        title = ""
        for k, v in props.items():
            if v.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                break

        # Determine which stage this page represents
        title_lower = title.lower().strip()
        stage_name = None

        if title_lower.startswith("lead email "):
            try:
                num = int(title.split()[-1])
                stage_name = f"Email {num}"
            except ValueError:
                continue
        elif title_lower.startswith("email ") and title_lower[6:].strip().isdigit():
            try:
                num = int(title.split()[-1])
                stage_name = f"Email {num}"
            except ValueError:
                continue
        elif "welcome" in title_lower:
            stage_name = "Welcome"
        else:
            continue

        stats = stage_stats.get(stage_name)
        if not stats:
            # No leads at this stage yet — set zeros
            stats = {"sent_to": 0, "at_stage": 0, "delivered": 0,
                     "opened": 0, "clicked": 0, "bounced": 0, "complained": 0}

        # Calculate rates (based on leads AT this stage, not total sent_to)
        denominator = max(stats["at_stage"], 1)
        open_rate = round(stats["opened"] / denominator * 100, 1)
        click_rate = round(stats["clicked"] / denominator * 100, 1)

        # Unsubscribe Rate = actual Resend audience unsubscribes / total contacts
        # This is a global rate (unsubscribe opts out of all emails) applied to each sequence
        unsub_total = max(resend_unsub["total"], 1)
        unsub_rate = round(resend_unsub["unsubscribed"] / unsub_total * 100, 1)

        # Determine status: Active if leads currently at this stage, else Completed/Waiting
        if stats["at_stage"] > 0:
            seq_status = "Active"
        elif stats["sent_to"] > 0:
            seq_status = "Completed"
        else:
            seq_status = "Waiting"

        # Try to extract Subject Line from the page's content (code block)
        subject_line = _extract_subject_from_page(page_id, h)

        # Build update payload — only Last Updated, Notes, Status, Emails Count
        # (Open Rate / Click Rate / Unsubscribe Rate left to rollup formulas)
        notes_text = (
            f"Sent to: {stats['sent_to']} | "
            f"At stage: {stats['at_stage']} | "
            f"Delivered: {stats['delivered']} | "
            f"Opened: {stats['opened']} ({open_rate}%) | "
            f"Clicked: {stats['clicked']} ({click_rate}%) | "
            f"Bounced: {stats['bounced']} | "
            f"Complained: {stats['complained']}"
        )
        update_props: dict[str, Any] = {
            "Emails Count": {"number": stats["sent_to"]},
            "Status": {"select": {"name": seq_status}},
            "Last Updated": {"date": {"start": today_iso}},
            "Notes": {"rich_text": [{"text": {"content": _truncate_notes(notes_text)}}]},
        }

        # Add Subject Line if found
        if subject_line:
            update_props["Subject Line"] = {
                "rich_text": [{"text": {"content": subject_line[:200]}}]
            }

        try:
            resp = notion_request(
                "patch",
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=h, json={"properties": update_props}, timeout=60,
            )
            if resp.status_code == 200:
                updated += 1
                print(f"    \u2705 {title}: sent={stats['sent_to']} open={open_rate}% click={click_rate}% unsub={unsub_rate}% status={seq_status}")
            else:
                print(f"    \u274c {title}: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            print(f"    \u274c {title}: {e}")
        time.sleep(0.35)

    print(f"    Done: {updated} sequences updated")


# ──────────────────────────────────────────────
# 2. Supabase Signups
# ──────────────────────────────────────────────
def get_supabase_stats() -> dict:
    """Get total users and recent signups from Supabase."""
    print("  [2/4] Pulling Supabase user stats …")
    try:
        from shared.supabase_client import get_supabase
        sb = get_supabase(use_service_role=True)

        # Total profiles
        result = sb.table("profiles").select("id", count="exact").execute()
        total_users = result.count or len(result.data)

        # All profiles with created_at for growth calc
        all_profiles = sb.table("profiles").select("id, created_at").execute().data
        now = datetime.now(timezone.utc)
        recent_24h = sum(
            1 for p in all_profiles
            if p.get("created_at") and
            (now - datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))).total_seconds() < 86400
        )

        print(f"    Total users: {total_users}  |  New (24h): {recent_24h}")
        return {"total_users": total_users, "new_signups_24h": recent_24h}
    except Exception as e:
        print(f"    Supabase unavailable: {e}")
        return {"total_users": 0, "new_signups_24h": 0}


# ──────────────────────────────────────────────
# 3. Landing Page Analytics (GA4 → Supabase fallback)
# ──────────────────────────────────────────────
def _get_ga4_landing_page_stats(report_date: str) -> dict | None:
    """Pull website analytics from Google Analytics 4 Data API."""
    try:
        from shared.google_analytics_client import get_daily_website_summary
        ga = get_daily_website_summary(report_date)

        # Convert GA4 traffic sources into a flat source → sessions dict
        by_source: dict[str, int] = {}
        for src in ga.get("traffic_sources", []):
            key = src.get("sessionSource", "direct")
            by_source[key] = by_source.get(key, 0) + src.get("sessions", 0)

        # Convert top pages into path → views dict
        by_path: dict[str, int] = {}
        for pg in ga.get("top_pages", []):
            by_path[pg.get("pagePath", "/")] = pg.get("screenPageViews", 0)

        return {
            "pageviews": ga.get("pageviews", 0),
            "sessions": ga.get("sessions", 0),
            "visitors": ga.get("visitors", 0),
            "new_users": ga.get("new_users", 0),
            "avg_session_duration": ga.get("avg_session_duration", 0.0),
            "bounce_rate": ga.get("bounce_rate", 0.0),
            "conversions": ga.get("conversions", 0),
            "by_path": by_path,
            "by_source": by_source,
            "device_breakdown": ga.get("device_breakdown", []),
            "geo_breakdown": ga.get("geo_breakdown", []),
            "utm_campaigns": ga.get("utm_campaigns", []),
            "source": "ga4",
        }
    except Exception as e:
        print(f"    GA4 unavailable: {e}")
        return None


def _get_supabase_landing_page_stats(report_date: str) -> dict:
    """Fallback: pull pageview data from Supabase page_views table."""
    try:
        from shared.supabase_client import get_supabase
        sb = get_supabase(use_service_role=True)

        start = f"{report_date}T00:00:00+00:00"
        end = f"{report_date}T23:59:59+00:00"

        result = sb.table("page_views") \
            .select("id, path, utm_source, utm_campaign, user_agent") \
            .gte("created_at", start) \
            .lte("created_at", end) \
            .execute()

        rows = result.data or []
        pageviews = len(rows)

        unique_agents = set()
        by_path: dict[str, int] = {}
        by_source: dict[str, int] = {}
        for r in rows:
            ua = r.get("user_agent", "")
            if ua:
                unique_agents.add(ua)
            path = r.get("path", "/")
            by_path[path] = by_path.get(path, 0) + 1
            src = r.get("utm_source") or "direct"
            by_source[src] = by_source.get(src, 0) + 1

        visitors = len(unique_agents) if unique_agents else 0

        return {
            "pageviews": pageviews,
            "sessions": 0,
            "visitors": visitors,
            "new_users": 0,
            "avg_session_duration": 0.0,
            "bounce_rate": 0.0,
            "conversions": 0,
            "by_path": by_path,
            "by_source": by_source,
            "device_breakdown": [],
            "geo_breakdown": [],
            "utm_campaigns": [],
            "source": "supabase",
        }
    except Exception as e:
        print(f"    Supabase page_views unavailable: {e}")
        return {
            "pageviews": 0, "sessions": 0, "visitors": 0, "new_users": 0,
            "avg_session_duration": 0.0, "bounce_rate": 0.0, "conversions": 0,
            "by_path": {}, "by_source": {},
            "device_breakdown": [], "geo_breakdown": [], "utm_campaigns": [],
            "source": "none",
        }


def get_landing_page_stats(report_date: str) -> dict:
    """Pull website analytics — tries GA4 first, falls back to Supabase."""
    print("  [3/4] Pulling landing page stats …")

    # Try GA4 first
    print("    Trying GA4 Data API …")
    ga4_data = _get_ga4_landing_page_stats(report_date)
    if ga4_data:
        src = ga4_data.get("source", "ga4")
        print(f"    ✅ GA4: {ga4_data['pageviews']} pageviews, {ga4_data['sessions']} sessions, "
              f"{ga4_data['visitors']} visitors, {ga4_data['new_users']} new users")
        print(f"    Bounce rate: {ga4_data['bounce_rate']:.1%}  |  "
              f"Avg session: {ga4_data['avg_session_duration']:.1f}s  |  "
              f"GA4 sign_up events: {ga4_data['conversions']} (indicative only, use Supabase for actual conversions)")
        if ga4_data["by_path"]:
            top = sorted(ga4_data["by_path"].items(), key=lambda x: -x[1])[:5]
            print(f"    Top pages: {top}")
        if ga4_data["by_source"]:
            print(f"    By source: {ga4_data['by_source']}")
        return ga4_data

    # Fallback to Supabase
    print("    Falling back to Supabase page_views …")
    sb_data = _get_supabase_landing_page_stats(report_date)
    print(f"    Supabase: {sb_data['pageviews']} pageviews, {sb_data['visitors']} visitors")
    return sb_data


# ──────────────────────────────────────────────
# 4. Lead pipeline stats (from Notion leads_crm)
# ──────────────────────────────────────────────
def get_lead_stats() -> dict:
    """Count leads by status from Notion CRM."""
    print("  [4/4] Pulling lead pipeline stats from Notion …")
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
        time.sleep(0.3)

    status_counts: dict[str, int] = {}
    for lead in all_leads:
        props = lead.get("properties", {})
        status_sel = props.get("Status", {}).get("select")
        status = status_sel.get("name", "Unknown") if status_sel else "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    total = len(all_leads)
    print(f"    Total leads: {total}  |  Breakdown: {status_counts}")
    return {"total_leads": total, "by_status": status_counts}


# ──────────────────────────────────────────────
# Write to Notion
# ──────────────────────────────────────────────
def write_kpi_snapshot(
    report_date: str,
    email_stats: dict,
    supabase_stats: dict,
    lp_stats: dict,
    lead_stats: dict,
) -> None:
    """Write a daily row to kpi_snapshots."""
    print("\n  Writing kpi_snapshots …")
    counts = email_stats["counts"]
    open_rate = round(counts["opened"] / max(counts["delivered"], 1) * 100, 1)
    click_rate = round(counts["clicked"] / max(counts["opened"], 1) * 100, 1) if counts["opened"] > 0 else 0
    add_row("kpi_snapshots", {
        "Name": f"Daily Snapshot {report_date}",
        "Date": report_date,
        "Period": "Daily",
        "MRR": 0,
        "Active Users": supabase_stats["total_users"],
        "New Signups": supabase_stats["new_signups_24h"],
        "Churn Rate": 0,
        "CAC": 0,
        "LTV": 0,
        "NPS": 0,
        "Notes": _truncate_notes(
            f"Emails: {counts['total']} sent, {counts['delivered']} delivered, "
            f"{counts['opened']} opened ({open_rate}%), {counts['clicked']} clicked ({click_rate}%), "
            f"{counts['bounced']} bounced, {counts['replied']} replied | "
            f"Web [{lp_stats.get('source', '?')}]: {lp_stats['pageviews']} pageviews, "
            f"{lp_stats.get('sessions', 0)} sessions, {lp_stats['visitors']} visitors, "
            f"bounce {lp_stats.get('bounce_rate', 0):.1%} | "
            f"Leads: {lead_stats['total_leads']} total"
        ),
    })
    print("    ✅ kpi_snapshots row added")


def write_funnel_metrics(
    report_date: str,
    email_stats: dict,
    supabase_stats: dict,
    lp_stats: dict,
    lead_stats: dict,
) -> None:
    """Write funnel stage rows to funnel_metrics — one row per stage."""
    print("  Writing funnel_metrics …")
    counts = email_stats["counts"]

    stages = [
        ("Lead Captured", counts["total"], "email",
         None),
        ("Email Delivered", counts["delivered"], "email",
         round(counts["delivered"] / max(counts["total"], 1) * 100, 1)),
        ("Email Opened", counts["opened"], "email",
         round(counts["opened"] / max(counts["delivered"], 1) * 100, 1)),
        ("Email Clicked", counts["clicked"], "email",
         round(counts["clicked"] / max(counts["opened"], 1) * 100, 1)),
        ("Email Replied", counts["replied"], "email",
         round(counts["replied"] / max(counts["total"], 1) * 100, 1)),
        ("Landing Page Visit", lp_stats["pageviews"], "website",
         None),
        ("Sessions", lp_stats.get("sessions", 0), "website",
         None),
        ("Unique Visitors", lp_stats["visitors"], "website",
         None),
        ("New Users", lp_stats.get("new_users", 0), "website",
         round(lp_stats.get("new_users", 0) / max(lp_stats["visitors"], 1) * 100, 1)
         if lp_stats["visitors"] > 0 else None),
        ("Signup", supabase_stats["total_users"], "website",
         round(supabase_stats["total_users"] / max(lp_stats["visitors"], 1) * 100, 1)
         if lp_stats["visitors"] > 0 else None),
    ]

    for stage_name, count, source, conv_rate in stages:
        props: dict[str, Any] = {
            "Name": f"{stage_name} — {report_date}",
            "Date": report_date,
            "Stage": stage_name,
            "Count": count,
            "Period": "Daily",
            "Source": source,
        }
        if conv_rate is not None:
            props["Conversion Rate"] = conv_rate
        add_row("funnel_metrics", props)

    # Per-email-wave breakdown
    for wave_name, wave_data in sorted(email_stats.get("by_email", {}).items()):
        sent = wave_data.get("sent", 0)
        opened = wave_data.get("opened", 0)
        clicked = wave_data.get("clicked", 0)
        if sent == 0:
            continue
        open_rate = round(opened / max(sent, 1) * 100, 1)
        click_rate = round(clicked / max(opened, 1) * 100, 1) if opened > 0 else 0
        add_row("funnel_metrics", {
            "Name": f"{wave_name} Performance — {report_date}",
            "Date": report_date,
            "Stage": wave_name,
            "Count": sent,
            "Period": "Daily",
            "Source": "email",
            "Conversion Rate": open_rate,
            "Notes": _truncate_notes(f"Sent: {sent} | Opened: {opened} ({open_rate}%) | Clicked: {clicked} ({click_rate}%)"),
        })

    print(f"    ✅ {len(stages) + len(email_stats.get('by_email', {}))} funnel rows added")


def write_campaign_stats(
    report_date: str,
    lp_stats: dict,
) -> None:
    """
    Update Notion campaigns DB with daily GA4 utm_campaign performance.

    For each UTM campaign seen in GA4 traffic:
      - Find or create a row in the campaigns DB
      - Update its Notes with the latest sessions/users/pageviews/conversions

    Also writes per-campaign funnel rows to funnel_metrics for trend tracking.
    """
    utm_campaigns = lp_stats.get("utm_campaigns", [])
    if not utm_campaigns:
        print("  Skipping campaign stats — no UTM campaign data available")
        return

    print(f"  Writing campaign stats ({len(utm_campaigns)} campaigns) …")

    # Pull existing campaign rows from Notion to find matches
    try:
        existing_campaigns = query_db("campaigns", page_size=100)
    except Exception as e:
        print(f"    ⚠️  Could not query campaigns DB: {e}")
        existing_campaigns = []

    # Build a lookup: campaign name (lowercase) → page_id
    campaign_lookup: dict[str, dict] = {}
    for row in existing_campaigns:
        # Check Name (title), Notes, or Type fields for campaign name
        name = (row.get("Name") or "").strip()
        if name:
            campaign_lookup[name.lower()] = row

    written = 0
    for camp in utm_campaigns:
        camp_name = camp.get("sessionCampaignName", "(not set)")
        if camp_name == "(not set)":
            continue

        sessions = camp.get("sessions", 0)
        users = camp.get("totalUsers", 0)
        pageviews = camp.get("screenPageViews", 0)
        conversions = camp.get("conversions", 0)

        notes_text = (
            f"[{report_date}] GA4: {sessions} sessions, {users} users, "
            f"{pageviews} pageviews, {conversions} conversions"
        )

        # Try to find existing campaign row
        existing = campaign_lookup.get(camp_name.lower())
        if existing:
            # Skip campaigns with End Date in the past and not Active
            end_date = existing.get("End Date") or ""
            camp_status = existing.get("Status") or ""
            if end_date and end_date < report_date and camp_status != "Active":
                continue
            # Update existing row — append to Notes
            page_id = existing.get("_id")
            old_notes = existing.get("Notes") or ""
            # Avoid duplicate date entries
            if report_date not in old_notes:
                new_notes = _truncate_notes(f"{notes_text}\n{old_notes}".strip())
                try:
                    from shared.notion_client import update_row
                    update_row(page_id, "campaigns", {"Notes": new_notes})
                    print(f"    \u2705 Updated: {camp_name} — {sessions} sessions")
                    written += 1
                except Exception as e:
                    print(f"    \u26a0\ufe0f  Update failed for {camp_name}: {e}")
        else:
            # Create new campaign row
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
                print(f"    \u2705 Created: {camp_name} — {sessions} sessions")
                written += 1
            except Exception as e:
                print(f"    \u26a0\ufe0f  Create failed for {camp_name}: {e}")

        # Also write a funnel_metrics row for this campaign
        try:
            add_row("funnel_metrics", {
                "Name": f"Campaign: {camp_name} — {report_date}",
                "Date": report_date,
                "Stage": f"Campaign: {camp_name}",
                "Count": sessions,
                "Period": "Daily",
                "Source": "ga4_campaign",
                "Conversion Rate": round(conversions / max(sessions, 1) * 100, 1) if sessions > 0 else 0,
                "Notes": _truncate_notes(notes_text),
            })
        except Exception:
            pass  # Non-fatal — KPI funnel row is optional

    print(f"    Done: {written} campaigns updated/created")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def run_daily_analytics(report_date: str | None = None) -> dict:
    """
    Collect all analytics and write to Notion.
    Returns summary dict for logging.
    """
    if not report_date:
        report_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 55)
    print("  DAILY ANALYTICS COLLECTOR")
    print(f"  Report date: {report_date}")
    print(f"  Run time:    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    # Step 0: Enrich Notion from Resend delivery data FIRST
    # This pulls open/click/bounce/delivered events from Resend API
    # and writes them back to Notion email_sends rows before we read stats.
    print("\n  [0/4] Enriching Notion from Resend delivery data …")
    try:
        sys.path.insert(0, _EMAIL_SYSTEM_DIR)
        from email_system import enrich_notion_from_resend
        enrich_notion_from_resend()
        print("    ✅ Enrichment complete — Notion now has latest Resend data")
    except Exception as e:
        print(f"    ⚠️  Enrichment failed (non-fatal): {e}")
        print("    Analytics will use existing Notion data (may be stale)")
    finally:
        # Remove from sys.path to avoid import conflicts
        if _EMAIL_SYSTEM_DIR in sys.path:
            sys.path.remove(_EMAIL_SYSTEM_DIR)
    print()

    # Collect
    email_stats = get_email_stats(report_date)
    supabase_stats = get_supabase_stats()
    lp_stats = get_landing_page_stats(report_date)
    lead_stats = get_lead_stats()

    # Update email_sequences DB with per-email delivery stats
    print("\n" + "─" * 55)
    try:
        update_email_sequence_stats(email_stats)
    except Exception as e:
        print(f"    ⚠️  Sequence stats update failed (non-fatal): {e}")

    # Write to Notion
    print("\n" + "─" * 55)
    write_kpi_snapshot(report_date, email_stats, supabase_stats, lp_stats, lead_stats)
    write_funnel_metrics(report_date, email_stats, supabase_stats, lp_stats, lead_stats)

    # Write campaign performance to Notion campaigns DB
    print("\n" + "─" * 55)
    try:
        write_campaign_stats(report_date, lp_stats)
    except Exception as e:
        print(f"    ⚠️  Campaign stats write failed (non-fatal): {e}")

    summary = {
        "date": report_date,
        "emails_total": email_stats["counts"]["total"],
        "emails_opened": email_stats["counts"]["opened"],
        "emails_clicked": email_stats["counts"]["clicked"],
        "emails_replied": email_stats["counts"]["replied"],
        "pageviews": lp_stats["pageviews"],
        "sessions": lp_stats.get("sessions", 0),
        "visitors": lp_stats["visitors"],
        "new_users": lp_stats.get("new_users", 0),
        "bounce_rate": lp_stats.get("bounce_rate", 0.0),
        "avg_session_duration": lp_stats.get("avg_session_duration", 0.0),
        "conversions": lp_stats.get("conversions", 0),
        "analytics_source": lp_stats.get("source", "unknown"),
        "total_users": supabase_stats["total_users"],
        "new_signups": supabase_stats["new_signups_24h"],
        "total_leads": lead_stats["total_leads"],
    }

    print("\n" + "─" * 55)
    print("  SUMMARY")
    for k, v in summary.items():
        print(f"    {k}: {v}")
    print("─" * 55)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedge Edge Daily Analytics Collector")
    parser.add_argument("--today", action="store_true", help="Report on today instead of yesterday")
    parser.add_argument("--date", type=str, help="Specific date to report on (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.date:
        dt = args.date
    elif args.today:
        dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    else:
        dt = None  # defaults to yesterday

    run_daily_analytics(dt)
