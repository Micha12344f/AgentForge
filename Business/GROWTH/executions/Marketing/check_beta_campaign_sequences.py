#!/usr/bin/env python3
"""Inspect the Beta Activation campaign and its linked email sequences in Notion."""

import json
import os
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
import shared.notion_client as nc

load_dotenv(WORKSPACE_ROOT / ".env")

BETA_CAMPAIGN_ID = "329652ea-6c6d-8192-8343-cc91260c359a"


def main() -> None:
    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": nc._NOTION_VERSION,
        "Content-Type": "application/json",
    }

    response = nc.notion_request(
        "get",
        f"{nc._API_BASE}/pages/{BETA_CAMPAIGN_ID}",
        headers=headers,
        timeout=20,
    )
    page = response.json()
    props = page.get("properties", {})
    print("=== Beta Activation Campaign Properties ===")
    for key, value in props.items():
        value_type = value.get("type")
        if value_type == "relation":
            ids = [item.get("id") for item in value.get("relation", [])]
            if ids:
                print(f"  {key}: {ids}")
        elif value_type == "title":
            text = "".join(item.get("plain_text", "") for item in value.get("title", []))
            print(f"  {key}: {text}")
        elif value_type in ("select", "status"):
            print(f"  {key}: {(value.get(value_type) or {}).get('name')}")

    print("\n=== Email Sequences in Beta Activation ===")
    sequence_rows = nc.query_db("email_sequences")
    beta_sequences = []
    normalized_campaign_id = BETA_CAMPAIGN_ID.replace("-", "")
    for row in sequence_rows:
        raw_campaigns = row.get("Campaign") or row.get("Campaigns") or []
        campaign_ids = raw_campaigns if isinstance(raw_campaigns, list) else [raw_campaigns]
        normalized_ids = [campaign_id.replace("-", "") for campaign_id in campaign_ids if campaign_id]
        if normalized_campaign_id in normalized_ids:
            beta_sequences.append(row)

    print(f"Found {len(beta_sequences)} sequences linked to Beta Activation")
    for sequence in beta_sequences:
        print(json.dumps({key: str(value)[:100] for key, value in sequence.items() if key != "_url"}, default=str))

    print("\n=== All email_sequences (names only) ===")
    for row in sequence_rows:
        name = row.get("Name") or row.get("Subject") or row.get("_id", "")
        step = row.get("Step") or row.get("Order") or row.get("Sequence Order") or ""
        campaign = row.get("Campaign") or row.get("Campaigns") or ""
        print(f"  step={step!r:6}  name={str(name)[:60]:60}  campaign_ids={str(campaign)[:80]}")


if __name__ == "__main__":
    main()
