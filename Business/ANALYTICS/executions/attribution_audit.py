#!/usr/bin/env python3
"""Attribution audit — diagnose why conversions show as direct traffic."""

import sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
from shared.supabase_client import get_supabase

load_dotenv(WORKSPACE_ROOT / ".env")

sb = get_supabase(use_service_role=True)


def main() -> None:
    total = sb.table("page_views").select("*", count="exact").execute()
    utm_rows = (
        sb.table("page_views")
        .select("utm_source,utm_medium,utm_campaign,referrer_domain,path,created_at")
        .not_.is_("utm_source", "null")
        .order("created_at", desc=True)
        .execute()
    )

    print("\n=== PAGE VIEWS ===")
    print(f"Total rows: {total.count}")
    print(f"Rows WITH utm_source: {len(utm_rows.data)}")
    print(f"Rows WITHOUT utm_source: {total.count - len(utm_rows.data)}")

    sources = Counter(row["utm_source"] for row in utm_rows.data)
    mediums = Counter(row["utm_medium"] for row in utm_rows.data)
    print(f"\nUTM Sources in page_views: {dict(sources)}")
    print(f"UTM Mediums in page_views: {dict(mediums)}")

    print("\nRecent UTM page_views:")
    for row in utm_rows.data[:15]:
        print(
            f"  {row['created_at'][:16]}  src={row['utm_source']}  "
            f"med={row['utm_medium']}  path={row['path']}  ref={row['referrer_domain']}"
        )

    ua = sb.table("user_attribution").select("*").order("signed_up_at").execute()
    print(f"\n=== USER ATTRIBUTION ({len(ua.data)} rows) ===")
    ua_sources = Counter(row["utm_source"] or "NULL" for row in ua.data)
    ua_mediums = Counter(row["utm_medium"] or "NULL" for row in ua.data)
    print(f"UTM Sources: {dict(ua_sources)}")
    print(f"UTM Mediums: {dict(ua_mediums)}")
    print(f"Landing URLs: {Counter(row['landing_url'] or 'NULL' for row in ua.data)}")
    print(f"Signup methods: {Counter(row['signup_method'] or 'NULL' for row in ua.data)}")

    print("\n=== SESSION LINKAGE CHECK ===")
    print("(Checking if page_views with UTM params exist near signup times)")
    for row in ua.data:
        signed_up = row.get("signed_up_at")
        if not signed_up:
            continue

        if signed_up.endswith("+00:00"):
            signed_up_dt = datetime.fromisoformat(signed_up)
        else:
            signed_up_dt = datetime.fromisoformat(signed_up).replace(tzinfo=timezone.utc)

        window_start = (signed_up_dt - timedelta(hours=2)).isoformat()
        window_end = signed_up_dt.isoformat()
        pv_near = (
            sb.table("page_views")
            .select("utm_source,utm_medium,path,created_at")
            .gte("created_at", window_start)
            .lte("created_at", window_end)
            .not_.is_("utm_source", "null")
            .execute()
        )

        user_short = row["user_id"][:8]
        if pv_near.data:
            print(
                f"  user={user_short} signed_up={signed_up[:16]} -> "
                f"{len(pv_near.data)} UTM page_views found nearby"
            )
            for page_view in pv_near.data:
                print(
                    f"    [{page_view['created_at'][:16]}] "
                    f"src={page_view['utm_source']} path={page_view['path']}"
                )
        else:
            print(
                f"  user={user_short} signed_up={signed_up[:16]} -> "
                f"NO UTM page_views in 2hr window [src={row['utm_source']}]"
            )

    print("\n=== DIAGNOSIS COMPLETE ===")


if __name__ == "__main__":
    main()
