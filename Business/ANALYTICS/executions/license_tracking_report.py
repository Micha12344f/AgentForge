#!/usr/bin/env python3
"""
license_tracking_report.py - License telemetry and customer health reporting.

Pulls live data from Supabase and produces repeatable analytics views for the
license system: registry, activation, last activity, cadence, device fleet,
error signals, and a unified customer health dashboard.

Usage:
    python license_tracking_report.py --action summary
    python license_tracking_report.py --action dashboard --days 30
    python license_tracking_report.py --action errors --days 30
    python license_tracking_report.py --action fleet --days 30
    python license_tracking_report.py --action export-json --days 30
"""

import argparse
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd
from dotenv import load_dotenv

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_AGENT_DIR, "..", "..", ".."))
sys.path.insert(0, _WORKSPACE)

load_dotenv(os.path.join(_WORKSPACE, ".env"), override=True)

from shared.supabase_client import get_supabase


@dataclass
class LicenseTrackingBundle:
    licenses: pd.DataFrame
    activations: pd.DataFrame
    merged: pd.DataFrame
    fleet: pd.DataFrame
    errors: pd.DataFrame
    health: pd.DataFrame
    days: int
    since: str


def _safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="mixed", utc=True, errors="coerce")


def _truncate_key(value: str, length: int = 12) -> str:
    if not isinstance(value, str):
        return ""
    return value[:length] + "..." if len(value) > length else value


def _log_key_candidates(full_key: str) -> list[str]:
    if not isinstance(full_key, str):
        return []
    candidates = [full_key]
    truncated = full_key[:20] + "..." if len(full_key) > 20 else full_key
    if truncated not in candidates:
        candidates.append(truncated)
    short = _truncate_key(full_key)
    if short not in candidates:
        candidates.append(short)
    return candidates


def _stringify_timestamp(value) -> str:
    if pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def _health_score(row: pd.Series) -> str:
    """Compute health label incorporating Platform Activation status.

    Platform Activation (mt5/mt4/ctrader with persistent device) is the
    ultimate conversion indicator. Desktop-only validation does NOT count
    as activation. See: ANALYTICS/directives/platform-activation-indicator.md
    """
    if row.get("activated_at") == "NEVER":
        return "NOT ACTIVATED"
    platform_activated = row.get("platform_activated", False)
    if not platform_activated and row.get("days_since_key", 0) > 7:
        return "NEEDS_ONBOARDING_HELP"  # Desktop opened but EA never connected
    if platform_activated and row.get("status") == "AT RISK":
        return "CHURNING"
    if row.get("errors_30d", 0) > 10:
        return "NEEDS SUPPORT"
    if platform_activated and row.get("engagement") in {"POWER USER", "REGULAR"}:
        return "HEALTHY"
    if platform_activated and row.get("engagement") == "LOW":
        return "WARMING UP"
    if not platform_activated:
        return "DESKTOP_ONLY"  # App opened but EA not connected to chart
    return "DORMANT"


