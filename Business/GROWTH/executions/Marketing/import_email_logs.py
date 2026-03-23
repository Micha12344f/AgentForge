#!/usr/bin/env python3
"""
Resend → email_logs  (import + enrich + reply detection)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
One script to keep email_logs in sync with Resend.

MODES
  import  (default)  Fetch emails from Resend, filter by template subjects,
                      detect replies (RE: …), create normalised rows.
  enrich             Poll existing email_logs rows against Resend for status
                      updates (safety-net for missed webhooks).

REPLY HANDLING
  Resend shows lead replies as emails with subject "RE: <template subject>".
  These are imported with:
    • Replied  = True
    • Lead Contact relation set (who replied)
    • Email Sequence / Email Campaign  NOT set
      (avoids double-counting in rollup aggregations)

ROW FORMAT
  • Subject (title)  — "-"  (template subject shown via rollup)
  • Checkboxes       — Sent ✓, Delivered ✓, Opened ✓, etc.
  • Timestamp        — when the email was sent
  • Relations        — Email Sequence, Lead Contact, Email Campaign
  • Resend ID        — for dedup
  • Template Subject — rollup from Email Sequence (auto)

USAGE
  python import_email_logs.py                 # import all
  python import_email_logs.py --limit 20      # import latest 20
  python import_email_logs.py --dry-run       # preview only
  python import_email_logs.py --enrich        # update existing rows
    python import_email_logs.py --include-replies  # opt in to reply polling
"""

import os
import sys
import re
import time
import argparse
import requests
from datetime import datetime, timezone

_ws_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, _ws_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_ws_root, ".env"))

from shared.notion_client import DATABASES, add_row, query_db, update_row

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
ENABLE_REPLY_POLL = os.getenv("ENABLE_REPLY_POLL", "0").strip().lower() in {"1", "true", "yes", "on"}

_RE_PREFIX = re.compile(r"^re:\s*", re.IGNORECASE)
_LEAD_REPLY_PREFIX = re.compile(
    r"^\[lead\s+reply\]\s+\S+\s+re:\s*", re.IGNORECASE
)  # [Lead Reply] sender@email re: <original subject>

# ── Checkpoint progression ──────────────────────────────
STATUS_PROGRESSION = {
    "sent":              ["Sent"],
    "delivered":         ["Sent", "Delivered"],
    "delivery_delayed":  ["Sent", "Delivered"],
    "opened":            ["Sent", "Delivered", "Opened"],
    "clicked":           ["Sent", "Delivered", "Opened", "Clicked"],
    "bounced":           ["Sent", "Bounced"],
    "complained":        ["Sent", "Unsubscribed"],
    "unsubscribed":      ["Sent", "Unsubscribed"],
}

ALL_CHECKBOXES = ["Sent", "Delivered", "Opened", "Clicked", "Bounced", "Unsubscribed", "Replied"]

