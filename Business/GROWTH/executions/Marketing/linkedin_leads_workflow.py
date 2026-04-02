#!/usr/bin/env python3
"""
linkedin_leads_workflow.py

Run the LinkedIn connections -> email enrichment -> Notion dedupe/push workflow
for one or more accounts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _find_ws_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / "Business").is_dir() and (candidate / "shared").is_dir():
            return candidate
    raise RuntimeError("Cannot locate workspace root")


WS_ROOT = _find_ws_root()
sys.path.insert(0, str(WS_ROOT))

from shared.env_loader import load_env_for_source  # noqa: E402

load_env_for_source(__file__)

from shared.notion_client import batch_add_rows, query_db  # noqa: E402
from Business.GROWTH.executions.Marketing.linkedin_scraper import do_scrape  # noqa: E402


ACCOUNT_CONFIG = {
    "default": {"scraper_account": None, "label": "Ryan"},
    "ryan": {"scraper_account": None, "label": "Ryan"},
    "mahmud": {"scraper_account": "mahmud", "label": "Mahmud"},
}
DEFAULT_ACCOUNTS = ["ryan", "mahmud"]


def _normalise_accounts(raw_accounts: list[str] | None) -> list[str]:
    if not raw_accounts:
        return DEFAULT_ACCOUNTS.copy()

    accounts: list[str] = []
    seen: set[str] = set()
    for item in raw_accounts:
        name = (item or "").strip().lower()
        if not name:
            continue
        if name not in seen:
            accounts.append(name)
            seen.add(name)
    return accounts or DEFAULT_ACCOUNTS.copy()


def _account_meta(account_name: str) -> dict[str, Any]:
    config = ACCOUNT_CONFIG.get(account_name, {"scraper_account": account_name, "label": account_name.title()})
    return {
        "account": account_name,
        "scraper_account": config["scraper_account"],
        "label": config["label"],
    }


def _fetch_existing_emails() -> set[str]:
    existing = query_db(
        "leads_crm",
        filter={
            "property": "Email",
            "email": {"is_not_empty": True},
        },
    )
    return {
        (row.get("Email") or "").strip().lower()
        for row in existing
        if row.get("Email")
    }


def _build_notion_row(connection: dict[str, Any]) -> dict[str, str]:
    return {
        "Subject": connection["full_name"],
        "First Name": connection["first_name"],
        "Email": connection["email"],
        "Source": "LinkedIn",
    }


def run_workflow(
    *,
    accounts: list[str] | None = None,
    days: int = 7,
    headless: bool = True,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    resolved_accounts = _normalise_accounts(accounts)
    existing_emails = _fetch_existing_emails()

    summaries: list[dict[str, Any]] = []
    totals = {
        "scraped": 0,
        "with_email": 0,
        "no_email": 0,
        "duplicates": 0,
        "added": 0,
        "failed": 0,
    }

    for account_name in resolved_accounts:
        meta = _account_meta(account_name)
        label = meta["label"]
        scraper_account = meta["scraper_account"]

        print(f"[workflow] Starting account: {label}", flush=True)
        connections = do_scrape(headless=headless, days=days, account=scraper_account)

        rows_to_add: list[dict[str, str]] = []
        no_email = 0
        duplicates = 0
        with_email = 0

        for connection in connections:
            email = (connection.get("email") or "").strip().lower()
            if not email:
                no_email += 1
                continue

            with_email += 1
            if email in existing_emails:
                duplicates += 1
                continue

            existing_emails.add(email)
            rows_to_add.append(_build_notion_row(connection))

        if rows_to_add:
            batch = batch_add_rows("leads_crm", rows_to_add, label=f"{label} leads")
            added = len(batch["added"])
            failed = len(batch["errors"])
        else:
            batch = {"added": [], "errors": [], "stats": {}}
            added = 0
            failed = 0
            print(f"[workflow] No new leads to push for {label}.", flush=True)

        summary = {
            "account": account_name,
            "label": label,
            "scraper_account": scraper_account,
            "scraped": len(connections),
            "with_email": with_email,
            "no_email": no_email,
            "duplicates": duplicates,
            "to_add": len(rows_to_add),
            "added": added,
            "failed": failed,
        }
        summaries.append(summary)

        for key in totals:
            totals[key] += summary[key]

    finished_at = datetime.now(timezone.utc)
    result = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "elapsed_seconds": round((finished_at - started_at).total_seconds(), 1),
        "days": days,
        "headless": headless,
        "accounts": resolved_accounts,
        "per_account": summaries,
        "totals": totals,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LinkedIn lead workflow for one or more accounts")
    parser.add_argument(
        "--accounts",
        default=",".join(DEFAULT_ACCOUNTS),
        help="Comma-separated account list. Supported: ryan, mahmud",
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--headed", action="store_true", help="Run Chromium headed instead of headless")
    args = parser.parse_args()

    accounts = [part.strip() for part in args.accounts.split(",") if part.strip()]
    result = run_workflow(accounts=accounts, days=args.days, headless=not args.headed)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