def build_license_tracking_bundle(days: int = 30) -> LicenseTrackingBundle:
    db = get_supabase(use_service_role=True)
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    licenses_raw = (
        db.table("licenses")
        .select("id, license_key, email, plan, max_devices, is_active, created_at, expires_at")
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )
    licenses = pd.DataFrame(licenses_raw)

    if licenses.empty:
        return LicenseTrackingBundle(
            licenses=pd.DataFrame(),
            activations=pd.DataFrame(),
            merged=pd.DataFrame(),
            fleet=pd.DataFrame(),
            errors=pd.DataFrame(),
            health=pd.DataFrame(),
            days=days,
            since=since,
        )

    licenses["created_at"] = _safe_to_datetime(licenses["created_at"])
    licenses["expires_at"] = _safe_to_datetime(licenses["expires_at"])
    licenses["key_short"] = licenses["license_key"].apply(_truncate_key)
    licenses["created_at_str"] = licenses["created_at"].dt.strftime("%Y-%m-%d")
    licenses["expires_at_str"] = licenses["expires_at"].dt.strftime("%Y-%m-%d")

    success_logs_raw = (
        db.table("license_validation_logs")
        .select("license_key, created_at")
        .eq("success", True)
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )
    success_logs = pd.DataFrame(success_logs_raw)
    if not success_logs.empty:
        success_logs["created_at"] = _safe_to_datetime(success_logs["created_at"])
        activations = (
            success_logs.groupby("license_key")["created_at"]
            .min()
            .reset_index()
            .rename(columns={"created_at": "activated_ts"})
        )
        activation_map = dict(zip(activations["license_key"], activations["activated_ts"]))
    else:
        activations = pd.DataFrame(columns=["license_key", "activated_ts"])
        activation_map = {}

    def lookup_activation(full_key: str) -> str:
        for candidate in _log_key_candidates(full_key):
            ts = activation_map.get(candidate)
            if pd.notna(ts):
                return _stringify_timestamp(ts)
        return "NEVER"

    licenses["activated_at"] = licenses["license_key"].apply(lookup_activation)

    # ── Platform Activation check (ultimate conversion indicator) ──
    # A user is only truly converted when platform IN (mt5, mt4, ctrader)
    # with a persistent device row. Desktop-only does NOT count.
    PLATFORM_VALUES = ('mt5', 'mt4', 'ctrader')
    TEST_DEVICE_PREFIXES = ('test-device-', 'dev-desktop-')

    platform_logs_raw = (
        db.table("license_validation_logs")
        .select("license_key, device_id, platform")
        .eq("success", True)
        .in_("platform", list(PLATFORM_VALUES))
        .execute()
        .data
        or []
    )
    platform_keys: set[str] = set()
    for pl in platform_logs_raw:
        dev = pl.get("device_id") or ""
        if not any(dev.startswith(p) for p in TEST_DEVICE_PREFIXES):
            platform_keys.add(pl.get("license_key") or "")

    def has_platform_activation(full_key: str) -> bool:
        for candidate in _log_key_candidates(full_key):
            if candidate in platform_keys:
                return True
        return False

    licenses["platform_activated"] = licenses["license_key"].apply(has_platform_activation)
    now_ts = pd.Timestamp.now(tz="UTC")
    licenses["days_since_key"] = (now_ts - licenses["created_at"]).dt.days

    devices_raw = (
        db.table("license_devices")
        .select("license_id, device_id, platform, broker, account_id, version, is_active, first_seen_at, last_seen_at")
        .order("last_seen_at", desc=True)
        .execute()
        .data
        or []
    )
    fleet = pd.DataFrame(devices_raw)

    merged = licenses.copy()
    if not fleet.empty:
        fleet["first_seen_at"] = _safe_to_datetime(fleet["first_seen_at"])
        fleet["last_seen_at"] = _safe_to_datetime(fleet["last_seen_at"])
        fleet["device_short"] = fleet["device_id"].fillna("").astype(str).str[:16] + "..."
        fleet["key_short"] = fleet["license_id"].map(dict(zip(licenses["id"], licenses["key_short"])))
        fleet["email"] = fleet["license_id"].map(dict(zip(licenses["id"], licenses["email"])))
        fleet["first_seen_at_str"] = fleet["first_seen_at"].dt.strftime("%Y-%m-%d")
        fleet["last_seen_at_str"] = fleet["last_seen_at"].dt.strftime("%Y-%m-%d %H:%M")

        active_devices = fleet[fleet["is_active"] == True].copy()
        last_seen = (
            active_devices.groupby("license_id")["last_seen_at"]
            .max()
            .reset_index()
            .rename(columns={"license_id": "id", "last_seen_at": "last_active"})
        )
        merged = merged.merge(last_seen, on="id", how="left")
    else:
        merged["last_active"] = pd.NaT

    now = pd.Timestamp.now(tz="UTC")
    merged["days_since"] = (now - merged["last_active"]).dt.days
    merged["status"] = merged["days_since"].apply(
        lambda value: "ACTIVE"
        if pd.notna(value) and value <= 3
        else "IDLE"
        if pd.notna(value) and value <= 7
        else "AT RISK"
        if pd.notna(value)
        else "NEVER SEEN"
    )
    merged["last_active_str"] = merged["last_active"].apply(_stringify_timestamp)

    recent_success_raw = (
        db.table("license_validation_logs")
        .select("license_key, created_at")
        .eq("success", True)
        .gte("created_at", since)
        .execute()
        .data
        or []
    )
    recent_success = pd.DataFrame(recent_success_raw)
    cadence_lookup: dict[str, int] = {}
    if not recent_success.empty:
        recent_success["created_at"] = _safe_to_datetime(recent_success["created_at"])
        recent_success["date"] = recent_success["created_at"].dt.date
        cadence = (
            recent_success.groupby("license_key")["date"]
            .nunique()
            .reset_index()
            .rename(columns={"date": "days_active"})
        )
        cadence_lookup = dict(zip(cadence["license_key"], cadence["days_active"]))

    def lookup_cadence(full_key: str) -> int:
        for candidate in _log_key_candidates(full_key):
            value = cadence_lookup.get(candidate)
            if value is not None:
                return int(value)
        return 0

    licenses["days_active_30d"] = licenses["license_key"].apply(lookup_cadence)
    licenses["engagement"] = licenses["days_active_30d"].apply(
        lambda value: "POWER USER"
        if value >= 15
        else "REGULAR"
        if value >= 5
        else "LOW"
        if value >= 1
        else "DORMANT"
    )

    error_logs_raw = (
        db.table("license_validation_logs")
        .select("license_key, error_code, error_message, created_at")
        .eq("success", False)
        .gte("created_at", since)
        .execute()
        .data
        or []
    )
    errors = pd.DataFrame(error_logs_raw)
    error_counts: dict[str, int] = {}
    if not errors.empty:
        errors["created_at"] = _safe_to_datetime(errors["created_at"])
        error_counts = errors.groupby("license_key").size().to_dict()

    def lookup_errors(full_key: str) -> int:
        for candidate in _log_key_candidates(full_key):
            value = error_counts.get(candidate)
            if value is not None:
                return int(value)
        return 0

    health = licenses[[
        "id", "license_key", "key_short", "email", "plan", "max_devices",
        "is_active", "created_at_str", "expires_at_str", "activated_at",
        "platform_activated", "days_since_key",
        "days_active_30d", "engagement",
    ]].copy()
    health = health.merge(
        merged[["id", "last_active_str", "days_since", "status"]],
        on="id",
        how="left",
    )

    if not fleet.empty:
        active_count = (
            fleet[fleet["is_active"] == True]
            .groupby("key_short")
            .size()
            .to_dict()
        )
        health["devices"] = health["key_short"].map(active_count).fillna(0).astype(int)
    else:
        health["devices"] = 0

    health["errors_30d"] = health["license_key"].apply(lookup_errors)
    health["health"] = health.apply(_health_score, axis=1)

    return LicenseTrackingBundle(
        licenses=licenses,
        activations=activations,
        merged=merged,
        fleet=fleet,
        errors=errors,
        health=health,
        days=days,
        since=since,
    )


