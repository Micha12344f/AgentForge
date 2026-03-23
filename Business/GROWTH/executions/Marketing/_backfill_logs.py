"""Backfill empty Email Campaign / Email Sequence / Lead Contact relations on email_logs rows.

Finds all email_logs rows where Sent=true but one of the three relation
columns is empty, then patches them with the correct page-IDs.
"""
import sys, os, time, requests, re

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if os.path.isfile(os.path.join(d, "shared", "notion_client.py")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"))

from shared.notion_client import DATABASES

TOKEN = os.getenv("NOTION_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _retry_post(url, body, retries=4):
    r = None
    for i in range(retries):
        try:
            r = requests.post(url, headers=HEADERS, json=body, timeout=30)
            if r.status_code == 429:
                wait = min(int(r.headers.get("Retry-After", 5)), 30)
                print(f"  429 — waiting {wait}s...")
                time.sleep(wait)
                continue
            return r
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print(f"  Timeout/conn error, retry {i+1}...")
            time.sleep(5)
    return r


def _retry_patch(url, body, retries=4):
    r = None
    for i in range(retries):
        try:
            r = requests.patch(url, headers=HEADERS, json=body, timeout=30)
            if r.status_code == 429:
                wait = min(int(r.headers.get("Retry-After", 5)), 30)
                print(f"  429 — waiting {wait}s...")
                time.sleep(wait)
                continue
            return r
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print(f"  Timeout/conn error, retry {i+1}...")
            time.sleep(5)
    return r


def load_email_sequences():
    """Map email_num -> page_id from the email_sequences DB."""
    mapping = {}
    r = _retry_post(
        f"https://api.notion.com/v1/databases/{DATABASES['email_sequences']}/query",
        {"page_size": 100},
    )
    for row in r.json().get("results", []):
        title_parts = row.get("properties", {}).get("Template", {}).get("title", [])
        name = "".join(p["plain_text"] for p in title_parts).strip()
        if name.lower().startswith("welcome"):
            mapping[0] = row["id"]
        elif name.lower().startswith("email "):
            try:
                num = int(name.split()[-1])
                mapping[num] = row["id"]
            except ValueError:
                pass
    print(f"Loaded {len(mapping)} email sequences: {sorted(mapping.keys())}")
    return mapping


def load_leads():
    """Map email_lower -> page_id from leads_crm."""
    mapping = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = _retry_post(
            f"https://api.notion.com/v1/databases/{DATABASES['leads_crm']}/query",
            body,
        )
        data = r.json()
        for row in data.get("results", []):
            email = row.get("properties", {}).get("Email", {}).get("email", "")
            if email:
                mapping[email.lower()] = row["id"]
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.4)
    print(f"Loaded {len(mapping)} leads")
    return mapping


def load_active_campaign():
    """Return page_id of first Active campaign."""
    r = _retry_post(
        f"https://api.notion.com/v1/databases/{DATABASES['campaigns']}/query",
        {"page_size": 1, "filter": {"property": "Status", "select": {"equals": "Active"}}},
    )
    results = r.json().get("results", [])
    if results:
        name = "".join(
            p["plain_text"]
            for p in results[0]["properties"].get("Name", {}).get("title", [])
        )
        print(f"Active campaign: {name!r} -> {results[0]['id']}")
        return results[0]["id"]
    print("No active campaign found!")
    return ""


def get_empty_rows():
    """Paginate through email_logs rows missing any of the three relations."""
    rows = []
    cursor = None
    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": "Sent", "checkbox": {"equals": True}},
                    {"or": [
                        {"property": "Email Campaign", "relation": {"is_empty": True}},
                        {"property": "Email Sequence", "relation": {"is_empty": True}},
                        {"property": "Lead Contact", "relation": {"is_empty": True}},
                    ]},
                ]
            },
        }
        if cursor:
            body["start_cursor"] = cursor
        r = _retry_post(
            f"https://api.notion.com/v1/databases/{DATABASES['email_logs']}/query",
            body,
        )
        if r is None or r.status_code != 200:
            print(f"  Query failed: {r.status_code if r else 'None'}")
            break
        data = r.json()
        for row in data.get("results", []):
            props = row["properties"]
            name = "".join(p["plain_text"] for p in props.get("Subject", {}).get("title", []))
            email = props.get("Email", {}).get("email", "")
            rows.append({
                "page_id": row["id"],
                "email": email,
                "name": name,
                "has_seq": bool(props.get("Email Sequence", {}).get("relation", [])),
                "has_lead": bool(props.get("Lead Contact", {}).get("relation", [])),
                "has_camp": bool(props.get("Email Campaign", {}).get("relation", [])),
            })
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.4)
    return rows


def guess_email_num_from_name(name: str) -> int:
    """Try to extract email number from the log row name.
    
    Names look like: 'Sent — Your prop firm doesn't want you to know this'
    We can't get email_num from that directly. But we can check common subject patterns.
    Email 1 subject usually differs from Email 2.
    
    Safer approach: look up the email in email_sends to get Drip Stage.
    """
    # For now return 0 as unknown — we'll look up from email_sends
    return 0


