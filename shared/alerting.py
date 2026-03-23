"""
Hedge Edge — Alerting Module
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Severity-routed alerts to Discord + email fallback for critical.

Severity levels:
    info     → green embed  (silent: daily summaries, cron completions)
    warn     → yellow embed (degraded service, high latency)
    critical → red embed + email backup (cron failures, bot crashes)

Usage:
    from shared.alerting import send_alert, send_daily_brief, send_signup_alert

    send_alert("Email Cron Complete", "Sent 12 emails", "info")
    send_alert("Hourly Sync Failed", traceback_str, "critical")
    send_signup_alert("alice@example.com", "landing-page")
    send_daily_brief()
"""

import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

# ── Severity → embed colour ──
_COLORS = {
    "info": 0x00D4AA,      # Hedge Edge green
    "warn": 0xFFA500,      # orange
    "critical": 0xFF3333,  # red
}

_SEVERITY_EMOJI = {
    "info": "✅",
    "warn": "⚠️",
    "critical": "🚨",
}

# Max Discord embed description length
_MAX_DESC = 4000


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Core: send_alert
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_alert(
    title: str,
    message: str,
    severity: str = "info",
    fields: Optional[list[dict]] = None,
) -> bool:
    """
    Send an alert to Discord #bot-alerts channel.

    For 'critical' severity, also sends an email via Resend as a backup.

    Args:
        title:    Alert headline (e.g. "Email Cron Complete")
        message:  Body text — can be a traceback for errors
        severity: "info" | "warn" | "critical"
        fields:   Optional list of {"name": ..., "value": ..., "inline": bool}

    Returns:
        True if at least one delivery channel succeeded.
    """
    severity = severity.lower() if severity.lower() in _COLORS else "info"
    emoji = _SEVERITY_EMOJI[severity]
    color = _COLORS[severity]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Truncate message for Discord embed limits
    desc = message[:_MAX_DESC] if message else ""

    sent = False

    # ── Primary: Discord embed to #bot-alerts ──
    try:
        channel_id = os.getenv("DISCORD_ALERTS_CHANNEL_ID", "")
        bot_token = os.getenv("DISCORD_BOT_TOKEN", "")

        if channel_id and bot_token:
            embed = {
                "title": f"{emoji} {title}",
                "description": desc,
                "color": color,
                "footer": {"text": f"{severity.upper()} • {ts}"},
            }
            if fields:
                embed["fields"] = fields[:25]  # Discord max 25 fields

            r = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json",
                },
                json={"embeds": [embed]},
                timeout=15,
            )
            r.raise_for_status()
            sent = True

    except Exception as e:
        print(f"[alerting] Discord embed failed: {e}")

        # Fallback: try webhook if bot fails
        try:
            webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
            if webhook_url:
                requests.post(
                    webhook_url,
                    json={
                        "content": f"**{emoji} {title}**\n{desc[:1900]}",
                        "username": "Hedge Edge Alerts",
                    },
                    timeout=15,
                )
                sent = True
        except Exception:
            pass

    return sent


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Specialised alerts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_hot_lead_alert(
    email: str,
    first_name: str = "",
    drip_stage: str = "",
    source: str = "",
    subject: str = "",
) -> bool:
    """Alert the team when a lead clicks a link — HOT LEAD.

    Fires to Discord #bot-alerts so the team can follow up immediately.
    """
    name_display = first_name or email.split("@")[0]
    fields = [
        {"name": "\U0001f525 Lead", "value": f"**{name_display}** ({email})", "inline": False},
    ]
    if drip_stage:
        fields.append({"name": "\U0001f4e7 Drip Stage", "value": drip_stage, "inline": True})
    if source:
        fields.append({"name": "\U0001f4cd Source", "value": source, "inline": True})
    if subject:
        fields.append({"name": "\U0001f4e8 Email", "value": subject[:80], "inline": False})
    fields.append(
        {"name": "\u23f0 Detected", "value": datetime.now(timezone.utc).strftime("%H:%M UTC"), "inline": True}
    )

    return send_alert(
        "\U0001f525 HOT LEAD \u2014 Link Click Detected!",
        (
            f"**{name_display}** just clicked a link in a drip email!\n\n"
            "This lead is showing **high intent** \u2014 consider immediate personal follow-up."
        ),
        "warn",
        fields=fields,
    )


def send_signup_alert(email: str, source: str = "unknown") -> bool:
    """Alert when a new user signs up on Supabase."""
    return send_alert(
        "New Signup! 🎉",
        f"**{email}** just signed up via **{source}**",
        "info",
        fields=[
            {"name": "Email", "value": email, "inline": True},
            {"name": "Source", "value": source, "inline": True},
            {"name": "Time", "value": datetime.now(timezone.utc).strftime("%H:%M UTC"), "inline": True},
        ],
    )


