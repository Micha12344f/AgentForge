#!/usr/bin/env python3
"""
strategic_report.py — direct-source analytics reports.

Produces daily, weekly, and monthly analytical reports from primary sources:
  - GA4 for traffic and engagement
  - Supabase for signups, attribution, and platform activation
  - Resend for email delivery and audience health
  - Creem for subscription state

Notion is intentionally not used as the default report source here.

Usage:
    python strategic_report.py --action weekly
    python strategic_report.py --action weekly --days 7
    python strategic_report.py --action monthly
"""

import argparse
import os
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, *([".."] * 3)))


def _workspace_python() -> str | None:
    candidates = [
        os.path.join(_WORKSPACE, ".venv", "Scripts", "python.exe"),
        os.path.join(_WORKSPACE, ".venv", "bin", "python"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _bootstrap_workspace_python() -> None:
    preferred = _workspace_python()
    if not preferred:
        return
    current = os.path.abspath(sys.executable).lower()
    target = os.path.abspath(preferred).lower()
    if current == target:
        return
    result = subprocess.run(
        [preferred, os.path.abspath(__file__), *sys.argv[1:]],
        check=False,
    )
    sys.exit(result.returncode)


_bootstrap_workspace_python()
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from dotenv import load_dotenv

load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from license_tracking_report import build_license_tracking_bundle, build_summary
from shared.creem_client import list_subscriptions
from shared.google_analytics_client import (
    get_avg_session_duration,
    get_bounce_rate,
    get_page_views,
    get_sessions,
    get_top_pages,
    get_traffic_sources,
    get_visitors,
)
from shared.notion_client import log_task
from shared.resend_client import list_contacts, list_emails
from shared.supabase_client import get_supabase


DEFAULT_RESEND_AUDIENCE_ID = os.getenv(
    "RESEND_AUDIENCE_ID",
    "17895b10-363b-47d7-9784-477131568f7f",
)


@dataclass(frozen=True)
class PeriodWindow:
    label: str
    days: int
    start: date
    end: date
    previous_start: date
    previous_end: date


def _normalize_action(action: str) -> tuple[str, int]:
    aliases = {
        "daily": ("daily", 1),
        "daily-report": ("daily", 1),
        "weekly": ("weekly", 7),
        "weekly-report": ("weekly", 7),
        "monthly": ("monthly", 30),
        "monthly-report": ("monthly", 30),
    }
    if action not in aliases:
        raise ValueError(f"Unsupported report action: {action}")
    return aliases[action]


def _build_window(label: str, days: int) -> PeriodWindow:
    end = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return PeriodWindow(
        label=label,
        days=days,
        start=start,
        end=end,
        previous_start=previous_start,
        previous_end=previous_end,
    )


def _window_bounds(start: date, end: date) -> tuple[str, str]:
    start_iso = f"{start.isoformat()}T00:00:00+00:00"
    end_iso = f"{(end + timedelta(days=1)).isoformat()}T00:00:00+00:00"
    return start_iso, end_iso


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 1)


def _change_str(current: float, previous: float, suffix: str = "") -> str:
    diff = current - previous
    if diff == 0:
        return f"0{suffix}"
    sign = "+" if diff > 0 else ""
    if isinstance(current, int) and isinstance(previous, int):
        return f"{sign}{int(diff)}{suffix}"
    return f"{sign}{diff:.1f}{suffix}"


def _pct_change(current: float, previous: float) -> str:
    if not previous:
        return "n/a"
    pct = ((current - previous) / abs(previous)) * 100
    return f"{pct:+.1f}%"


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_source_counter(counter: Counter[str], limit: int = 3) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{name} ({count})" for name, count in counter.most_common(limit))


def _collect_supabase_pageviews(start: date, end: date) -> dict[str, Any]:
    sb = get_supabase(use_service_role=True)
    start_iso, end_iso = _window_bounds(start, end)
    rows = (
        sb.table("page_views")
        .select("id, path, utm_source, utm_campaign, user_agent")
        .gte("created_at", start_iso)
        .lt("created_at", end_iso)
        .execute()
        .data
        or []
    )

    by_path: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    unique_agents: set[str] = set()
    for row in rows:
        by_path[row.get("path") or "/"] += 1
        by_source[row.get("utm_source") or "direct"] += 1
        user_agent = row.get("user_agent") or ""
        if user_agent:
            unique_agents.add(user_agent)

    return {
        "available": True,
        "source": "supabase",
        "pageviews": len(rows),
        "sessions": 0,
        "visitors": len(unique_agents),
        "avg_session_duration": 0.0,
        "bounce_rate": 0.0,
        "top_pages": [{"pagePath": key, "screenPageViews": value} for key, value in by_path.most_common(5)],
        "top_sources": [{"sessionSource": key, "sessions": value} for key, value in by_source.most_common(5)],
    }


def _collect_traffic(start: date, end: date) -> dict[str, Any]:
    start_iso = start.isoformat()
    end_iso = end.isoformat()
    try:
        return {
            "available": True,
            "source": "ga4",
            "pageviews": get_page_views(start_iso, end_iso),
            "sessions": get_sessions(start_iso, end_iso),
            "visitors": get_visitors(start_iso, end_iso),
            "avg_session_duration": get_avg_session_duration(start_iso, end_iso),
            "bounce_rate": get_bounce_rate(start_iso, end_iso),
            "top_pages": get_top_pages(start_iso, end_iso, limit=5),
            "top_sources": get_traffic_sources(start_iso, end_iso, limit=5),
        }
    except Exception as exc:
        try:
            fallback = _collect_supabase_pageviews(start, end)
            fallback["note"] = f"GA4 unavailable: {exc}"
            return fallback
        except Exception as fallback_exc:
            return {
                "available": False,
                "source": "none",
                "error": f"GA4 unavailable: {exc}; Supabase fallback unavailable: {fallback_exc}",
            }


def _collect_conversions(start: date, end: date) -> dict[str, Any]:
    sb = get_supabase(use_service_role=True)
    start_iso, end_iso = _window_bounds(start, end)
    rows = (
        sb.table("user_attribution")
        .select("ref, utm_source, utm_medium, utm_campaign, signup_method, created_at")
        .gte("created_at", start_iso)
        .lt("created_at", end_iso)
        .order("created_at", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )

    by_source: Counter[str] = Counter()
    by_method: Counter[str] = Counter()
    by_campaign: Counter[str] = Counter()
    for row in rows:
        by_source[row.get("utm_source") or "direct"] += 1
        by_method[row.get("signup_method") or "unknown"] += 1
        by_campaign[row.get("utm_campaign") or "none"] += 1

    return {
        "available": True,
        "count": len(rows),
        "by_source": by_source,
        "by_method": by_method,
        "by_campaign": by_campaign,
        "rows": rows,
    }


def _email_stage_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    delivered_states = {"delivered", "opened", "clicked", "complained"}
    opened_states = {"opened", "clicked"}
    clicked_states = {"clicked"}
    bounced_states = {"bounced", "failed"}

    sent = len(rows)
    delivered = sum(1 for row in rows if (row.get("last_event") or "").lower() in delivered_states)
    opened = sum(1 for row in rows if (row.get("last_event") or "").lower() in opened_states)
    clicked = sum(1 for row in rows if (row.get("last_event") or "").lower() in clicked_states)
    bounced = sum(1 for row in rows if (row.get("last_event") or "").lower() in bounced_states)
    pending = max(sent - delivered - bounced, 0)

    return {
        "sent": sent,
        "delivered": delivered,
        "opened": opened,
        "clicked": clicked,
        "bounced": bounced,
        "pending": pending,
    }


def _collect_email(start: date, end: date, *, max_rows: int = 1000) -> dict[str, Any]:
    emails = list_emails(limit=max_rows)
    start_ts, end_ts = _window_bounds(start, end)
    start_dt = _parse_timestamp(start_ts)
    end_dt = _parse_timestamp(end_ts)
    filtered: list[dict[str, Any]] = []

    for row in emails:
        created = _parse_timestamp(row.get("created_at"))
        if created is None or start_dt is None or end_dt is None:
            continue
        if start_dt <= created < end_dt:
            filtered.append(row)

    stage = _email_stage_counts(filtered)
    by_subject: Counter[str] = Counter((row.get("subject") or "Untitled") for row in filtered)

    audience_contacts = list_contacts(DEFAULT_RESEND_AUDIENCE_ID)
    unsubscribed = sum(1 for row in audience_contacts if row.get("unsubscribed") is True)

    return {
        "available": True,
        "sent": stage["sent"],
        "delivered": stage["delivered"],
        "opened": stage["opened"],
        "clicked": stage["clicked"],
        "bounced": stage["bounced"],
        "pending": stage["pending"],
        "delivery_rate": _pct(stage["delivered"], stage["sent"]),
        "open_rate": _pct(stage["opened"], stage["delivered"]),
        "click_rate": _pct(stage["clicked"], stage["delivered"]),
        "audience_contacts": len(audience_contacts),
        "audience_unsubscribed": unsubscribed,
        "top_subjects": by_subject,
    }


def _collect_subscriptions(start: date, end: date) -> dict[str, Any]:
    subs = list_subscriptions(use_test=False, limit=250)
    active_statuses = {"active", "trialing"}
    active = [row for row in subs if (row.get("status") or "").lower() in active_statuses]
    start_dt, end_dt = _window_bounds(start, end)
    start_ts = _parse_timestamp(start_dt)
    end_ts = _parse_timestamp(end_dt)
    new_in_window = 0
    for row in subs:
        created = _parse_timestamp(row.get("created_at"))
        if created and start_ts and end_ts and start_ts <= created < end_ts:
            new_in_window += 1

    return {
        "available": True,
        "active_count": len(active),
        "new_count": new_in_window,
    }


def _collect_license(days: int) -> dict[str, Any]:
    bundle = build_license_tracking_bundle(days=days)
    summary = build_summary(bundle)
    return {
        "available": True,
        "summary": summary,
    }


def _collect_period(window: PeriodWindow) -> dict[str, Any]:
    data: dict[str, Any] = {"window": window}
    issues: list[str] = []

    try:
        data["traffic"] = _collect_traffic(window.start, window.end)
        if not data["traffic"].get("available"):
            issues.append(data["traffic"].get("error", "Traffic unavailable"))
        elif data["traffic"].get("note"):
            issues.append(data["traffic"]["note"])
    except Exception as exc:
        data["traffic"] = {"available": False, "error": str(exc)}
        issues.append(f"Traffic unavailable: {exc}")

    try:
        data["conversions"] = _collect_conversions(window.start, window.end)
    except Exception as exc:
        data["conversions"] = {"available": False, "error": str(exc), "count": 0, "by_source": Counter()}
        issues.append(f"Supabase conversions unavailable: {exc}")

    try:
        data["email"] = _collect_email(window.start, window.end)
    except Exception as exc:
        data["email"] = {"available": False, "error": str(exc)}
        issues.append(f"Resend email data unavailable: {exc}")

    try:
        data["subscriptions"] = _collect_subscriptions(window.start, window.end)
    except Exception as exc:
        data["subscriptions"] = {"available": False, "error": str(exc)}
        issues.append(f"Creem subscription data unavailable: {exc}")

    try:
        data["license"] = _collect_license(window.days)
    except Exception as exc:
        data["license"] = {"available": False, "error": str(exc)}
        issues.append(f"License telemetry unavailable: {exc}")

    data["issues"] = issues
    return data


def _build_insights(current: dict[str, Any], previous: dict[str, Any]) -> tuple[list[str], list[str]]:
    insights: list[str] = []
    improvements: list[str] = []

    traffic = current.get("traffic", {})
    prev_traffic = previous.get("traffic", {})
    if traffic.get("available") and prev_traffic.get("available"):
        pageviews = _safe_int(traffic.get("pageviews"))
        prev_pageviews = _safe_int(prev_traffic.get("pageviews"))
        sessions = _safe_int(traffic.get("sessions"))
        prev_sessions = _safe_int(prev_traffic.get("sessions"))
        insights.append(
            f"Traffic source: {traffic.get('source')} with {pageviews} page views and {sessions} sessions ({_pct_change(pageviews, prev_pageviews)} page views vs prior window)."
        )
        top_page = (traffic.get("top_pages") or [{}])[0]
        if top_page.get("pagePath"):
            insights.append(
                f"Top landing path was {top_page.get('pagePath')} with {_safe_int(top_page.get('screenPageViews'))} views."
            )

    conversions = current.get("conversions", {})
    prev_conversions = previous.get("conversions", {})
    if conversions.get("available") and prev_conversions.get("available"):
        count = _safe_int(conversions.get("count"))
        prev_count = _safe_int(prev_conversions.get("count"))
        top_source = _format_source_counter(conversions.get("by_source", Counter()), limit=1)
        insights.append(
            f"Supabase recorded {count} signups ({_pct_change(count, prev_count)} vs prior window); top source was {top_source}."
        )
        direct_share = _pct(conversions.get("by_source", Counter()).get("direct", 0), max(count, 1))
        if direct_share >= 40:
            improvements.append(
                f"Direct signups are {direct_share:.1f}% of measured conversions; tighten UTM discipline across Growth links. → @growth"
            )

    license_data = current.get("license", {})
    if license_data.get("available"):
        summary = license_data["summary"]
        rate = _safe_float(summary.get("platform_activation_rate"))
        desktop_only = _safe_int(summary.get("desktop_only"))
        if desktop_only > 0:
            insights.append(
                f"Platform Activation Rate is {rate:.1f}% with {desktop_only} desktop-only users still short of real activation."
            )
        else:
            insights.append(
                f"Platform Activation Rate is {rate:.1f}% and the remaining gap is coming from not-activated license holders rather than desktop-only installs."
            )
        if rate < 30:
            if desktop_only > 0:
                improvements.append(
                    "Platform activation is below the alert floor; prioritize onboarding fixes and desktop-only follow-up before acquiring more top-of-funnel volume. → @growth @strategy"
                )
            else:
                improvements.append(
                    "Platform activation is below the alert floor; focus Growth and Strategy on moving not-activated license holders to a first confirmed platform connection before pushing more acquisition volume. → @growth @strategy"
                )
        elif rate < 60:
            improvements.append(
                "Platform activation is below target; use license health outreach to move warming-up and onboarding-help users into confirmed platform activation. → @growth"
            )

    email = current.get("email", {})
    prev_email = previous.get("email", {})
    if email.get("available") and prev_email.get("available"):
        sent = _safe_int(email.get("sent"))
        prev_sent = _safe_int(prev_email.get("sent"))
        delivery_rate = _safe_float(email.get("delivery_rate"))
        click_rate = _safe_float(email.get("click_rate"))
        if sent > 0:
            insights.append(
                f"Resend logged {sent} emails with {delivery_rate:.1f}% delivery and {click_rate:.1f}% click-through ({_pct_change(sent, prev_sent)} sends vs prior window)."
            )
            if delivery_rate < 95:
                improvements.append(
                    "Delivery rate is below 95%; review recipient hygiene and bounce handling before scaling sequences. → @growth"
                )
            if click_rate < 3:
                improvements.append(
                    "Email click-through is below the 3% KPI target; tighten CTA clarity and segment relevance on the highest-volume subjects. → @growth"
                )
        else:
            insights.append("No Resend sends landed in the current window, so email performance is neutral rather than weak.")

    subscriptions = current.get("subscriptions", {})
    prev_subscriptions = previous.get("subscriptions", {})
    if subscriptions.get("available") and prev_subscriptions.get("available"):
        active_count = _safe_int(subscriptions.get("active_count"))
        prev_active_count = _safe_int(prev_subscriptions.get("active_count"))
        insights.append(
            f"Creem reports {active_count} active subscriptions ({_change_str(active_count, prev_active_count)} vs prior snapshot) and {_safe_int(subscriptions.get('new_count'))} new subscriptions in-window."
        )

    if not improvements:
        improvements.append("No structural KPI breach is visible in the current window; keep using direct-source reporting and watch attribution quality plus platform activation first.")

    return insights[:4], improvements[:4]


def render_report(action: str, days: int) -> str:
    window = _build_window(action, days)
    previous_window = PeriodWindow(
        label=f"previous-{window.label}",
        days=window.days,
        start=window.previous_start,
        end=window.previous_end,
        previous_start=window.previous_start - timedelta(days=window.days),
        previous_end=window.previous_start - timedelta(days=1),
    )

    current = _collect_period(window)
    previous = _collect_period(previous_window)
    insights, improvements = _build_insights(current, previous)

    traffic = current.get("traffic", {})
    conversions = current.get("conversions", {})
    email = current.get("email", {})
    subscriptions = current.get("subscriptions", {})
    license_data = current.get("license", {})
    license_summary = license_data.get("summary", {}) if license_data.get("available") else {}

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f"STRATEGIC {window.label.upper()} ANALYTICAL REPORT")
    lines.append("=" * 72)
    lines.append(f"Period: {window.start.isoformat()} -> {window.end.isoformat()} UTC")
    lines.append("Source order: GA4 -> Supabase -> Resend -> Creem | Notion mirrors excluded")
    lines.append("")
    lines.append("Summary")
    if traffic.get("available"):
        lines.append(
            f"  Traffic ({traffic.get('source')}): {_safe_int(traffic.get('pageviews'))} page views, {_safe_int(traffic.get('sessions'))} sessions, {_safe_int(traffic.get('visitors'))} visitors"
        )
    else:
        lines.append("  Traffic: unavailable")
    if conversions.get("available"):
        lines.append(
            f"  Signups (Supabase): {_safe_int(conversions.get('count'))} | top sources: {_format_source_counter(conversions.get('by_source', Counter()))}"
        )
    else:
        lines.append("  Signups: unavailable")
    if email.get("available"):
        if _safe_int(email.get("sent")) > 0:
            lines.append(
                f"  Email (Resend): {_safe_int(email.get('sent'))} sent, {_safe_float(email.get('delivery_rate')):.1f}% delivered, {_safe_float(email.get('click_rate')):.1f}% clicked"
            )
        else:
            lines.append("  Email (Resend): no sends in-window")
    else:
        lines.append("  Email: unavailable")
    if subscriptions.get("available"):
        lines.append(
            f"  Subscriptions (Creem): {_safe_int(subscriptions.get('active_count'))} active, {_safe_int(subscriptions.get('new_count'))} new in-window"
        )
    else:
        lines.append("  Subscriptions: unavailable")
    if license_data.get("available"):
        lines.append(
            f"  Platform activation (Supabase): {_safe_float(license_summary.get('platform_activation_rate')):.1f}% | desktop-only {_safe_int(license_summary.get('desktop_only'))}"
        )
    else:
        lines.append("  Platform activation: unavailable")

    if traffic.get("available") and traffic.get("top_pages"):
        lines.append("")
        lines.append("Top pages")
        for row in traffic.get("top_pages", [])[:5]:
            path = row.get("pagePath") or row.get("path") or "/"
            views = _safe_int(row.get("screenPageViews") or row.get("views"))
            lines.append(f"  - {path}: {views}")

    lines.append("")
    lines.append("Insights")
    for item in insights:
        lines.append(f"  - {item}")

    lines.append("")
    lines.append("Improvements")
    for item in improvements:
        lines.append(f"  - {item}")

    coverage_gaps = list(dict.fromkeys(current.get("issues", [])))
    if coverage_gaps:
        lines.append("")
        lines.append("Coverage")
        for issue in coverage_gaps:
            lines.append(f"  - {issue}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Strategic direct-source analytics report")
    parser.add_argument(
        "--action",
        required=True,
        choices=["daily", "weekly", "monthly", "daily-report", "weekly-report", "monthly-report"],
    )
    parser.add_argument("--days", type=int, default=None, help="Override lookback window in completed UTC days")
    args = parser.parse_args()

    action, default_days = _normalize_action(args.action)
    days = args.days or default_days
    report = render_report(action, days)
    print(report)

    try:
        log_task(
            "Analytics",
            f"report/{action}",
            "Complete",
            "P2",
            report[:200],
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()