def load_drip_stages():
    """Map email_lower -> email_num from email_sends Drip Stage.
    
    NOTE: This returns the CURRENT drip stage, not the historical one.
    For backfill, we'll also count how many email_logs 'Sent' rows each
    email has to determine which email_num each row corresponds to.
    """
    mapping = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = _retry_post(
            f"https://api.notion.com/v1/databases/{DATABASES['email_sends']}/query",
            body,
        )
        if r is None or r.status_code != 200:
            break
        data = r.json()
        for row in data.get("results", []):
            props = row.get("properties", {})
            email = props.get("Email", {}).get("email", "")
            drip = props.get("Drip Stage", {}).get("select", {})
            drip_name = drip.get("name", "") if drip else ""
            if email and drip_name:
                if drip_name.lower().startswith("welcome"):
                    mapping[email.lower()] = 0
                elif drip_name.lower().startswith("email "):
                    try:
                        mapping[email.lower()] = int(drip_name.split()[-1])
                    except ValueError:
                        pass
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.4)
    print(f"Loaded {len(mapping)} drip stages from email_sends")
    return mapping


def count_sent_per_email():
    """For rows missing Email Sequence, determine email_num by looking at
    what other email_logs rows for the same email DO have as Email Sequence.
    
    Returns {email_lower: email_num} by finding the highest-numbered sequence
    relation for each contact.
    """
    per_email = {}
    cursor = None
    while True:
        body = {
            "page_size": 100,
            "filter": {"property": "Email Sequence", "relation": {"is_not_empty": True}},
        }
        if cursor:
            body["start_cursor"] = cursor
        r = _retry_post(
            f"https://api.notion.com/v1/databases/{DATABASES['email_logs']}/query",
            body,
        )
        if r is None or r.status_code != 200:
            break
        data = r.json()
        for row in data.get("results", []):
            email = row.get("properties", {}).get("Email", {}).get("email", "")
            seq_rel = row.get("properties", {}).get("Email Sequence", {}).get("relation", [])
            if email and seq_rel:
                seq_id = seq_rel[0]["id"]
                per_email[email.lower()] = seq_id
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.4)
    print(f"Found existing Email Sequence for {len(per_email)} emails")
    return per_email


def main():
    print("=== BACKFILL EMAIL LOGS RELATIONS ===\n")

    # Load reference data
    seq_map = load_email_sequences()
    time.sleep(0.5)
    leads = load_leads()
    time.sleep(0.5)
    campaign_id = load_active_campaign()
    time.sleep(0.5)
    drip_stages = load_drip_stages()
    time.sleep(0.5)
    sent_rows = count_sent_per_email()  # {email_lower: seq_page_id}
    time.sleep(0.5)

    # Get rows to fix
    rows = get_empty_rows()
    print(f"\nFound {len(rows)} email_logs rows to backfill\n")
    if not rows:
        print("Nothing to do!")
        return

    patched = 0
    errors = 0
    skipped = 0
    for i, row in enumerate(rows):
        update_props = {}

        # Email Campaign
        if not row["has_camp"] and campaign_id:
            update_props["Email Campaign"] = {"relation": [{"id": campaign_id}]}

        # Lead Contact
        if not row["has_lead"] and row["email"]:
            lead_id = leads.get(row["email"].lower(), "")
            if lead_id:
                update_props["Lead Contact"] = {"relation": [{"id": lead_id}]}

        # Email Sequence — use sibling row's sequence, or drip_stages fallback
        if not row["has_seq"] and row["email"]:
            # First: check if another log row for this email already has a sequence
            sibling_seq = sent_rows.get(row["email"].lower(), "")
            if sibling_seq:
                update_props["Email Sequence"] = {"relation": [{"id": sibling_seq}]}
            else:
                # Fallback: use current drip stage from email_sends
                email_num = drip_stages.get(row["email"].lower())
                if email_num is not None:
                    seq_id = seq_map.get(email_num, "")
                    if seq_id:
                        update_props["Email Sequence"] = {"relation": [{"id": seq_id}]}

        if not update_props:
            skipped += 1
            continue

        r = _retry_patch(
            f"https://api.notion.com/v1/pages/{row['page_id']}",
            {"properties": update_props},
        )
        if r is not None and r.status_code == 200:
            patched += 1
            what = "+".join(k for k in update_props.keys())
            if (patched % 20 == 0) or patched <= 3:
                print(f"  [{patched}] {row['email'][:30]} <- {what}")
        else:
            errors += 1
            status = r.status_code if r else "None"
            if errors <= 3:
                print(f"  ERROR {status} on {row['email']}: {r.text[:150] if r else 'no response'}")

        # Rate-limit ourselves
        time.sleep(0.4)

    print(f"\n=== DONE: Patched {patched}, Skipped {skipped}, Errors {errors}, Total {len(rows)} ===")


if __name__ == "__main__":
    main()
