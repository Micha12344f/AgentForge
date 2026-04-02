#!/usr/bin/env python3
"""
test_license_tracking_e2e.py - End-to-end validation for license tracking.

Confirms that the license tracking report can load the live Supabase schema,
build the expected output tables, and expose the support-facing health fields.
"""

import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from license_tracking_report import build_license_tracking_bundle, build_summary


def assert_columns(frame, required: list[str], label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise AssertionError(f"{label} missing columns: {missing}")


def main() -> None:
    bundle = build_license_tracking_bundle(days=30)
    summary = build_summary(bundle)

    if bundle.licenses.empty:
        print("[WARN] No licenses found. Schema access succeeded but live data is empty.")
        print(summary)
        return

    assert_columns(
        bundle.licenses,
        ["id", "license_key", "email", "plan", "max_devices", "is_active", "key_short", "activated_at"],
        "licenses",
    )
    assert_columns(
        bundle.health,
        [
            "email", "plan", "activated_at", "last_active_str", "days_active_30d",
            "devices", "errors_30d", "engagement", "health",
        ],
        "health",
    )

    if not bundle.fleet.empty:
        assert_columns(
            bundle.fleet,
            ["license_id", "device_id", "platform", "is_active", "key_short", "email"],
            "fleet",
        )

    if not bundle.errors.empty:
        assert_columns(
            bundle.errors,
            ["license_key", "error_code", "created_at"],
            "errors",
        )

    assert summary["total_licenses"] == len(bundle.licenses)
    assert summary["active_licenses"] <= summary["total_licenses"]
    assert set(bundle.health["health"].unique()).issubset(
        {"HEALTHY", "WARMING UP", "NOT ACTIVATED", "NEEDS_ONBOARDING_HELP",
         "DESKTOP_ONLY", "NEEDS SUPPORT", "CHURNING", "DORMANT"}
    )

    print("License tracking E2E passed")
    print(summary)


if __name__ == "__main__":
    main()