#!/usr/bin/env python3
"""
beta_waitlist_onboard.py — Sales Agent: Beta Tester Onboarding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Registers a new beta tester in the beta_waitlist Notion database.
Run this every time a beta license key is issued to an external user.

See directive: Business/GROWTH/directives/Sales/beta-tester-onboarding.md

Usage:
    python beta_waitlist_onboard.py --email "user@example.com" --name "Jane Doe" --source "Twitter Bio" --key "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
    python beta_waitlist_onboard.py --email "user@example.com" --source "Landing Page" --priority P1 --watchlist
    python beta_waitlist_onboard.py --email "user@example.com" --dry-run
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
    'twitter':      'Twitter Bio',
    'twitter bio':  'Twitter Bio',
    'twitter/bio':  'Twitter Bio',
    'landing page': 'Landing Page',
    'landing-page': 'Landing Page',
    'referral':     'Referral',
    'email drip':   'Email Drip',
    'email':        'Email Drip',
    'discord':      'Discord',
    'direct':       'Direct',
    'none':         'Direct',
}

VALID_PRIORITIES = {'P1', 'P2', 'P3'}


def _normalise_source(raw: str) -> str:
    return SOURCE_MAP.get(raw.lower().strip(), raw)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], '')


def _email_prefix(email: str) -> str:
    return email.split('@')[0]


def check_existing(email: str) -> dict | None:
    """Return the existing beta_waitlist row for this email, or None."""
    rows = query_db('beta_waitlist')
    for row in rows:
        if (row.get('Email') or '').lower().strip() == email.lower().strip():
            return row
    return None


def onboard(args) -> bool:
    """
    Create a beta_waitlist record for the given user.
    Returns True on success, False if skipped (duplicate).
    """
    email = args.email.strip().lower()
    source = _normalise_source(args.source or 'Twitter Bio')
    priority = (args.priority or 'P2').upper()
    if priority not in VALID_PRIORITIES:
        print(f'  ⚠ Invalid priority "{priority}", defaulting to P2')
        priority = 'P2'

    # Resolve name
    display = args.name or _email_prefix(email)
    first, last = _split_name(display)

    license_key = (args.key or '').strip()
    key_sent = bool(license_key)

    # Build tags
    tags = ['Beta']
    if key_sent:
        tags.append('Beta Key Sent')

    notes = (
        f'Beta tester registered via {source} on {TODAY}.'
        + (f' License key assigned: {license_key}.' if license_key else ' License key pending.')
    )

    row = {
        'Name':            first,
        'First Name':      first,
        'Last Name':       last,
        'Email':           email,
        'Source':          source,
        'Beta Key':        license_key,
        'Beta Key Sent':   key_sent,
        'Key Sent Date':   TODAY if key_sent else None,
        'Tags':            tags,
        'Priority':        priority,
        'Sales Watchlist': bool(args.watchlist),
        'Beta Activated':  False,
        'Beta Key Clicked': False,
        'Product Used':    False,
        'Lifecycle Owner': 'Marketing',
        'Notes':           notes,
    }

    print()
    print('=' * 62)
    print('  Beta Waitlist Onboarding')
    print('=' * 62)
    print(f'  Email   : {email}')
    print(f'  Name    : {first} {last}'.rstrip())
    print(f'  Source  : {source}')
    print(f'  Key     : {license_key or "(none — pending)"}')
    print(f'  Priority: {priority}')
    print(f'  Watchlist: {"Yes" if args.watchlist else "No"}')

    # ── Step 1: Deduplication ───────────────────────────────────────
    existing = check_existing(email)
    if existing:
        print()
        print(f'  ⚠ Already in beta_waitlist (Notion ID: {existing["_id"]})')
        print('  Skipping creation — no duplicate written.')
        return False

    if args.dry_run:
        print()
        print('  [DRY RUN] Row that would be written:')
        for k, v in row.items():
            if v not in (None, '', False, []):
                print(f'    {k}: {v}')
        print()
        return True

    # ── Step 2: Write to Notion ─────────────────────────────────────
    add_row('beta_waitlist', {k: v for k, v in row.items() if v is not None})

    log_task(
        'Sales',
        f'Beta waitlist: onboarded {email}',
        'Complete',
        priority,
        f'Source={source} | Key={license_key or "TBD"} | Watchlist={args.watchlist}',
    )

    print()
    print('  ✓ Added to beta_waitlist')
    if args.watchlist:
        print('  ✓ Flagged on Sales Watchlist — review within 24h')
    print()
    print('  Next steps:')
    print('  1. Run beta_lead_register.py (Marketing) to add to leads_crm')
    if not key_sent:
        print('  2. Assign a license key and re-run with --key XXXXX-...')
    print()
    return True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Register a beta tester in the beta_waitlist Notion database.',
    )
    p.add_argument('--email',     required=True,  help='Beta tester email address')
    p.add_argument('--name',      default=None,   help='Full name (optional)')
    p.add_argument('--source',    default='Twitter Bio',
                   help='Acquisition source (default: Twitter Bio)')
    p.add_argument('--key',       default=None,   help='License key (if already assigned)')
    p.add_argument('--priority',  default='P2',   choices=['P1', 'P2', 'P3'],
                   help='CRM priority (default: P2)')
    p.add_argument('--watchlist', action='store_true',
                   help='Flag for Sales Watchlist')
    p.add_argument('--dry-run',   action='store_true', dest='dry_run',
                   help='Print the row without writing to Notion')
    return p


if __name__ == '__main__':
    args = build_parser().parse_args()
    success = onboard(args)
    sys.exit(0 if success else 1)
