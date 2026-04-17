"""CLI for writing durable research network intelligence into network.db.

Usage examples:
    python Business/RESEARCH/executions/network_capture.py init
    python Business/RESEARCH/executions/network_capture.py reset
    python Business/RESEARCH/executions/network_capture.py summary
    python Business/RESEARCH/executions/network_capture.py upsert-opportunity --name Meeseks --description "Campaign launch assurance"
    python Business/RESEARCH/executions/network_capture.py upsert-person --full-name "Mark Adams" --current-role CEO --current-company "Reading Tech Cluster"
    python Business/RESEARCH/executions/network_capture.py match --person-slug markinreading --opportunity-slug meeseks --match-score 84 --match-type introducer --rationale "Connector into Thames Valley tech network"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BUSINESS_DIR = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(BUSINESS_DIR))

from RESEARCH.resources.Network.network_db import NetworkDB  # noqa: E402


def _json_or_none(raw: str | None) -> str | None:
    if raw is None:
        return None
    json.loads(raw)
    return raw


def _csv_to_json_array(raw: str | None) -> str | None:
    if raw is None:
        return None
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return json.dumps(values) if values else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persist research network intelligence into network.db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize the database")
    init.add_argument("--migrate-legacy", action="store_true", help="Import legacy agency data from Agencies.db")
    reset = subparsers.add_parser("reset", help="Delete and recreate network.db")
    reset.add_argument("--migrate-legacy", action="store_true", help="Import legacy agency data after reset")
    subparsers.add_parser("summary", help="Print table counts")

    opportunity = subparsers.add_parser("upsert-opportunity", help="Create or update an opportunity record")
    opportunity.add_argument("--name", required=True)
    opportunity.add_argument("--slug")
    opportunity.add_argument("--description")
    opportunity.add_argument("--ideal-profile")
    opportunity.add_argument("--keywords-json")
    opportunity.add_argument("--keywords", help="Comma-separated keywords; easier than JSON in PowerShell")
    opportunity.add_argument("--status", default="active")

    person = subparsers.add_parser("upsert-person", help="Create or update a person record")
    person.add_argument("--full-name", required=True)
    person.add_argument("--slug")
    person.add_argument("--first-name")
    person.add_argument("--last-name")
    person.add_argument("--current-role")
    person.add_argument("--current-company")
    person.add_argument("--linkedin-url")
    person.add_argument("--email")
    person.add_argument("--location")
    person.add_argument("--profile-summary")
    person.add_argument("--relationship-type")
    person.add_argument("--opportunity-signal")
    person.add_argument("--source-confidence", default="medium")
    person.add_argument("--tags-json")
    person.add_argument("--tags", help="Comma-separated tags; easier than JSON in PowerShell")
    person.add_argument("--profile-data-json")
    person.add_argument("--public-handle", action="append", default=[])
    person.add_argument("--affiliation", action="append", default=[])
    person.add_argument("--source-type")
    person.add_argument("--source-url")
    person.add_argument("--source-title")
    person.add_argument("--source-snippet")

    match = subparsers.add_parser("match", help="Create or update a person-opportunity match")
    match.add_argument("--person-slug", required=True)
    match.add_argument("--opportunity-slug", required=True)
    match.add_argument("--match-score", required=True, type=int)
    match.add_argument("--match-type", required=True)
    match.add_argument("--rationale", required=True)
    match.add_argument("--next-step")
    match.add_argument("--status", default="open")

    return parser


def cmd_init(db: NetworkDB) -> None:
    db.summary()


def cmd_reset(args: argparse.Namespace) -> None:
    db = NetworkDB(migrate_legacy=False)
    db.reset()
    fresh_db = NetworkDB(migrate_legacy=args.migrate_legacy)
    try:
        fresh_db.summary()
    finally:
        fresh_db.close()


def cmd_summary(db: NetworkDB) -> None:
    db.summary()


def cmd_upsert_opportunity(db: NetworkDB, args: argparse.Namespace) -> None:
    keywords_json = _json_or_none(args.keywords_json) if args.keywords_json else _csv_to_json_array(args.keywords)
    opportunity_id = db.upsert_opportunity(
        name=args.name,
        slug=args.slug,
        description=args.description,
        ideal_profile=args.ideal_profile,
        keywords_json=keywords_json,
        status=args.status,
    )
    print(json.dumps({"opportunity_id": opportunity_id, "slug": args.slug or args.name.lower().replace(" ", "-")}, indent=2))


def cmd_upsert_person(db: NetworkDB, args: argparse.Namespace) -> None:
    tags_json = _json_or_none(args.tags_json) if args.tags_json else _csv_to_json_array(args.tags)
    profile_data_json = _json_or_none(args.profile_data_json) if args.profile_data_json else None
    if profile_data_json is None and (args.public_handle or args.affiliation):
        profile_data_json = json.dumps(
            {
                "public_handles": args.public_handle,
                "other_affiliations": args.affiliation,
            }
        )

    person_id = db.upsert_person(
        full_name=args.full_name,
        slug=args.slug,
        first_name=args.first_name,
        last_name=args.last_name,
        current_role=args.current_role,
        current_company=args.current_company,
        linkedin_url=args.linkedin_url,
        email=args.email,
        location=args.location,
        profile_summary=args.profile_summary,
        relationship_type=args.relationship_type,
        opportunity_signal=args.opportunity_signal,
        source_confidence=args.source_confidence,
        tags_json=tags_json,
        profile_data_json=profile_data_json,
    )

    if args.source_type:
        db.add_person_source(
            person_id=person_id,
            source_type=args.source_type,
            source_url=args.source_url,
            source_title=args.source_title,
            source_snippet=args.source_snippet,
        )

    person_rows = db.query("SELECT * FROM people WHERE id = ?", (person_id,))
    person = person_rows[0] if person_rows else None
    print(json.dumps({"person_id": person_id, "person": person}, indent=2))


def cmd_match(db: NetworkDB, args: argparse.Namespace) -> None:
    person = db.get_person(args.person_slug)
    if not person:
        raise SystemExit(f"Unknown person slug: {args.person_slug}")
    opportunities = db.query("SELECT * FROM opportunities WHERE slug = ?", (args.opportunity_slug,))
    if not opportunities:
        raise SystemExit(f"Unknown opportunity slug: {args.opportunity_slug}")
    opportunity = opportunities[0]
    match_id = db.upsert_person_opportunity_match(
        person_id=person["id"],
        opportunity_id=opportunity["id"],
        match_score=args.match_score,
        match_type=args.match_type,
        rationale=args.rationale,
        next_step=args.next_step,
        status=args.status,
    )
    print(json.dumps({"match_id": match_id, "person_slug": args.person_slug, "opportunity_slug": args.opportunity_slug}, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "reset":
        cmd_reset(args)
        return 0

    migrate_legacy = bool(getattr(args, "migrate_legacy", False))
    db = NetworkDB(migrate_legacy=migrate_legacy)
    try:
        if args.command == "init":
            cmd_init(db)
        elif args.command == "summary":
            cmd_summary(db)
        elif args.command == "upsert-opportunity":
            cmd_upsert_opportunity(db, args)
        elif args.command == "upsert-person":
            cmd_upsert_person(db, args)
        elif args.command == "match":
            cmd_match(db, args)
        else:
            parser.error(f"Unsupported command: {args.command}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())