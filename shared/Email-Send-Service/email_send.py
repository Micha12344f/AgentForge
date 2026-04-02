#!/usr/bin/env python3
"""
Email Send Workflow
━━━━━━━━━━━━━━━━━━
Orchestrates email sending across active Notion campaigns:
  1. Pull active campaigns (Status == Active)
  2. Load audiences per campaign via dual-relation
  3. Enrich leads: First Name, Email, Last send, Pipeline stage — exclude unsubscribed
  4. Apply Send Frequency + global cooldown filter
  5. Resolve campaign overlaps using Campaign Score (one email per lead per run)
  6. Determine next email from Pipeline stage → Email Sequences
  7. Load & personalise templates from Notion blocks
  8. Send via Resend, log to Email Logs (dual-relation auto-syncs rollups)

Returns a summary dict for the entry point.
"""

import os
import re
import html as _html_mod
import logging
from collections import Counter
from datetime import datetime, timezone, timedelta

from shared.notion_client import (
    update_row, add_row, DATABASES,
    notion_request, _API_BASE,
)
from shared.resend_client import send_email

log = logging.getLogger(__name__)

# ── Config ──
GLOBAL_MIN_COOLDOWN_HOURS = 12


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _notion_headers():
    token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def query_db_raw(db_key, filt=None, page_size=100):
    """Query a Notion DB returning raw page objects (preserves relation IDs)."""
    db_id = DATABASES[db_key]
    body = {"page_size": page_size}
    if filt:
        body["filter"] = filt
    results = []
    while True:
        resp = notion_request(
            "post", f"{_API_BASE}/databases/{db_id}/query",
            headers=_notion_headers(), json=body, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results.extend(data["results"])
        if not data.get("has_more"):
            break
        body["start_cursor"] = data["next_cursor"]
    return results


def extract_raw(page, prop_name):
    """Extract a value from a raw Notion page, handling all property types."""
    p = page["properties"].get(prop_name)
    if not p:
        return None
    t = p["type"]
    if t == "title":
        return "".join(rt["plain_text"] for rt in p.get("title", []))
    elif t == "rich_text":
        return "".join(rt["plain_text"] for rt in p.get("rich_text", []))
    elif t == "number":
        return p.get("number")
    elif t in ("select", "status"):
        v = p.get(t)
        return v["name"] if v else None
    elif t == "multi_select":
        return [s["name"] for s in p.get("multi_select", [])]
    elif t == "date":
        d = p.get("date")
        return d["start"] if d else None
    elif t == "checkbox":
        return p.get("checkbox", False)
    elif t == "email":
        return p.get("email")
    elif t == "url":
        return p.get("url")
    elif t == "relation":
        return [r["id"] for r in p.get("relation", [])]
    elif t == "formula":
        f = p.get("formula", {})
        return f.get(f.get("type"))
    elif t == "rollup":
        r = p.get("rollup", {})
        rtype = r.get("type")
        if rtype == "array":
            arr = r.get("array", [])
            vals = []
            for item in arr:
                it = item.get("type")
                if it == "formula":
                    ff = item["formula"]
                    vals.append(ff.get(ff.get("type")))
                elif it == "title":
                    vals.append("".join(rt["plain_text"] for rt in item.get("title", [])))
                elif it == "rich_text":
                    vals.append("".join(rt["plain_text"] for rt in item.get("rich_text", [])))
                else:
                    vals.append(item.get(it))
            return vals
        return r.get(rtype)
    return None


def parse_timestamp(ts):
    """Parse a Notion date value (string or rollup dict) to aware datetime."""
    if not ts:
        return None
    if isinstance(ts, dict):
        ts = ts.get("start")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _extract_sent_seq_ids(pipeline_stage_val):
    """Return set of email_sequence page IDs (no dashes) already sent to this lead.

    Pipeline stage is a rollup of Email Logs → Email Sequence. extract_raw returns
    the array items, each being a list of relation dicts: [[{'id': '...'}], ...].
    Handles both the extract_raw form (list of lists) and the raw Notion form
    (list of {'type': 'relation', 'relation': [...]} dicts).
    """
    sent = set()
    if not pipeline_stage_val or not isinstance(pipeline_stage_val, list):
        return sent
    for item in pipeline_stage_val:
        if isinstance(item, list):
            # extract_raw form: [[{'id': 'abc-123'}], ...]
            for rel in item:
                if isinstance(rel, dict) and rel.get("id"):
                    sent.add(rel["id"].replace("-", ""))
        elif isinstance(item, dict):
            if item.get("type") == "relation":
                # raw Notion form: [{'type': 'relation', 'relation': [{'id': '...'}]}, ...]
                for rel in item.get("relation", []):
                    if rel.get("id"):
                        sent.add(rel["id"].replace("-", ""))
    return sent


def load_template_body(page_id):
    """Fetch text content of an Email Sequence Notion page via blocks API."""
    hdrs = _notion_headers()
    resp = notion_request("get", f"{_API_BASE}/blocks/{page_id}/children", headers=hdrs, timeout=15)
    resp.raise_for_status()
    blocks = resp.json().get("results", [])
    parts = []
    for block in blocks:
        btype = block["type"]
        text_types = (
            "paragraph", "heading_1", "heading_2", "heading_3",
            "bulleted_list_item", "numbered_list_item",
        )
        if btype in text_types:
            rich = block[btype].get("rich_text", [])
            parts.append("".join(rt["plain_text"] for rt in rich))
        elif btype == "code":
            rich = block["code"].get("rich_text", [])
            parts.append("".join(rt["plain_text"] for rt in rich))
        elif btype == "divider":
            parts.append("---")
    return "\n\n".join(parts)


def personalise(text, first_name):
    """Replace {{Name}} / {{name}} placeholders."""
    name = first_name if first_name and first_name.lower() != "there" else "there"
    return re.sub(r"\{\{[Nn]ame\}\}", name, text)


def text_to_html(text):
    """Convert plain-text template to basic HTML email body."""
    escaped = _html_mod.escape(text)
    escaped = re.sub(r"(https?://[^\s<>]+)", r'<a href="\1">\1</a>', escaped)
    return escaped.replace("\n", "<br>\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Pipeline steps
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def step2_pull_campaigns():
    """Pull active campaigns from Notion."""
    campaigns_raw = query_db_raw(
        "campaigns",
        filt={"property": "Status", "status": {"equals": "Active"}},
    )
    campaigns = []
    for page in campaigns_raw:
        freq = extract_raw(page, "Send Frequency")
        score = extract_raw(page, "Campaign Score")
        campaigns.append({
            "id":             page["id"],
            "name":           extract_raw(page, "Name") or "Unnamed",
            "send_frequency": freq if freq is not None else 48,
            "campaign_score": score if score is not None else 0,
        })
    log.info("Active campaigns: %d", len(campaigns))
    for c in campaigns:
        log.info("  - %s  |  freq: %sh  |  score: %s", c["name"], c["send_frequency"], c["campaign_score"])
    return campaigns


def step3_load_audiences(campaigns):
    """Load & enrich audiences from email_sends DB."""
    lead_map = {}
    for campaign in campaigns:
        leads_raw = query_db_raw(
            "email_sends",
            filt={
                "and": [
                    {"property": "Campaign", "relation": {"contains": campaign["id"]}},
                    {"property": "Unsubscribed", "checkbox": {"equals": False}},
                ]
            },
        )
        for page in leads_raw:
            lid = page["id"]
            if lid not in lead_map:
                first = extract_raw(page, "First Name") or ""
                if not first:
                    full = extract_raw(page, "Subject") or ""
                    first = full.split()[0] if full.strip() else ""
                lead_map[lid] = {
                    "id":             lid,
                    "first_name":     first or "there",
                    "email":          extract_raw(page, "Email"),
                    "last_send":      extract_raw(page, "Last send"),
                    "pipeline_stage": extract_raw(page, "Pipeline stage"),
                    "campaigns":      [],
                }
            lead_map[lid]["campaigns"].append(campaign)

    lead_map = {lid: d for lid, d in lead_map.items() if d["email"]}
    log.info("Unique leads (non-unsubscribed, with email): %d", len(lead_map))
    return lead_map


def step4_frequency_filter(lead_map, now):
    """Apply send frequency + global cooldown filter."""
    eligible = {}
    skipped_global = 0
    skipped_freq = 0

    for lid, data in lead_map.items():
        last_send_dt = parse_timestamp(data["last_send"])
        if last_send_dt and (now - last_send_dt) < timedelta(hours=GLOBAL_MIN_COOLDOWN_HOURS):
            skipped_global += 1
            continue

        ok_campaigns = []
        for campaign in data["campaigns"]:
            freq_hours = campaign["send_frequency"]
            if last_send_dt and (now - last_send_dt) < timedelta(hours=freq_hours):
                skipped_freq += 1
                continue
            ok_campaigns.append(campaign)

        if ok_campaigns:
            eligible[lid] = {**data, "eligible_campaigns": ok_campaigns}

    log.info("Frequency filter: %d passed, %d global skip, %d freq skip",
             len(eligible), skipped_global, skipped_freq)
    return eligible


def step5_resolve_overlaps(eligible, now):
    """Resolve campaign overlaps — highest Campaign Score wins."""
    send_queue = []
    for lid, data in eligible.items():
        camps = data["eligible_campaigns"]
        if len(camps) == 1:
            winner = camps[0]
        else:
            last_send_dt = parse_timestamp(data["last_send"])

            def _score(camp, _ls=last_send_dt):
                overdue = 0.0
                if _ls:
                    overdue = max(0, (now - _ls).total_seconds() / 3600 - camp["send_frequency"])
                return (camp["campaign_score"], overdue)

            winner = max(camps, key=_score)
            deferred = [c["name"] for c in camps if c["id"] != winner["id"]]
            log.info("  Overlap: %s -> %s wins over %s", data["email"], winner["name"], deferred)
        send_queue.append({"lead": data, "campaign": winner})

    log.info("Send queue: %d emails", len(send_queue))
    return send_queue


def step6_determine_next_email(send_queue, dry_run):
    """Determine next email for each lead from Email Sequences."""
    campaign_sequences = {}
    campaign_ids_needed = {item["campaign"]["id"] for item in send_queue}

    for cid in campaign_ids_needed:
        seqs_raw = query_db_raw(
            "email_sequences",
            filt={"property": "Campaign", "relation": {"contains": cid}},
        )
        parsed = []
        for page in seqs_raw:
            name = extract_raw(page, "Template") or ""
            subj = extract_raw(page, "Subject Line") or name
            num_match = re.search(r"(\d+)", name)
            num = int(num_match.group(1)) if num_match else 0
            parsed.append({"id": page["id"], "name": name, "subject": subj, "number": num})
        parsed.sort(key=lambda x: x["number"])
        campaign_sequences[cid] = parsed
        log.info("  %s... -> %d sequences", cid[:8], len(parsed))

    final_queue = []
    for item in send_queue:
        lead = item["lead"]
        campaign = item["campaign"]
        cid = campaign["id"]
        sequences = campaign_sequences.get(cid, [])

        # Set-based lookup: first sequence whose ID is not in the already-sent set.
        # This is independent of template numbering — works across gaps, renames,
        # and reordering. The rollup gives us exactly the sent sequence IDs.
        sent_ids = _extract_sent_seq_ids(lead["pipeline_stage"])
        next_seq = next(
            (seq for seq in sequences if seq["id"].replace("-", "") not in sent_ids),
            None,
        )

        if not next_seq:
            log.info(
                "  Done: %s — all %d sequences sent for '%s'",
                lead["email"], len(sequences), campaign["name"],
            )
            if not dry_run:
                update_row(lead["id"], "email_sends", {"Pipeline Stage": "Complete"})
            continue

        final_queue.append({"lead": lead, "campaign": campaign, "sequence": next_seq})

    log.info("Final send queue: %d emails ready", len(final_queue))
    return final_queue


def step7_load_templates(final_queue):
    """Load & personalise templates from Notion blocks."""
    prepared = []
    for item in final_queue:
        seq = item["sequence"]
        lead = item["lead"]
        raw_body = load_template_body(seq["id"])
        body = personalise(raw_body, lead["first_name"])
        subject = personalise(seq["subject"], lead["first_name"])
        html_body = text_to_html(body)
        prepared.append({
            "lead": lead, "campaign": item["campaign"],
            "sequence": seq, "subject": subject, "html_body": html_body,
        })
    log.info("Templates loaded & personalised: %d", len(prepared))
    return prepared


def step8_send_and_log(prepared, now, dry_run):
    """Send emails via Resend, log to Email Logs DB."""
    sent_count = 0
    error_count = 0
    results_log = []

    for p in prepared:
        lead = p["lead"]
        campaign = p["campaign"]
        seq = p["sequence"]

        if dry_run:
            log.info("  [DRY RUN] Would send to %s: \"%s\" (%s)",
                     lead["email"], p["subject"], campaign["name"])
            results_log.append({"email": lead["email"], "campaign": campaign["name"], "status": "dry_run"})
            sent_count += 1
            continue

        try:
            resp = send_email(
                to=lead["email"],
                subject=p["subject"],
                html=p["html_body"],
                reply_to="reply@hedgedge.info",
                tags=[
                    {"name": "campaign", "value": campaign["name"]},
                    {"name": "sequence", "value": seq["name"]},
                ],
                include_unsubscribe=True,
                respect_notion_unsubscribe=False,
            )
            resend_id = resp.get("id", "")

            add_row("email_logs", {
                "Subject":        p["subject"],
                "Email":          lead["email"],
                "Email Sequence": seq["id"],
                "Email Send":     lead["id"],
                "Timestamp":      now.isoformat(),
                "Sent":           True,
                "Resend ID":      resend_id,
            })

            sent_count += 1
            results_log.append({"email": lead["email"], "campaign": campaign["name"], "status": "sent"})
            log.info("  Sent to %s: \"%s\"", lead["email"], p["subject"])

        except Exception as e:
            error_count += 1
            results_log.append({"email": lead["email"], "campaign": campaign["name"], "status": f"error: {e}"})
            log.error("  FAILED %s: %s", lead["email"], e)

    camp_counts = Counter(r["campaign"] for r in results_log)
    return {
        "total_prepared": len(prepared),
        "sent": sent_count,
        "errors": error_count,
        "dry_run": dry_run,
        "per_campaign": dict(camp_counts),
        "results_log": results_log,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main orchestrator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_email_send(dry_run=False):
    """Execute the full email send workflow. Returns summary dict."""
    now = datetime.now(timezone.utc)
    log.info("=" * 60)
    log.info("Email Send Workflow | DRY_RUN=%s | %s", dry_run, now.strftime("%Y-%m-%d %H:%M UTC"))
    log.info("=" * 60)

    campaigns = step2_pull_campaigns()
    if not campaigns:
        log.info("No active campaigns found — nothing to do.")
        return {"total_prepared": 0, "sent": 0, "errors": 0, "dry_run": dry_run, "per_campaign": {}}

    lead_map = step3_load_audiences(campaigns)
    if not lead_map:
        log.info("No eligible leads found — nothing to do.")
        return {"total_prepared": 0, "sent": 0, "errors": 0, "dry_run": dry_run, "per_campaign": {}}

    eligible = step4_frequency_filter(lead_map, now)
    if not eligible:
        log.info("All leads filtered by frequency — nothing to send.")
        return {"total_prepared": 0, "sent": 0, "errors": 0, "dry_run": dry_run, "per_campaign": {}}

    send_queue = step5_resolve_overlaps(eligible, now)
    final_queue = step6_determine_next_email(send_queue, dry_run)
    if not final_queue:
        log.info("No emails to send after sequence resolution.")
        return {"total_prepared": 0, "sent": 0, "errors": 0, "dry_run": dry_run, "per_campaign": {}}

    prepared = step7_load_templates(final_queue)
    summary = step8_send_and_log(prepared, now, dry_run)

    log.info("=" * 60)
    log.info("SEND REPORT")
    log.info("=" * 60)
    log.info("  Total prepared:  %d", summary["total_prepared"])
    log.info("  Sent:            %d", summary["sent"])
    log.info("  Errors:          %d", summary["errors"])
    log.info("  DRY_RUN:         %s", summary["dry_run"])
    for camp, count in summary["per_campaign"].items():
        log.info("    - %s: %d", camp, count)

    return summary