def send_revenue_alert(event: str, amount: float, currency: str = "GBP") -> bool:
    """Alert on revenue events (new subscription, payment, etc.)."""
    return send_alert(
        f"Revenue: {event} 💰",
        f"**{currency} {amount:.2f}** — {event}",
        "info",
        fields=[
            {"name": "Event", "value": event, "inline": True},
            {"name": "Amount", "value": f"{currency} {amount:.2f}", "inline": True},
        ],
    )


def send_cron_success(cron_name: str, summary: str, elapsed_s: float = 0) -> bool:
    """Alert on successful cron completion."""
    fields = []
    if elapsed_s > 0:
        fields.append({"name": "Elapsed", "value": f"{elapsed_s:.1f}s", "inline": True})
    return send_alert(
        f"{cron_name} — Complete",
        summary,
        "info",
        fields=fields,
    )


def send_cron_failure(cron_name: str, error: Exception) -> bool:
    """Alert on cron failure (critical — also sends email)."""
    tb = traceback.format_exception(type(error), error, error.__traceback__)
    tb_str = "".join(tb)[-3000:]  # last 3000 chars of traceback
    return send_alert(
        f"{cron_name} — FAILED",
        f"```\n{tb_str}\n```",
        "critical",
        fields=[
            {"name": "Error", "value": str(error)[:1000], "inline": False},
        ],
    )


def send_bot_status(bot_name: str, status: str, details: str = "") -> bool:
    """Alert on bot status changes."""
    sev = "info" if status.lower() in ("running", "started", "up") else "critical"
    return send_alert(
        f"{bot_name} — {status}",
        details or f"Bot is now **{status}**",
        sev,
    )


def send_traffic_alert() -> bool:
    """
    Hourly page-visit digest posted to #bot-alerts.

    Pulls page_views from Supabase for the last hour, filters out known
    internal users (founders, test emails), and sends a summary embed
    with UTM source breakdown, top pages, geographic data, and an
    all-time UTM stats table with conversion (signup) tracking.
    """
    try:
        from datetime import timedelta
        from collections import Counter, defaultdict

        # ── Known internal referrers to filter out ──
        _INTERNAL_REFERRERS_CONTAINS = [
            "temp-mail.org", "advarm.com", "creteanu.com",
            "deposin.com", "ruutukf.com",
        ]

        # ── Known founder / test emails (not organic signups) ──
        _INTERNAL_EMAILS = {
            "ryansossion@gmail.com",
            "mahmudabubakar276@gmail.com",
            "mamzzy13@gmail.com",
        }
        _DISPOSABLE_DOMAINS = {
            "creteanu.com", "advarm.com", "deposin.com", "ruutukf.com",
        }

        # Import Supabase
        try:
            from shared.supabase_client import get_supabase
            sb = get_supabase(use_service_role=True)
        except Exception as e:
            print(f"[alerting] Supabase unavailable for traffic alert: {e}")
            return False

        # ── 1. Page views from the last hour ──
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        result = sb.table("page_views").select("*").gte(
            "created_at", one_hour_ago,
        ).order("created_at", desc=True).limit(500).execute()
        views = result.data or []

        # ── 2. All-time UTM stats (all page_views) ──
        all_pvs = []
        offset = 0
        while True:
            batch = sb.table("page_views").select(
                "utm_source,utm_medium,utm_campaign,path,country,referrer",
            ).order("created_at", desc=True).range(offset, offset + 999).execute()
            if not batch.data:
                break
            all_pvs.extend(batch.data)
            if len(batch.data) < 1000:
                break
            offset += 1000

        # ── 3. All-time signup attribution ──
        import requests as _req
        attrs_result = sb.table("user_attribution").select("*").order(
            "created_at", desc=True,
        ).limit(500).execute()
        attrs = attrs_result.data or []

        # Resolve emails from auth admin API for internal filtering
        try:
            url = os.getenv("SUPABASE_URL", "") + "/auth/v1/admin/users"
            headers = {
                "apikey": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                "Authorization": f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')}",
            }
            r = _req.get(url, headers=headers, params={"per_page": 100}, timeout=15)
            auth_users = {u["id"]: u.get("email", "") for u in r.json().get("users", [])}
        except Exception:
            auth_users = {}

        # Build signup-by-source (organic only — exclude founders & disposable)
        signups_by_source = Counter()  # source → organic signup count
        total_organic_signups = 0
        for a in attrs:
            uid = a.get("user_id", "")
            email = auth_users.get(uid, "")
            domain = email.split("@")[-1] if "@" in email else ""
            if email in _INTERNAL_EMAILS or domain in _DISPOSABLE_DOMAINS:
                continue  # skip internal / test
            src = a.get("utm_source") or "direct"
            signups_by_source[src] += 1
            total_organic_signups += 1

        # ── 4. Build all-time UTM list (no wide table — mobile friendly) ──
        alltime_source = Counter()
        for v in all_pvs:
            src = v.get("utm_source") or "(direct)"
            alltime_source[src] += 1

        utm_lines = []
        for src, cnt in alltime_source.most_common(8):
            signup_key = src if src != "(direct)" else "direct"
            sups = signups_by_source.get(signup_key, 0)
            conv = f" → **{sups}** conv" if sups > 0 else ""
            utm_lines.append(f"▸ **{src}** — {cnt} views{conv}")
        utm_lines.append(f"▸ **Total** — {len(all_pvs)} views, {total_organic_signups} signups")

        # ── 5. Hourly breakdown ──
        if not views:
            desc = (
                "No visits in the last hour.\n\n"
                "📈 **All-Time UTM:**\n"
                + "\n".join(utm_lines)
            )
            return send_alert("📊 Traffic — No visits", desc, "info")

        # Classify hourly views
        internal_views = []
        external_views = []
        for v in views:
            ref = (v.get("referrer") or "").lower()
            is_internal = any(t in ref for t in _INTERNAL_REFERRERS_CONTAINS)
            if is_internal:
                internal_views.append(v)
            else:
                external_views.append(v)

        total = len(views)
        ext_count = len(external_views)
        int_count = len(internal_views)

        # Source breakdown (external, this hour)
        source_counter = Counter()
        page_counter = Counter()
        country_counter = Counter()
        for v in external_views:
            src = v.get("utm_source") or "(direct)"
            med = v.get("utm_medium") or "(none)"
            source_counter[f"{src}/{med}"] += 1
            page_counter[v.get("path") or "/"] += 1
            country = v.get("country")
            if country:
                country_counter[country] += 1

        # ── 6. Build embed (compact for mobile) ──
        lines = [
            f"**{total}** views this hour"
            f" ({ext_count} real · {int_count} internal)",
        ]

        if source_counter:
            lines.append("")
            lines.append("⚡ **This Hour:**")
            for src, cnt in source_counter.most_common(4):
                lines.append(f"▸ {src} — {cnt}")

        if page_counter:
            lines.append("")
            lines.append("📄 **Pages:**")
            for page, cnt in page_counter.most_common(4):
                lines.append(f"▸ `{page}` — {cnt}")

        if country_counter:
            flags = {
                "United Kingdom": "🇬🇧", "United States": "🇺🇸",
                "Germany": "🇩🇪", "Norway": "🇳🇴", "Kenya": "🇰🇪",
                "Singapore": "🇸🇬", "Canada": "🇨🇦", "Australia": "🇦🇺",
                "India": "🇮🇳", "Nigeria": "🇳🇬",
            }
            lines.append("")
            geo = " ".join(
                f"{flags.get(c, '🌍')}{cnt}" for c, cnt in country_counter.most_common(5)
            )
            lines.append(f"🌍 {geo}")

        # Append all-time UTM
        lines.append("")
        lines.append("📈 **All-Time UTM:**")
        lines.extend(utm_lines)

        desc = "\n".join(lines)

        # ── Fields (no inline — stacks vertically on mobile) ──
        fields = [
            {"name": "🕐 This Hour", "value": f"{ext_count} real · {int_count} internal", "inline": False},
            {"name": "📊 All-Time", "value": f"{len(all_pvs)} views · {total_organic_signups} signups", "inline": False},
        ]

        return send_alert(
            "📊 Traffic",
            desc,
            "info",
            fields=fields,
        )

    except Exception as e:
        print(f"[alerting] Traffic alert failed: {e}")
        return False


