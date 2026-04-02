#!/usr/bin/env python3
"""
Email Template Audit
━━━━━━━━━━━━━━━━━━━━
Pulls full email template content from Notion together with per-template metrics.

Usage:
    python Business/ANALYTICS/executions/email_template_audit.py --action summary
    python Business/ANALYTICS/executions/email_template_audit.py --action markdown
    python Business/ANALYTICS/executions/email_template_audit.py --action json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(_EXEC_DIR)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from shared.notion_client import list_block_children, query_db


TEXT_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "quote",
    "callout",
}


def _extract_rich_text(block: dict) -> str:
    block_type = block.get("type")
    if block_type == "code":
        rich_text = block.get("code", {}).get("rich_text", [])
    elif block_type in TEXT_BLOCK_TYPES:
        rich_text = block.get(block_type, {}).get("rich_text", [])
    else:
        rich_text = []
    return "".join(seg.get("plain_text", "") for seg in rich_text).strip()


def _read_template_bodies() -> dict[str, str]:
    rows = query_db("email_sequences")
    bodies: dict[str, str] = {}
    for row in rows:
        page_id = row["_id"]
        blocks = list_block_children(page_id)
        content_parts: list[str] = []
        for block in blocks:
            text = _extract_rich_text(block)
            if text:
                content_parts.append(text)
        bodies[page_id] = "\n".join(content_parts).strip()
    return bodies


def _read_template_metrics() -> list[dict]:
    rows = query_db("email_sequences")
    metrics: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        sent_count = int(row.get("Sent Count") or row.get("Total Sent") or 0)
        delivered_count = int(row.get("Delivered Count") or row.get("Total Delivered") or 0)
        opened_count = int(row.get("Opened Count") or row.get("Total Opened") or 0)
        clicked_count = int(row.get("Clicked Count") or row.get("Total Clicked") or 0)
        bounced_count = int(row.get("Bounced Count") or row.get("Total Bounced") or 0)
        replied_count = int(row.get("Replied Count") or row.get("Total Replied") or 0)
        delivery_rate_pct = round(delivered_count / sent_count * 100, 1) if sent_count else 0.0
        metrics.append({
            "id": row.get("_id", ""),
            "template_name": row.get("Template") or row.get("Name") or "",
            "subject_line": row.get("Subject Line") or "",
            "sent_count": sent_count,
            "delivered_count": delivered_count,
            "opened_count": opened_count,
            "clicked_count": clicked_count,
            "bounced_count": bounced_count,
            "replied_count": replied_count,
            "open_rate": row.get("Open Rate") or 0,
            "click_rate": row.get("Click Rate") or 0,
            "bounce_rate": row.get("Bounce Rate") or 0,
            "reply_rate": row.get("Reply Rate") or 0,
            "delivery_rate_pct": delivery_rate_pct,
            "invisible_fail_count": max(0, sent_count - delivered_count - bounced_count),
            "seq_num": idx,
        })
    return metrics


def build_template_audit() -> list[dict]:
    metrics = _read_template_metrics()
    bodies = _read_template_bodies()
    audit: list[dict] = []
    for item in metrics:
        audit.append({
            **item,
            "content": bodies.get(item["id"], ""),
        })
    audit.sort(key=lambda row: (row.get("seq_num", 0), row.get("template_name", "")))
    return audit


def _format_summary(rows: list[dict]) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  EMAIL TEMPLATE AUDIT")
    lines.append("=" * 60)
    lines.append("")
    for row in rows:
        lines.append(f"[{row['template_name']}]")
        lines.append(f"  Subject: {row['subject_line']}")
        lines.append(
            f"  Sent: {row['sent_count']} | Delivered: {row['delivered_count']} | "
            f"Open: {row['open_rate']}% | Click: {row['click_rate']}% | Reply: {row['reply_rate']}%"
        )
        preview = row.get("content", "").splitlines()
        preview_text = " ".join(line.strip() for line in preview[:3] if line.strip())
        if len(preview_text) > 180:
            preview_text = preview_text[:177] + "..."
        lines.append(f"  Preview: {preview_text}")
        lines.append("")
    return "\n".join(lines)


def _format_markdown(rows: list[dict]) -> str:
    lines = []
    lines.append("# Email Template Audit")
    lines.append("")
    lines.append("Generated by `Business/ANALYTICS/executions/email_template_audit.py`.")
    lines.append("")
    for row in rows:
        lines.append(f"## {row['template_name']}")
        lines.append("")
        lines.append(f"- Subject line: {row['subject_line']}")
        lines.append(f"- Sent: {row['sent_count']}")
        lines.append(f"- Delivered: {row['delivered_count']}")
        lines.append(f"- Opened: {row['opened_count']}")
        lines.append(f"- Clicked: {row['clicked_count']}")
        lines.append(f"- Bounced: {row['bounced_count']}")
        lines.append(f"- Replied: {row['replied_count']}")
        lines.append(f"- Open rate: {row['open_rate']}%")
        lines.append(f"- Click rate: {row['click_rate']}%")
        lines.append(f"- Bounce rate: {row['bounce_rate']}%")
        lines.append(f"- Reply rate: {row['reply_rate']}%")
        lines.append(f"- Delivery rate: {row['delivery_rate_pct']}%")
        lines.append(f"- Invisible fails: {row['invisible_fail_count']}")
        lines.append("")
        lines.append("```text")
        lines.append(row.get("content", ""))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit full email templates and metrics")
    parser.add_argument("--action", required=True, choices=["summary", "markdown", "json"])
    args = parser.parse_args()

    rows = build_template_audit()

    if args.action == "summary":
        print(_format_summary(rows))
    elif args.action == "markdown":
        print(_format_markdown(rows))
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()