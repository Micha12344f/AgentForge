#!/usr/bin/env python3
"""
beta_lead_register.py — Marketing Agent: Beta Lead Registration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Registers a new beta tester as a lead in the leads_crm Notion database.
Run this every time a beta license key is issued to an external user,
in parallel with beta_waitlist_onboard.py (Sales).

See directive: Business/GROWTH/directives/Marketing/beta-lead-registration.md

Usage:
    python beta_lead_register.py --email "user@example.com" --name "Jane Doe" --source "Twitter"
    python beta_lead_register.py --email "user@example.com" --source "Landing Page"
    python beta_lead_register.py --email "user@example.com" --dry-run
"""

import sys
import os
import argparse
from datetime import datetime, timezone

def _find_ws_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

_WS_ROOT = _find_ws_root()
sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, '.env'), override=True)

from shared.notion_client import add_row, query_db, log_task

TODAY = datetime.now(timezone.utc).strftime('%Y-%m-%d')

SOURCE_MAP = {
    'twitter':      'Twitter',
    'twitter bio':  'Twitter',
    'twitter/bio':  'Twitter',
    'landing page': 'Landing Page',
    'landing-page': 'Landing Page',
    'referral':     'Referral',
    'email drip':   'Email Drip',
    'email':        'Email Drip',
    'discord':      'Discord',
    'direct':       'Direct',
    'none':         'Direct',
}


def _normalise_source(raw: str) -> str:
    return SOURCE_MAP.get(raw.lower().strip(), raw)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], '')


def _email_prefix(email: str) -> str:
    return email.split('@')[0]


def check_existing(email: str) -> dict | None:
    """Return the existing leads_crm row for this email, or None."""
    rows = query_db('leads_crm')
    for row in rows:
        if (row.get('Email') or '').lower().strip() == email.lower().strip():
            return row
    return None


def register(args) -> bool:
    """
    Create a leads_crm record for the given beta tester.
    Returns True on success, False if skipped (duplicate).
    """
    email = args.email.strip().lower()
    source = _normalise_source(args.source or 'Twitter')

    display = args.name or _email_prefix(email)
    first, last = _split_name(display)

    row = {
        'Email':      email,
        'First Name': first,
        'Last Name':  last,
        'Source':     source,
        'Subject':    f'Beta Tester — {source}',
    }

    print()
    print('=' * 62)
    print('  Beta Lead Registration (leads_crm)')
    print('=' * 62)
    print(f'  Email  : {email}')
    print(f'  Name   : {first} {last}'.rstrip())
    print(f'  Source : {source}')

    # ── Step 1: Deduplication ───────────────────────────────────────
    existing = check_existing(email)
    if existing:
        print()
        print(f'  ⚠ Already in leads_crm (Notion ID: {existing["_id"]})')
        print('  Skipping creation — no duplicate written.')
        return False

    if args.dry_run:
        print()
        print('  [DRY RUN] Row that would be written:')
        for k, v in row.items():
            print(f'    {k}: {v}')
        print()
        return True

    # ── Step 2: Write to Notion ─────────────────────────────────────
    add_row('leads_crm', row)

    log_task(
        'Marketing',
        f'Beta lead registered: {email}',
        'Complete',
        'P2',
        f'Source={source} | Registered {TODAY}',
    )

    print()
    print('  ✓ Added to leads_crm')
    print()
    print('  Next steps:')
    print('  1. Enroll in Beta Activation email sequence via email_marketing engine')
    print('  2. Verify utm_source in Supabase user_attribution matches source above')
    print()
    return True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Register a beta tester as a lead in the leads_crm Notion database.',
    )
    p.add_argument('--email',   required=True, help='Beta tester email address')
    p.add_argument('--name',    default=None,  help='Full name (optional)')
    p.add_argument('--source',  default='Twitter',
                   help='Acquisition source (default: Twitter). '
                        'Options: Twitter, Landing Page, Referral, Email Drip, Discord, Direct')
    p.add_argument('--dry-run', action='store_true', dest='dry_run',
                   help='Print the row without writing to Notion')
    return p


if __name__ == '__main__':
    args = build_parser().parse_args()
    success = register(args)
    sys.exit(0 if success else 1)
