#!/usr/bin/env python3
"""Check whether named beta testers are present across Supabase auth and product tables."""

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
from shared.supabase_client import get_supabase, get_user_by_email

load_dotenv(WORKSPACE_ROOT / ".env")

BETA_TESTERS = [
    ("Emmanuel Adelegan", "adeleganemmanuel14@gmail.com"),
    ("ILINDA", "zyuunigenk@gmail.com"),
    ("Lavesh", "pateldheeraj98876@gmail.com"),
]


def main() -> None:
    supabase = get_supabase(use_service_role=True)

    print("=" * 65)
    print("  AUTH.USERS")
    print("=" * 65)
    auth_ids = {}
    for name, email in BETA_TESTERS:
        user = get_user_by_email(email)
        if user:
            user_id = user.get("id")
            auth_ids[email] = user_id
            created = str(user.get("created_at", ""))[:19]
            metadata = user.get("app_metadata") or {}
            print(f"  FOUND      {name:22s}  id={user_id}  created={created}")
            print(f"             app_metadata={json.dumps(metadata, default=str)}")
        else:
            print(f"  NOT FOUND  {name}")
    print()

    print("=" * 65)
    print("  PROFILES TABLE")
    print("=" * 65)
    try:
        profiles = supabase.table("profiles").select("*").execute().data
        for name, email in BETA_TESTERS:
            user_id = auth_ids.get(email)
            hits = [
                profile
                for profile in profiles
                if (user_id and profile.get("user_id") == user_id)
                or (user_id and profile.get("id") == user_id)
                or (profile.get("email", "").lower() == email.lower())
            ]
            if hits:
                print(f"  FOUND      {name}: {json.dumps(hits[0], default=str)[:200]}")
            else:
                print(f"  NOT FOUND  {name}")
    except Exception as error:
        print(f"  profiles table error: {error}")
    print()

    print("=" * 65)
    print("  CONVERSION / EVENT TABLES")
    print("=" * 65)
    for table_name in [
        "conversions",
        "events",
        "activations",
        "beta_signups",
        "license_activations",
        "utm_events",
        "page_views",
    ]:
        try:
            supabase.table(table_name).select("*").limit(1).execute()
            count_result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
            total = count_result.count or 0
            print(f"  TABLE '{table_name}' exists — {total} rows")
            for name, email in BETA_TESTERS:
                user_id = auth_ids.get(email)
                try:
                    hits = supabase.table(table_name).select("*").ilike("email", email).limit(5).execute().data
                    if hits:
                        print(f"    -> {name} FOUND: {json.dumps(hits[0], default=str)[:150]}")
                except Exception:
                    pass
                if user_id:
                    try:
                        hits = supabase.table(table_name).select("*").eq("user_id", user_id).limit(5).execute().data
                        if hits:
                            print(f"    -> {name} FOUND by uid: {json.dumps(hits[0], default=str)[:150]}")
                    except Exception:
                        pass
        except Exception as error:
            if "does not exist" in str(error) or "relation" in str(error).lower() or "42P01" in str(error):
                print(f"  TABLE '{table_name}' — does not exist")
            else:
                print(f"  TABLE '{table_name}' — error: {str(error)[:100]}")


if __name__ == "__main__":
    main()