def build_summary(bundle: LicenseTrackingBundle) -> dict:
    licenses = bundle.licenses
    health = bundle.health
    errors = bundle.errors
    fleet = bundle.fleet

    if licenses.empty:
        return {
            "window_days": bundle.days,
            "since": bundle.since,
            "total_licenses": 0,
            "active_licenses": 0,
            "activated_licenses": 0,
            "never_activated": 0,
            "successful_validations_30d": 0,
            "failed_validations_30d": 0,
            "active_devices": 0,
            "health": {},
        }

    return {
        "window_days": bundle.days,
        "since": bundle.since,
        "total_licenses": int(len(licenses)),
        "active_licenses": int(licenses["is_active"].fillna(False).sum()),
        "activated_licenses": int((licenses["activated_at"] != "NEVER").sum()),
        "never_activated": int((licenses["activated_at"] == "NEVER").sum()),
        "platform_activated": int(licenses["platform_activated"].sum()),
        "desktop_only": max(
            int((licenses["activated_at"] != "NEVER").sum() - licenses["platform_activated"].sum()),
            0,
        ),
        "platform_activation_rate": round(
            licenses["platform_activated"].sum() / max(len(licenses), 1) * 100, 1
        ),
        "successful_validations_30d": int(licenses["days_active_30d"].sum()),
        "failed_validations_30d": int(len(errors)),
        "active_devices": int(len(fleet[fleet["is_active"] == True])) if not fleet.empty else 0,
        "health": {
            label: int(count)
            for label, count in health["health"].value_counts().sort_index().items()
        },
    }


