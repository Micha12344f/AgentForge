"""
Pull tutorial PDF link click stats from Short.io → update Notion link_tracking DB.

Filters link_tracking rows where Destination URL contains the PDF,
fetches click stats from Short.io, updates Notion, and prints a summary.

Usage:
    python scripts/pdf_link_stats.py
"""

import os, sys

_WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 3)))
sys.path.insert(0, _WS)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS, ".env"), override=True)

from datetime import datetime, timezone
from shared.notion_client import query_db, update_row
from shared.shortio_client import get_link_stats
from shared.supabase_client import get_supabase

PDF_KEYWORD = "How-to-hedge-prop-firms.pdf"


def get_conversion_counts() -> dict[str, int]:
    """Count real signups per utm_campaign from Supabase user_attribution."""
    sb = get_supabase(use_service_role=True)
    rows = sb.table("user_attribution").select("utm_campaign").execute().data or []
    counts: dict[str, int] = {}
    for r in rows:
        camp = r.get("utm_campaign")
        if camp:
            counts[camp] = counts.get(camp, 0) + 1
    return counts


def main():
    print("=" * 60)
    print("  Tutorial PDF Link Stats → Notion")
    print("=" * 60)

    # 1. Query all link_tracking rows
    print("\n[1] Querying Notion link_tracking DB …")
    all_rows = query_db("link_tracking", page_size=100)
    print(f"    Total tracked links: {len(all_rows)}")

    # 1b. Get real conversion counts from Supabase user_attribution
    print("\n[1b] Querying Supabase user_attribution for real conversions …")
    conversion_counts = get_conversion_counts()
    print(f"     Campaigns with signups: {conversion_counts}")

    # 2. Filter for PDF-related links (by destination URL or short URL path)
    pdf_rows = [
        r for r in all_rows
        if (
            (r.get("Destination URL") and PDF_KEYWORD.lower() in r["Destination URL"].lower())
            or (r.get("Short URL") and "/pdf" in r.get("Short URL", "").lower())
            or (r.get("Destination URL") and ".pdf" in r["Destination URL"].lower())
            or (r.get("UTM Campaign") and "pdf" in (r.get("UTM Campaign") or "").lower())
        )
        # Exclude Canva links — not real PDF destinations
        and not ("canva" in (r.get("Destination URL") or "").lower())
        and not ("canva" in (r.get("Short URL") or "").lower())
    ]
    print(f"    PDF tutorial links found: {len(pdf_rows)}")

    if not pdf_rows:
        # Fall back to all links so user can see what's tracked
        print("\n⚠️  No PDF-specific links found. Pulling stats for ALL tracked links:")
        pdf_rows = all_rows

    # 3. Pull stats from Short.io and update Notion
    print("\n[2] Pulling Short.io stats and updating Notion …\n")
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_clicks_all = 0
    total_human_all = 0
    total_conversions_all = 0

    for row in pdf_rows:
        link_id = row.get("Link ID") or row.get("Short.io ID")
        short_url = row.get("Short URL", "?")
        dest_url = row.get("Destination URL", "?")
        page_id = row.get("_id")
        campaign = row.get("UTM Campaign", "—")

        if not link_id:
            print(f"  ⚠️  {short_url} — no Link ID, skipping")
            continue

        try:
            stats = get_link_stats(link_id, period="total")
            total_clicks = stats.get("totalClicks", 0)
            human_clicks = stats.get("humanClicks", 0)

            # Real conversions from Supabase user_attribution
            real_conversions = conversion_counts.get(campaign, 0) if campaign else 0

            # Breakdown
            browsers = stats.get("browser", [])
            countries = stats.get("country", [])
            referers = stats.get("referer", [])

            total_clicks_all += total_clicks
            total_human_all += human_clicks
            total_conversions_all += real_conversions

            # Update Notion — Clicks = Short.io total, Conversions = real signups
            if page_id:
                update_row(page_id, "link_tracking", {
                    "Clicks": total_clicks,
                    "Conversions": real_conversions,
                    "Last Clicked": now_iso,
                })

            print(f"  ✅ {short_url}")
            print(f"     Campaign:     {campaign}")
            print(f"     Destination:  {dest_url}")
            print(f"     Total clicks: {total_clicks}")
            print(f"     Human clicks: {human_clicks}")
            print(f"     Conversions:  {real_conversions} (real signups)")
            if browsers:
                top_browsers = sorted(browsers, key=lambda b: b.get("score", 0), reverse=True)[:3]
                bstr = ", ".join(f"{b.get('label','?')}: {b.get('score',0)}" for b in top_browsers)
                print(f"     Browsers:     {bstr}")
            if countries:
                top_countries = sorted(countries, key=lambda c: c.get("score", 0), reverse=True)[:3]
                cstr = ", ".join(f"{c.get('label','?')}: {c.get('score',0)}" for c in top_countries)
                print(f"     Countries:    {cstr}")
            if referers:
                top_refs = sorted(referers, key=lambda r: r.get("score", 0), reverse=True)[:3]
                rstr = ", ".join(f"{r.get('label','?')}: {r.get('score',0)}" for r in top_refs)
                print(f"     Referrers:    {rstr}")
            print()

        except Exception as e:
            print(f"  ❌ {short_url} — {e}\n")

    # 4. Summary
    print("=" * 60)
    print(f"  SUMMARY — Tutorial PDF Links")
    print(f"  Links tracked:  {len(pdf_rows)}")
    print(f"  Total clicks:   {total_clicks_all}")
    print(f"  Human clicks:   {total_human_all}")
    print(f"  Conversions:    {total_conversions_all} (real signups from Supabase)")
    print(f"  Updated in Notion: {now_iso}")
    print("=" * 60)


if __name__ == "__main__":
    main()
