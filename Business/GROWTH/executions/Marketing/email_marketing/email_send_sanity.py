#!/usr/bin/env python3
"""
email_send_sanity.py — Read-only fallback sanity check for email sends.

Purpose:
    Inspect assigned leads, campaign membership, next template in sequence,
    and send eligibility without touching Railway or sending anything.

Usage:
    python email_send_sanity.py --action summary
    python email_send_sanity.py --action summary --limit 10
    python email_send_sanity.py --action lead --email user@example.com
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta


def _find_workspace() -> str:
    root = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(root, "shared")) and os.path.isdir(os.path.join(root, "Business")):
            return root
        root = os.path.dirname(root)
    raise RuntimeError("Cannot locate workspace root")


_WORKSPACE = _find_workspace()
_MARKETING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (_WORKSPACE, _MARKETING_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WORKSPACE, ".env"))

import shared.notion_client as notion_client
from shared.notion_client import log_task


def _patch_relation_extractor() -> None:
    original = notion_client._extract_value

    def patched(prop: dict):
        if prop.get("type") == "relation":
            return [item["id"] for item in prop.get("relation", [])]
        return original(prop)

    notion_client._extract_value = patched


_patch_relation_extractor()

from email_marketing.campaigns import read_campaigns
from email_marketing.templates import list_templates_for_campaign
from email_marketing.leads import _read_leads_full


def _flatten_relation_ids(value) -> list[str]:
    ids: list[str] = []
    if isinstance(value, dict):
        page_id = value.get("id")
        if page_id:
            ids.append(page_id)
    elif isinstance(value, list):
        for item in value:
            ids.extend(_flatten_relation_ids(item))
    return ids


def _parse_last_send(raw) -> str:
    if not raw:
        return ""
    if isinstance(raw, dict):
        return raw.get("start") or ""
    return str(raw)


def _get_state():
    campaigns = read_campaigns(status_filter="Active")
    leads, email_to_rel = _read_leads_full(exclude_unsubscribed=True)
    templates_by_campaign = {
        campaign["id"]: list_templates_for_campaign(campaign["id"])
        for campaign in campaigns
    }
    return campaigns, leads, email_to_rel, templates_by_campaign


def _next_template_for_lead(lead: dict, campaign_templates: list[dict]) -> dict | None:
    sent_template_ids = set(_flatten_relation_ids(lead.get("pipeline_stage") or []))
    for template in campaign_templates:
        if template["id"] not in sent_template_ids:
            return template
    return None


def _eligibility_for_lead(lead: dict, campaign: dict, next_template: dict | None) -> tuple[bool, str]:
    if next_template is None:
        return False, "sequence complete"

    last_send = _parse_last_send(lead.get("last_send"))
    if not last_send:
        return True, "no prior send recorded"

    try:
        sent_at = datetime.fromisoformat(last_send.replace("Z", "+00:00"))
    except ValueError:
        return True, f"unparseable last_send={last_send}"

    hours_since = (datetime.now(timezone.utc) - sent_at).total_seconds() / 3600
    wait_hours = float(campaign.get("send_frequency") or 0)
    if hours_since >= wait_hours:
        return True, f"due now; last send {hours_since:.1f}h ago"
    remaining = max(0.0, wait_hours - hours_since)
    return False, f"cooldown; wait {remaining:.1f}h"


def run_sanity_check(limit: int = 5) -> dict:
    campaigns, leads, email_to_rel, templates_by_campaign = _get_state()
    total_due = 0
    total_assigned = 0
    total_unassigned = 0
    results = []

    for campaign in sorted(campaigns, key=lambda item: -item["campaign_score"]):
        campaign_id = campaign["id"]
        templates = templates_by_campaign[campaign_id]
        members = [lead for lead in leads if campaign_id in email_to_rel.get(lead["email"], [])]
        total_assigned += len(members)

        due = []
        cooling_down = 0
        complete = 0
        for lead in members:
            next_template = _next_template_for_lead(lead, templates)
            should_send, reason = _eligibility_for_lead(lead, campaign, next_template)
            row = {
                "email": lead["email"],
                "segment": lead["segment"],
                "score": lead["score"],
                "last_send": _parse_last_send(lead.get("last_send")),
                "next_template": next_template["template_name"] if next_template else None,
                "subject_line": next_template["subject_line"] if next_template else None,
                "reason": reason,
            }
            if next_template is None:
                complete += 1
            elif should_send:
                due.append(row)
            else:
                cooling_down += 1

        total_due += len(due)
        results.append({
            "campaign": campaign["name"],
            "campaign_score": campaign["campaign_score"],
            "send_frequency": campaign["send_frequency"],
            "template_count": len(templates),
            "assigned": len(members),
            "due": len(due),
            "cooling_down": cooling_down,
            "complete": complete,
            "due_rows": due[:limit],
        })

    total_unassigned = len(leads) - total_assigned

    print("=" * 72)
    print("  EMAIL SEND SANITY CHECK")
    print("=" * 72)
    for item in results:
        print(
            f"\n  {item['campaign']:<30} score={item['campaign_score']:<4} "
            f"freq={item['send_frequency']}h templates={item['template_count']} "
            f"assigned={item['assigned']} due={item['due']} cooldown={item['cooling_down']} complete={item['complete']}"
        )
        if item["due_rows"]:
            print("      Next emails due:")
            for row in item["due_rows"]:
                subject = (row["subject_line"] or "")[:55]
                print(
                    f"        {row['email']:<35} [{row['segment']}] "
                    f"->{row['next_template']} | {subject}"
                )
                print(f"           reason: {row['reason']}")

    print(f"\n{'-' * 72}")
    print(f"  Assigned leads:   {total_assigned}")
    print(f"  Unassigned leads: {total_unassigned}")
    print(f"  Emails due now:   {total_due}")

    try:
        log_task(
            "Marketing",
            "email-sequences/sanity-check",
            "Complete",
            "P2",
            f"Assigned={total_assigned}, Unassigned={total_unassigned}, Due={total_due}",
        )
    except Exception:
        pass

    return {
        "assigned": total_assigned,
        "unassigned": total_unassigned,
        "due": total_due,
        "campaigns": results,
    }


def inspect_lead(email: str) -> dict:
    campaigns, leads, email_to_rel, templates_by_campaign = _get_state()
    lead = next((item for item in leads if item["email"].lower() == email.lower()), None)
    if not lead:
        raise ValueError(f"Lead not found: {email}")

    campaign_ids = email_to_rel.get(lead["email"], [])
    sent_template_ids = set(_flatten_relation_ids(lead.get("pipeline_stage") or []))
    print("=" * 72)
    print(f"  LEAD INSPECTION — {lead['email']}")
    print("=" * 72)
    print(f"  Segment:   {lead['segment']}")
    print(f"  Score:     {lead['score']}")
    print(f"  Last send: {_parse_last_send(lead.get('last_send')) or 'none'}")
    print(f"  Source:    {lead['source']}")
    print()

    for campaign in sorted(campaigns, key=lambda item: -item["campaign_score"]):
        if campaign["id"] not in campaign_ids:
            continue
        templates = templates_by_campaign[campaign["id"]]
        next_template = _next_template_for_lead(lead, templates)
        should_send, reason = _eligibility_for_lead(lead, campaign, next_template)
        print(f"  Campaign: {campaign['name']}")
        print(f"    Assigned: yes")
        print(f"    Templates in campaign: {len(templates)}")
        print(f"    Sent template matches: {sum(1 for t in templates if t['id'] in sent_template_ids)}")
        print(f"    Next template: {next_template['template_name'] if next_template else 'none'}")
        print(f"    Subject: {(next_template['subject_line'] if next_template else '')}")
        print(f"    Should send now: {'yes' if should_send else 'no'}")
        print(f"    Reason: {reason}")
        print()

    return {
        "email": lead["email"],
        "campaign_ids": campaign_ids,
        "sent_template_ids": sorted(sent_template_ids),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only email send sanity checker")
    parser.add_argument("--action", choices=["summary", "lead"], default="summary")
    parser.add_argument("--limit", type=int, default=5, help="Max due leads shown per campaign")
    parser.add_argument("--email", help="Inspect a single lead email")
    args = parser.parse_args()

    if args.action == "lead":
        if not args.email:
            parser.error("--email is required for --action lead")
        inspect_lead(args.email)
    else:
        run_sanity_check(limit=args.limit)
