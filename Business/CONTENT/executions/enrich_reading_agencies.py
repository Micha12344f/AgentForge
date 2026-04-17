"""
enrich_reading_agencies.py — Apollo enrichment for Reading, UK marketing agencies.

Enriches each domain via Apollo /organizations/enrich and writes results directly
to the SQLite network database (network.db).  Run repeatedly — it upserts, never
duplicates.

Usage:
    cd "Agentic Hedge Edge"
    python Business/CONTENT/executions/enrich_reading_agencies.py

Credits cost: 1 per agency per run (12 agencies = 12 credits from 100/month free
plan).  Already-enriched rows are re-upserted with fresh data; skip flag below
lets you avoid re-spending credits on previously successful rows.
"""

import json
import sys
from pathlib import Path

# Allow running from workspace root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from CONTENT.executions.apollo_api import ApolloAPI
from RESEARCH.resources.Network.network_db import NetworkDB

# ---------------------------------------------------------------------------
# Prospect list
# ---------------------------------------------------------------------------
PROSPECTS = [
    {"name": "Cyber-Duck",              "domain": "cyber-duck.co.uk"},
    {"name": "Jam",                     "domain": "wearejam.agency"},
    {"name": "Atomic Digital",          "domain": "atomicdigital.agency"},
    {"name": "Coconut Creatives",       "domain": "coconutcreatives.co.uk"},
    {"name": "Equinet Media",           "domain": "equinetmedia.co.uk"},
    {"name": "Big Reach",               "domain": "bigreach.co.uk"},
    {"name": "Intelligent Positioning", "domain": "intelligentpositioning.com"},
    {"name": "TBD Media Group",         "domain": "tbdmediagroup.com"},
    {"name": "Intergage",               "domain": "intergage.co.uk"},
    {"name": "Key Principles",          "domain": "keyprinciples.co.uk"},
    {"name": "Reflow",                  "domain": "reflow.co.uk"},
    {"name": "Ascensor",                "domain": "ascensor.co.uk"},
]

# Set True to skip agencies that already have enrichment data in the DB
SKIP_ALREADY_ENRICHED = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_priority(employees: int | None) -> str:
    if employees and 10 <= employees <= 100:
        return "HIGH"
    if employees and employees > 0:
        return "MEDIUM"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api = ApolloAPI()
    db  = NetworkDB()

    ok = 0
    skipped = 0
    failed = 0

    for prospect in PROSPECTS:
        name   = prospect["name"]
        domain = prospect["domain"]

        # Optional skip if already enriched
        if SKIP_ALREADY_ENRICHED:
            existing = db.query(
                "SELECT enriched_at FROM agencies WHERE domain = ? AND enriched_at IS NOT NULL",
                (domain,),
            )
            if existing:
                print(f"  SKIP  {name} (already enriched at {existing[0]['enriched_at']})")
                skipped += 1
                continue

        print(f"  ···   {name} ({domain}) ...", end=" ", flush=True)
        try:
            data = api.enrich_organization(domain)
            org  = data.get("organization") or data   # Apollo wraps under 'organization'

            employees = org.get("estimated_num_employees")
            keywords  = org.get("keywords") or []
            techs     = [t.get("name") for t in (org.get("technologies") or [])]

            db.upsert_agency(
                name        = name,
                domain      = domain,
                apollo_name = org.get("name"),
                employees   = employees,
                industry    = org.get("industry"),
                revenue     = org.get("annual_revenue"),
                founded     = org.get("founded_year"),
                linkedin    = org.get("linkedin_url"),
                city        = org.get("city"),
                country     = org.get("country"),
                keywords    = json.dumps(keywords[:5]),
                technologies= json.dumps(techs[:8]),
                priority    = _score_priority(employees),
                enriched_at = __import__("datetime").datetime.utcnow().isoformat(timespec="seconds"),
                enrichment_error = None,
            )
            print(f"OK  ({employees} employees, priority={_score_priority(employees)})")
            ok += 1

        except Exception as exc:
            print(f"FAILED — {exc}")
            db.upsert_agency(
                name             = name,
                domain           = domain,
                enrichment_error = str(exc)[:400],
                priority         = "UNKNOWN",
            )
            failed += 1

    print(f"\n── Enrichment complete: {ok} OK  |  {skipped} skipped  |  {failed} failed ──")
    db.summary()
    db.close()


if __name__ == "__main__":
    main()
