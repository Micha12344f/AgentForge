"""
leads.py — Lead management layer.

Read leads_crm and manage campaign audience assignments.
Consumed by email_send_sanity.py, Send_Emails.ipynb, and the E2E test.
"""

import os
import sys

# Ensure workspace root and Marketing dir are importable
def _find_ws_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "shared")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
_MARKETING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_WS_ROOT, _MARKETING_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import shared.notion_client as _nc  # noqa: E402
from email_marketing.config import query_db, update_row, SEGMENTS  # noqa: E402


# ── Patch relation extractor so relation fields return page ID lists ─────────

def _patch_relation_extractor() -> None:
    original = _nc._extract_value

    def _patched(prop: dict):
        if prop.get("type") == "relation":
            return [item["id"] for item in prop.get("relation", [])]
        return original(prop)

    _nc._extract_value = _patched


_patch_relation_extractor()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _score_to_segment(score) -> str:
    """Classify a numeric engagement score into a segment name using SEGMENTS."""
    s = int(score or 0)
    for seg_name, (lo, hi) in SEGMENTS.items():
        if s >= lo and (hi == float("inf") or s <= hi):
            return seg_name
    return "Cold"


def _parse_lead(row: dict) -> dict:
    """Map a raw Notion row to a clean lead dict."""
    score = row.get("Engagement Score") or row.get("Score") or 0
    segment = row.get("Segment") or _score_to_segment(score)
    return {
        "id":              row.get("_id", ""),
        "email":           row.get("Email") or "",
        "first_name":      row.get("First Name") or "",
        "last_name":       row.get("Last Name") or "",
        "score":           int(score) if score is not None else 0,
        "segment":         segment,
        "pipeline_stage":  row.get("Pipeline stage") or [],
        "last_send":       row.get("Last send") or "",
        "source":          row.get("Source") or "",
        "unsubscribed":    bool(row.get("Unsubscribed") or False),
        # internal — campaign relation IDs (not exposed publicly via read_leads)
        "_campaign_ids":   row.get("Campaign") or [],
    }


# ── Public API ────────────────────────────────────────────────────────────────

def read_leads(
    segment: str | None = None,
    exclude_unsubscribed: bool = True,
) -> list[dict]:
    """Return leads from leads_crm, optionally filtered.

    Args:
        segment: "Cold", "Warm", or "Hot". Pass None for all.
        exclude_unsubscribed: Skip unsubscribed leads when True.

    Returns:
        List of lead dicts: email, score, segment, pipeline_stage, source, last_send.
    """
    rows = query_db("leads_crm")
    leads = []
    for row in rows:
        lead = _parse_lead(row)
        if exclude_unsubscribed and lead["unsubscribed"]:
            continue
        if segment and lead["segment"] != segment:
            continue
        leads.append(lead)
    return leads


def _read_leads_full(
    exclude_unsubscribed: bool = True,
) -> tuple[list[dict], dict[str, list[str]]]:
    """Return (leads, email_to_campaign_ids) for full assignment analysis.

    The second element maps lead email → list of campaign Notion page IDs
    extracted from the Campaign relation.

    Args:
        exclude_unsubscribed: Skip unsubscribed leads when True.

    Returns:
        (list[lead_dict], dict[email, list[campaign_id]])
    """
    rows = query_db("leads_crm")
    leads: list[dict] = []
    email_to_rel: dict[str, list[str]] = {}
    for row in rows:
        lead = _parse_lead(row)
        if exclude_unsubscribed and lead["unsubscribed"]:
            continue
        leads.append(lead)
        if lead["email"]:
            email_to_rel[lead["email"]] = lead["_campaign_ids"]
    return leads, email_to_rel


def preview_assignments(
    campaign_id: str,
    min_score: int = 0,
    segment: str | None = None,
) -> list[dict]:
    """Dry-run: return leads that meet criteria for a campaign.

    Args:
        campaign_id: Target campaign Notion page ID.
        min_score: Minimum engagement score threshold.
        segment: Restrict to a single segment ("Cold"/"Warm"/"Hot").

    Returns:
        List of lead dicts with extra 'already_assigned' boolean field.
    """
    leads, email_to_rel = _read_leads_full(exclude_unsubscribed=True)
    candidates = []
    for lead in leads:
        if lead["score"] < min_score:
            continue
        if segment and lead["segment"] != segment:
            continue
        already = campaign_id in email_to_rel.get(lead["email"], [])
        candidates.append({**lead, "already_assigned": already})
    return candidates


def assign_leads_by_score(
    campaign_id: str,
    min_score: int = 0,
    segment: str | None = None,
    dry_run: bool = True,
) -> dict:
    """Assign qualifying leads to a campaign via the Audience relation.

    Only leads NOT already in the campaign are touched.

    Args:
        campaign_id: Target campaign Notion page ID.
        min_score: Minimum engagement score.
        segment: Restrict to a segment.
        dry_run: When True, count only — no Notion writes.

    Returns:
        Dict with total_candidates, assigned, dry_run.
    """
    candidates = preview_assignments(campaign_id, min_score, segment)
    to_assign = [c for c in candidates if not c["already_assigned"]]
    prefix = "DRY RUN: " if dry_run else ""
    print(f"  {prefix}Assigning {len(to_assign)} leads to campaign {campaign_id[:8]}...")

    assigned = 0
    for lead in to_assign:
        if not dry_run:
            try:
                new_ids = list(set(lead["_campaign_ids"] + [campaign_id]))
                update_row(lead["id"], "leads_crm", {
                    "Campaign": new_ids,
                })
                assigned += 1
            except Exception as e:
                print(f"    Failed {lead['email']}: {e}")
        else:
            assigned += 1

    return {"total_candidates": len(candidates), "assigned": assigned, "dry_run": dry_run}


def clear_assignments(
    campaign_id: str,
    dry_run: bool = True,
) -> dict:
    """Remove all leads from a campaign's Audience relation.

    Args:
        campaign_id: Target campaign Notion page ID.
        dry_run: When True, count only — no Notion writes.

    Returns:
        Dict with cleared, dry_run.
    """
    leads, email_to_rel = _read_leads_full(exclude_unsubscribed=False)
    members = [l for l in leads if campaign_id in email_to_rel.get(l["email"], [])]
    prefix = "DRY RUN: " if dry_run else ""
    print(f"  {prefix}Clearing {len(members)} leads from campaign {campaign_id[:8]}...")

    cleared = 0
    for lead in members:
        if not dry_run:
            try:
                new_ids = [cid for cid in lead["_campaign_ids"] if cid != campaign_id]
                update_row(lead["id"], "leads_crm", {
                    "Campaign": new_ids,
                })
                cleared += 1
            except Exception as e:
                print(f"    Failed {lead['email']}: {e}")
        else:
            cleared += 1

    return {"cleared": cleared, "dry_run": dry_run}