STATUS_RANK = {
    "sent": 1, "delivered": 2, "delivery_delayed": 2,
    "opened": 3, "clicked": 4, "bounced": 5,
    "complained": 6, "unsubscribed": 7,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _resend_headers():
    return {"Authorization": f"Bearer {RESEND_API_KEY}"}


def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. Load template subject whitelist
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_template_subjects() -> dict[str, dict]:
    """Return {subject_lower: {page_id, template_name, subject}}."""
    print("\n[1] Loading Email Template subject lines …")
    h = _notion_headers()
    db_id = DATABASES.get("email_sequences")
    if not db_id:
        print("  ✗ email_sequences DB not configured"); return {}

    templates: dict[str, dict] = {}
    try:
        r = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=h, json={"page_size": 100}, timeout=15,
        )
        r.raise_for_status()
        for row in r.json().get("results", []):
            p = row["properties"]
            title_parts = p.get("Template", {}).get("title", [])
            tpl_name = "".join(t.get("plain_text", "") for t in title_parts).strip()
            subj_parts = p.get("Subject Line", {}).get("rich_text", [])
            subj = "".join(t.get("plain_text", "") for t in subj_parts).strip()
            if not subj:
                continue
            templates[subj.lower()] = {
                "page_id": row["id"],
                "template_name": tpl_name,
                "subject": subj,
            }
            print(f"  ✓ {tpl_name:30s} → \"{subj[:60]}\"")
    except Exception as e:
        print(f"  ✗ Failed to load templates: {e}")
        return {}

    print(f"  {len(templates)} template subjects loaded")
    return templates


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. Fetch emails from Resend
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_and_classify(
    templates: dict[str, dict],
    limit: int = 0,
    include_replies: bool = False,
) -> tuple[list[tuple[dict, str, dict]], int, dict[str, int]]:
    """Paginate through Resend, classify each email on the fly.

    Returns (matches, total_scanned, junk_subjects).
    Only template/reply matches are kept in memory — junk is discarded immediately.

    Resend pagination: ?limit=100&after=<last_email_id>  (NOT cursor=)
    """
    print(f"\n[2] Scanning Resend emails{f' (limit {limit})' if limit else ' (all)'} …")
    h = _resend_headers()
    matches: list[tuple[dict, str, dict]] = []  # (summary, kind, tpl_info)
    junk_subjects: dict[str, int] = {}
    total = 0
    after: str | None = None
    page = 0

    while True:
        page += 1
        params: dict = {"limit": 100}
        if after:
            params["after"] = after
        try:
            r = requests.get("https://api.resend.com/emails", headers=h, params=params, timeout=30)
            if r.status_code == 429:
                print(f"  ⚠ Rate limited on page {page}, waiting 5s …")
                time.sleep(5)
                continue
            if r.status_code != 200:
                print(f"  ✗ Resend list failed on page {page}: {r.status_code}")
                break
            data = r.json()
            batch = data.get("data", [])
            if not batch:
                break

            # Classify each email in this batch
            for email in batch:
                total += 1
                subj = email.get("subject", "")
                kind, tpl_info = classify_email(subj, templates, include_replies=include_replies)
                if kind == "junk":
                    key = subj[:80] or "(no subject)"
                    junk_subjects[key] = junk_subjects.get(key, 0) + 1
                else:
                    matches.append((email, kind, tpl_info))

            if page % 5 == 0 or page <= 3:
                print(f"  … page {page}, scanned {total}, {len(matches)} matches so far")

            # Stop if we have enough matches
            if limit > 0 and len(matches) >= limit:
                matches = matches[:limit]
                break

            # Stop if no more pages
            if not data.get("has_more"):
                break

            # "after" = last email ID in this batch
            after = batch[-1].get("id")
            time.sleep(0.25)

        except Exception as e:
            print(f"  ✗ Resend error on page {page}: {e}")
            break

    n_template = sum(1 for _, k, _ in matches if k == "template")
    n_reply = sum(1 for _, k, _ in matches if k == "reply")
    print(f"  Scanned {total} across {page} page(s)")
    print(f"  → {n_template} template  |  {n_reply} reply  |  {total - len(matches)} junk")
    return matches, total, junk_subjects


def fetch_email_details(summaries: list[dict]) -> list[dict]:
    """Fetch full details for each email (last_event etc.).

    Handles Resend rate limits (429) with exponential backoff.
    """
    print(f"\n[3] Fetching details for {len(summaries)} emails …")
    h = _resend_headers()
    detailed = []
    for i, s in enumerate(summaries):
        eid = s.get("id", "")
        for attempt in range(3):
            try:
                r = requests.get(f"https://api.resend.com/emails/{eid}", headers=h, timeout=10)
                if r.status_code == 200:
                    detailed.append(r.json())
                    break
                elif r.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    print(f"  [{i+1}] Rate limited, waiting {wait}s …")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [{i+1}] {eid[:12]}… HTTP {r.status_code}")
                    break
            except Exception as e:
                print(f"  [{i+1}] {eid[:12]}… Error: {e}")
                break
        if (i + 1) % 25 == 0:
            print(f"  … {i+1}/{len(summaries)}")
        time.sleep(0.35)
    print(f"  Details for {len(detailed)}/{len(summaries)}")
    return detailed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. Lead + dedup caches
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_lead_cache() -> dict[str, str]:
    """email_lower → Notion page ID from leads_crm."""
    print("\n[4] Building lead cache …")
    cache: dict[str, str] = {}
    h = _notion_headers()
    db_id = DATABASES.get("leads_crm")
    if not db_id:
        return cache
    cursor = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                headers=h, json=body, timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            for row in data.get("results", []):
                e = row.get("properties", {}).get("Email", {}).get("email", "")
                if e:
                    cache[e.lower()] = row["id"]
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
            time.sleep(0.35)
        except Exception as e:
            print(f"  ⚠ leads fetch error: {e}")
            break
    print(f"  {len(cache)} leads cached")
    return cache