def print_summary(bundle: LicenseTrackingBundle) -> None:
    summary = build_summary(bundle)
    print("=" * 72)
    print("LICENSE TRACKING SUMMARY")
    print("=" * 72)
    print(f"Window: {summary['window_days']} days since {summary['since'][:10]}")
    print(f"Total licenses:            {summary['total_licenses']}")
    print(f"Active licenses:           {summary['active_licenses']}")
    print(f"Activated licenses:        {summary['activated_licenses']}")
    print(f"Never activated:           {summary['never_activated']}")
    print(f"Platform Activated:        {summary['platform_activated']} ({summary['platform_activation_rate']}%)  ← ULTIMATE CONVERSION")
    print(f"Desktop Only (not conv.):  {summary['desktop_only']}")
    print(f"Successful active days:    {summary['successful_validations_30d']}")
    print(f"Failed validations:        {summary['failed_validations_30d']}")
    print(f"Active devices:            {summary['active_devices']}")
    print("-" * 72)
    for label in ["HEALTHY", "WARMING UP", "NOT ACTIVATED", "NEEDS_ONBOARDING_HELP", "DESKTOP_ONLY", "NEEDS SUPPORT", "CHURNING", "DORMANT"]:
        print(f"{label:24s}{summary['health'].get(label, 0)}")


def print_dashboard(bundle: LicenseTrackingBundle) -> None:
    health = bundle.health.copy()
    if health.empty:
        print("[!] No license data available")
        return

    final_cols = [
        "email", "plan", "activated_at", "platform_activated", "last_active_str",
        "days_active_30d", "devices", "errors_30d", "engagement", "health",
    ]
    print_summary(bundle)
    print()
    print("=" * 120)
    print("CUSTOMER HEALTH DASHBOARD")
    print("=" * 120)
    print(health[final_cols].sort_values(["health", "email"]).to_string(index=False))


def print_fleet(bundle: LicenseTrackingBundle) -> None:
    fleet = bundle.fleet.copy()
    if fleet.empty:
        print("[!] No device fleet data available")
        return

    active_fleet = fleet[fleet["is_active"] == True].copy()
    show_cols = [
        "key_short", "email", "device_short", "platform", "broker",
        "account_id", "version", "last_seen_at_str",
    ]
    print("=" * 120)
    print("DEVICE FLEET")
    print("=" * 120)
    print(active_fleet[show_cols].to_string(index=False))


def print_errors(bundle: LicenseTrackingBundle) -> None:
    errors = bundle.errors.copy()
    if errors.empty:
        print(f"[OK] No failed validations in the last {bundle.days} days")
        return

    error_summary = (
        errors.groupby(["license_key", "error_code"])
        .agg(count=("created_at", "size"), last_error=("created_at", "max"))
        .reset_index()
        .sort_values(["count", "last_error"], ascending=[False, False])
    )
    error_summary["last_error"] = error_summary["last_error"].apply(_stringify_timestamp)
    print("=" * 96)
    print("ERROR SIGNALS")
    print("=" * 96)
    print(error_summary.to_string(index=False))


def export_json(bundle: LicenseTrackingBundle) -> None:
    payload = {
        "summary": build_summary(bundle),
        "health": bundle.health.to_dict(orient="records"),
        "errors": bundle.errors.to_dict(orient="records"),
        "fleet": bundle.fleet.to_dict(orient="records"),
    }
    print(json.dumps(payload, default=str, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="License tracking analytics report")
    parser.add_argument(
        "--action",
        required=True,
        choices=["summary", "dashboard", "fleet", "errors", "export-json"],
    )
    parser.add_argument("--days", type=int, default=30, help="Rolling window size")
    args = parser.parse_args()

    bundle = build_license_tracking_bundle(days=args.days)

    if args.action == "summary":
        print_summary(bundle)
    elif args.action == "dashboard":
        print_dashboard(bundle)
    elif args.action == "fleet":
        print_fleet(bundle)
    elif args.action == "errors":
        print_errors(bundle)
    elif args.action == "export-json":
        export_json(bundle)


if __name__ == "__main__":
    main()