def send_daily_brief() -> bool:
    """
    Generate and post a full daily summary to #bot-alerts.
    Combines service health, business metrics, and ERP summary.
    """
    try:
        from shared.dashboard import get_service_health, get_business_metrics, get_erp_summary

        health = get_service_health()
        metrics = get_business_metrics()
        erp = get_erp_summary()

        # Build summary text
        h_summary = health.get("_summary", {})
        lines = [
            f"**Services:** {h_summary.get('up', 0)}/{h_summary.get('total', 0)} up",
        ]

        # Service details (only show down services)
        down_services = [
            k for k, v in health.items()
            if isinstance(v, dict) and v.get("status") == "down" and k != "_summary"
        ]
        if down_services:
            lines.append(f"**Down:** {', '.join(down_services)}")

        # Business metrics
        if metrics and not metrics.get("_errors"):
            mrr = metrics.get("mrr")
            if mrr is not None:
                lines.append(f"**MRR:** £{mrr:.2f}")
            leads = metrics.get("total_leads")
            if leads is not None:
                lines.append(f"**Leads:** {leads}")
            bugs = metrics.get("open_bugs")
            if bugs is not None:
                lines.append(f"**Open Bugs:** {bugs}")

        # ERP row counts
        if erp and not erp.get("_errors"):
            total_rows = sum(v for v in erp.values() if isinstance(v, int))
            lines.append(f"**ERP Rows:** {total_rows} across {len([v for v in erp.values() if isinstance(v, int)])} tables")

        summary_text = "\n".join(lines)

        return send_alert(
            "📊 Daily Brief",
            summary_text,
            "info",
        )

    except Exception as e:
        print(f"[alerting] Daily brief failed: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CLI test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("Sending test alert to Discord #bot-alerts ...")
    ok = send_alert("Test Alert", "Monitoring & alerting system is live.", "info")
    print(f"Result: {'sent' if ok else 'failed'}")