def load_existing_resend_ids() -> dict[str, str]:
    """Return {resend_id: page_id} already in email_logs."""
    print("  Loading existing Resend IDs for dedup …")
    existing: dict[str, str] = {}
    h = _notion_headers()
    db_id = DATABASES.get("email_logs")
    if not db_id:
        return existing
    cursor = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                headers=h, json=body, timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            for row in data.get("results", []):
                rid_rt = row.get("properties", {}).get("Resend ID", {}).get("rich_text", [])
                rid = "".join(t.get("plain_text", "") for t in rid_rt).strip()
                if rid:
                    existing[rid] = row["id"]
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
            time.sleep(0.35)
        except Exception:
            break
    print(f"  {len(existing)} existing rows")
    return existing


def get_active_campaign_id() -> str:
    """Return the page ID of the Active campaign, or ''."""
    try:
        rows = query_db("campaigns", filter={
            "property": "Status", "select": {"equals": "Active"},
        }, page_size=1)
        if rows:
            print(f"  Active campaign: {rows[0].get('Name', '?')}")
            return rows[0]["_id"]
    except Exception:
        pass
    return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. Classify email: template / reply / junk
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_email(subject: str, templates: dict[str, dict], include_replies: bool = False) -> tuple[str, dict]:
    """Return (kind, template_info).

    kind is one of:
      "template"  — subject matches a known template
      "reply"     — RE: or [Lead Reply] prefix, remainder matches a template
      "junk"      — no match
    """
    subj_lower = (subject or "").lower().strip()

    # Exact template match
    if subj_lower in templates:
        return "template", templates[subj_lower]

    if not include_replies:
        return "junk", {}

    # Reply detection — two formats:
    #   "RE: <template subject>"
    #   "[Lead Reply] sender@email re: <template subject>"
    for pattern in (_LEAD_REPLY_PREFIX, _RE_PREFIX):
        stripped = pattern.sub("", subj_lower).strip()
        if stripped != subj_lower and stripped in templates:
            return "reply", templates[stripped]

    return "junk", {}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  5. Create / update rows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_log_row(
    email_data: dict,
    kind: str,
    template_info: dict,
    lead_cache: dict[str, str],
    campaign_id: str,
    dry_run: bool = False,
) -> bool:
    """Create ONE normalised row in email_logs.

    kind="template" → full relations (sequence + campaign + lead)
    kind="reply"    → lead only, Replied=True, no sequence/campaign
    """
    resend_id = email_data.get("id", "")
    to_list = email_data.get("to", [])
    from_addr = email_data.get("from", "")
    last_event = email_data.get("last_event", "sent")
    created_at = email_data.get("created_at", "")
    sent_ts = (created_at[:19] + ".000Z") if created_at else datetime.now(timezone.utc).isoformat()[:19] + ".000Z"

    # For regular sends: recipient is in "to"
    # For replies: the lead sent the email, so lead is in "from"
    if kind == "reply":
        # Extract lead email — could be in "from" field or embedded in subject
        # Subject format: "[Lead Reply] sender@email re: ..." 
        subj = email_data.get("subject", "")
        m_subj = re.search(r'\[Lead Reply\]\s+([\w.+-]+@[\w.-]+)', subj, re.IGNORECASE)
        if m_subj:
            lead_email = m_subj.group(1).lower()
        else:
            # Standard reply: lead is "from" field
            m = re.search(r'[\w.+-]+@[\w.-]+', from_addr or "")
            lead_email = m.group(0).lower() if m else ""
        active_states = ["Sent", "Delivered", "Opened", "Replied"]
    else:
        recipient = to_list[0] if isinstance(to_list, list) and to_list else str(to_list)
        lead_email = recipient.lower().strip()
        active_states = STATUS_PROGRESSION.get(last_event, ["Sent"])

    # Build properties — title is "-" (subject shown via Template Subject rollup)
    props: dict = {
        "Subject": "-",
        "Email": lead_email if lead_email else (to_list[0] if isinstance(to_list, list) and to_list else ""),
        "Resend ID": resend_id,
        "Timestamp": sent_ts,
    }

    # Checkboxes
    for cb in ALL_CHECKBOXES:
        props[cb] = cb in active_states

    if kind == "reply":
        props["Replied"] = True
        # NO campaign or sequence relations for replies
        # (avoids double-counting in rollup aggregations)
    else:
        # Template match → full relations
        if template_info.get("page_id"):
            props["Email Sequence"] = template_info["page_id"]
        if campaign_id:
            props["Email Campaign"] = campaign_id

    # Lead Contact (set for both templates and replies)
    lead_id = lead_cache.get(lead_email, "")
    if lead_id:
        props["Lead Contact"] = lead_id

    if dry_run:
        return True

    try:
        add_row("email_logs", props)
        return True
    except Exception as e:
        print(f"    ✗ create failed: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  6. Enrich existing rows (catch-up)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enrich_existing_rows(dry_run: bool = False):
    """Poll Resend for status updates on non-terminal email_logs rows.

    Non-terminal = not Bounced/Unsubscribed AND has a Resend ID.
    Compares last_event from Resend against current checkboxes and
    upgrades checkboxes if Resend shows a higher status.
    """
    print("\n[ENRICH] Checking existing email_logs rows for status updates …")
    h_notion = _notion_headers()
    h_resend = _resend_headers()
    db_id = DATABASES.get("email_logs")

    # Query non-terminal rows with a Resend ID
    rows_to_check = []
    cursor = None
    while True:
        payload: dict = {
            "filter": {
                "and": [
                    {"property": "Resend ID", "rich_text": {"is_not_empty": True}},
                    {"property": "Bounced", "checkbox": {"equals": False}},
                    {"property": "Unsubscribed", "checkbox": {"equals": False}},
                ],
            },
            "page_size": 100,
        }
        if cursor:
            payload["start_cursor"] = cursor
        try:
            r = requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                headers=h_notion, json=payload, timeout=15,
            )
            data = r.json()
            for row in data.get("results", []):
                p = row["properties"]
                rid_rt = p.get("Resend ID", {}).get("rich_text", [])
                rid = "".join(t.get("plain_text", "") for t in rid_rt).strip()
                if not rid:
                    continue
                # Determine current highest checkbox rank
                current_rank = 0
                if p.get("Clicked", {}).get("checkbox"):
                    current_rank = 4
                elif p.get("Opened", {}).get("checkbox"):
                    current_rank = 3
                elif p.get("Delivered", {}).get("checkbox"):
                    current_rank = 2
                elif p.get("Sent", {}).get("checkbox"):
                    current_rank = 1
                rows_to_check.append({
                    "page_id": row["id"],
                    "resend_id": rid,
                    "current_rank": current_rank,
                })
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
            time.sleep(0.35)
        except Exception as e:
            print(f"  ⚠ query error: {e}")
            break

    print(f"  {len(rows_to_check)} non-terminal rows to check")
    if not rows_to_check:
        print("  Nothing to enrich.")
        return

    # Fetch current status from Resend
    enriched = 0
    skipped = 0
    errors = 0
    for i, row in enumerate(rows_to_check):
        try:
            r = requests.get(
                f"https://api.resend.com/emails/{row['resend_id']}",
                headers=h_resend, timeout=10,
            )
            if r.status_code != 200:
                skipped += 1
                continue
            email_data = r.json()
        except Exception:
            skipped += 1
            continue

        last_event = email_data.get("last_event", "sent")
        new_rank = STATUS_RANK.get(last_event, 1)

        if new_rank <= row["current_rank"]:
            skipped += 1
        else:
            # Build checkbox update
            active_states = STATUS_PROGRESSION.get(last_event, ["Sent"])
            update_props: dict = {}
            for cb in ALL_CHECKBOXES:
                if cb in active_states:
                    update_props[cb] = True

            if dry_run:
                print(f"  [DRY] {row['resend_id'][:12]}… → {last_event} ({', '.join(active_states)})")
                enriched += 1
            else:
                try:
                    update_row(row["page_id"], "email_logs", update_props)
                    enriched += 1
                except Exception as e:
                    print(f"  ✗ update error: {e}")
                    errors += 1

        if (i + 1) % 20 == 0:
            print(f"  … {i+1}/{len(rows_to_check)}")
        time.sleep(0.5)

    print(f"\n  Enriched: {enriched}  Skipped: {skipped}  Errors: {errors}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    parser = argparse.ArgumentParser(description="Resend → email_logs (import + enrich + reply detection)")
    parser.add_argument("--limit", type=int, default=0, help="Max emails to fetch from Resend (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Notion")
    parser.add_argument("--enrich", action="store_true", help="Enrich mode: update existing rows only")
    parser.add_argument(
        "--include-replies",
        action="store_true",
        help="Opt in to reply polling for this run",
    )
    args = parser.parse_args()
    include_replies = ENABLE_REPLY_POLL or args.include_replies

    print("=" * 65)
    print("  RESEND → EMAIL_LOGS")
    if args.enrich:
        print("  Mode: ENRICH (update existing rows)")
    else:
        print("  Mode: IMPORT (fetch + create new rows)")
        if include_replies:
            print("  Reply poll: ENABLED")
        else:
            print("  Reply poll: SUSPENDED")
    if args.dry_run:
        print("  *** DRY RUN ***")
    if args.limit:
        print(f"  Limit: {args.limit}")
    print("=" * 65)

    if not RESEND_API_KEY:
        print("\n✗ RESEND_API_KEY not set"); return
    if not NOTION_API_KEY:
        print("\n✗ NOTION_API_KEY not set"); return

    # ── ENRICH mode ──
    if args.enrich:
        enrich_existing_rows(dry_run=args.dry_run)
        return

    # ── IMPORT mode ──
    # 1. Load template subjects
    templates = load_template_subjects()
    if not templates:
        print("\n✗ No templates found. Nothing to import.")
        return

    # 2. Fetch + classify from Resend (streaming — only matches kept in memory)
    to_fetch, total_scanned, skipped_junk = fetch_and_classify(
        templates,
        limit=args.limit,
        include_replies=include_replies,
    )
    if not to_fetch:
        print("\n  No matching emails. Nothing to import.")
        return

    n_template = sum(1 for _, k, _ in to_fetch if k == "template")
    n_reply = sum(1 for _, k, _ in to_fetch if k == "reply")
    n_junk = total_scanned - len(to_fetch)

    if skipped_junk:
        print("\n  Top junk subjects (ignored):")
        for subj, cnt in sorted(skipped_junk.items(), key=lambda x: -x[1])[:15]:
            print(f"    × {cnt:4d}× \"{subj[:70]}\"")

    # 3. Fetch details for matches only
    summaries_to_detail = [s for s, _, _ in to_fetch]
    detailed_list = fetch_email_details(summaries_to_detail)

    # Re-map details by ID
    detail_by_id = {d["id"]: d for d in detailed_list if "id" in d}

    # 4. Build caches
    lead_cache = build_lead_cache()
    existing_ids = load_existing_resend_ids()
    campaign_id = get_active_campaign_id()

    # 5. Create rows
    print(f"\n[5] Creating rows{'  [DRY RUN]' if args.dry_run else ''} …")
    created = 0
    skipped_dup = 0
    created_replies = 0
    failed = 0

    for summary, kind, tpl_info in to_fetch:
        eid = summary.get("id", "")
        email_data = detail_by_id.get(eid)
        if not email_data:
            continue

        resend_id = email_data.get("id", "")
        if resend_id in existing_ids:
            skipped_dup += 1
            continue

        ok = create_log_row(email_data, kind, tpl_info, lead_cache, campaign_id, dry_run=args.dry_run)
        if ok:
            created += 1
            if kind == "reply":
                created_replies += 1
            last_event = email_data.get("last_event", "?")
            to_list = email_data.get("to", ["?"])
            recipient = to_list[0] if isinstance(to_list, list) and to_list else "?"
            if created <= 5 or created % 25 == 0:
                tag = "↩ REPLY" if kind == "reply" else "  send "
                print(f"  [{created:3d}] {tag}  {recipient:35s}  {last_event:12s}")
        else:
            failed += 1
        time.sleep(0.5)

    print(f"\n{'='*65}")
    print(f"  DONE{'  [DRY RUN]' if args.dry_run else ''}")
    print(f"  Created:  {created}  ({created_replies} replies)")
    print(f"  Deduped:  {skipped_dup}")
    print(f"  Failed:   {failed}")
    print(f"  Junk:     {n_junk}")
    print(f"{'='*65}")
    if not args.dry_run and created > 0:
        print("  ✓ Template Subject rollup auto-populates via Email Sequence relation")
        if include_replies:
            print("  ✓ Replies logged with Lead Contact only (no double-counting)")


if __name__ == "__main__":
    main()
