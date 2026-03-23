#!/usr/bin/env python3
"""Check same-day beta waitlist activity and recent page views."""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
from shared.notion_client import query_db
from shared.supabase_client import get_supabase

load_dotenv(WORKSPACE_ROOT / ".env")

TARGET_DATE = "2026-03-22"


def main() -> None:
    rows = query_db("beta_waitlist")
    today_rows = [
        row
        for row in rows
        if row.get("created_time", "").startswith(TARGET_DATE)
        or row.get("last_edited_time", "").startswith(TARGET_DATE)
    ]

    print(f"Total beta waitlist entries: {len(rows)}")
    print(f"Entries touched today ({TARGET_DATE}): {len(today_rows)}")
    if today_rows:
        for row in today_rows:
            print(
                f"  created={row.get('created_time', '?')[:19]}  "
                f"edited={row.get('last_edited_time', '?')[:19]}"
            )
            print(f"  props keys: {list(row.get('properties', {}).keys())}")
    else:
        print("\nLatest 3 entries:")
        for row in sorted(rows, key=lambda item: item.get("created_time", ""), reverse=True)[:3]:
            print(f"  {row.get('created_time', '?')[:19]}")

    supabase = get_supabase(use_service_role=True)
    page_views = (
        supabase.table("page_views")
        .select("utm_source,utm_medium,path,created_at")
        .gte("created_at", TARGET_DATE)
        .order("created_at", desc=True)
        .execute()
    )
    print(f"\nPage views since {TARGET_DATE}: {len(page_views.data)}")
    for row in page_views.data[:15]:
        source = row.get("utm_source") or "(none)"
        medium = row.get("utm_medium") or "(none)"
        print(f"  {row['created_at'][:19]}  src={source}  med={medium}  path={row.get('path', '?')}")


if __name__ == "__main__":
    main()
