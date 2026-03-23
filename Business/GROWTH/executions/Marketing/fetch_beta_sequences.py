#!/usr/bin/env python3
"""Fetch beta email sequence pages and preview their Notion properties and body blocks."""

import os
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
import shared.notion_client as nc

load_dotenv(WORKSPACE_ROOT / ".env")

SEQUENCE_IDS = [
    "329652ea-6c6d-8195-b4a2-c5aa4441e180",
    "329652ea-6c6d-81c0-95a8-c432674a0d54",
    "329652ea-6c6d-819a-b59e-d9d5808e7e8e",
]


def main() -> None:
    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": nc._NOTION_VERSION,
        "Content-Type": "application/json",
    }

    for sequence_id in SEQUENCE_IDS:
        response = nc.notion_request(
            "get",
            f"{nc._API_BASE}/pages/{sequence_id}",
            headers=headers,
            timeout=20,
        )
        page = response.json()
        props = page.get("properties", {})
        print(f"\n=== Sequence {sequence_id} ===")
        for key, value in props.items():
            value_type = value.get("type")
            if value_type == "title":
                text = "".join(item.get("plain_text", "") for item in value.get("title", []))
                print(f"  {key} (title): {text}")
            elif value_type == "rich_text":
                text = "".join(item.get("plain_text", "") for item in value.get("rich_text", []))
                if text:
                    print(f"  {key}: {text[:200]}")
            elif value_type in ("select", "status"):
                print(f"  {key}: {(value.get(value_type) or {}).get('name')}")
            elif value_type == "number":
                print(f"  {key}: {value.get('number')}")
            elif value_type == "relation":
                ids = [item.get("id") for item in value.get("relation", [])]
                if ids:
                    print(f"  {key}: {ids}")
            elif value_type == "checkbox":
                print(f"  {key}: {value.get('checkbox')}")

        blocks_response = nc.notion_request(
            "get",
            f"{nc._API_BASE}/blocks/{sequence_id}/children",
            headers=headers,
            timeout=20,
        )
        blocks = blocks_response.json().get("results", [])
        if blocks:
            print(f"  [body blocks: {len(blocks)}]")
            for block in blocks[:3]:
                block_type = block.get("type", "")
                text_content = ""
                if block_type in block:
                    rich_text = block[block_type].get("rich_text", [])
                    text_content = "".join(item.get("plain_text", "") for item in rich_text)
                if text_content:
                    print(f"    {block_type}: {text_content[:120]}")


if __name__ == "__main__":
    main()
