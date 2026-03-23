#!/usr/bin/env python3
"""
seed_beta_key_pool.py — Beta License Key Pool Seeder
=====================================================
Generates a pool of unique beta license keys and stores them in Supabase
so they can be assigned one-per-user when new beta signups arrive.

Actions:
  setup-table          → Print SQL to create beta_license_pool table in Supabase
  generate             → Generate N HE-XXXX keys locally, write to Supabase (fast)
  generate-playwright  → Complete N Creem test checkouts via headless browser,
                         then generate HE-XXXX keys linked to those checkout IDs
  status               → Show pool stats (total / assigned / available)
  list                 → Print keys in the pool

Usage:
    python seed_beta_key_pool.py --action setup-table
    python seed_beta_key_pool.py --action generate --count 100
    python seed_beta_key_pool.py --action generate-playwright --count 100
    python seed_beta_key_pool.py --action generate-playwright --count 10 --headed
    python seed_beta_key_pool.py --action status
    python seed_beta_key_pool.py --action list --limit 50

Notes:
    - HE-XXXX keys bypass the Creem API cross-check in the Railway backend.
      The 'validate_license_with_creem' function in license_api_production.py
      returns {"valid": True} immediately for any key starting with "HE-".
    - Keys are written to BOTH:
        1. beta_license_pool  — the assignment queue
        2. licenses           — looked up by the Railway validation endpoint
"""

import argparse
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta

def _find_ws_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(12):
        if os.path.isdir(os.path.join(d, "shared")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
sys.path.insert(0, _WS_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"))

import requests
from shared.supabase_client import get_supabase

# ── Config ─────────────────────────────────────────────────────────────────

CREEM_TEST_API_URL = os.getenv("CREEM_TEST_API_URL", "https://test-api.creem.io")
CREEM_TEST_API_KEY = os.getenv("CREEM_TEST_API_KEY", "")
PRODUCT_ID = os.getenv("CREEM_BETA_PRODUCT_ID", "prod_6Mkxf6mcZn3WyCsVMP7jJJ")

BETA_KEY_POOL_TABLE = "beta_license_pool"
LICENSES_TABLE = "licenses"

BETA_PLAN = "Hedge Edge Beta"
BETA_MAX_DEVICES = 3
BETA_DURATION_DAYS = 180

# ── SQL for table setup ────────────────────────────────────────────────────

SETUP_SQL = """\
-- ============================================================
-- Beta License Key Pool
-- Run in Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.beta_license_pool (
  id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  license_key         TEXT        NOT NULL UNIQUE,
  creem_checkout_id   TEXT        DEFAULT NULL,
  product_id          TEXT        DEFAULT NULL,
  assigned_to_email   TEXT        DEFAULT NULL,
  assigned_to_user_id UUID        DEFAULT NULL,
  assigned_at         TIMESTAMPTZ DEFAULT NULL,
  is_assigned         BOOLEAN     DEFAULT FALSE,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_beta_pool_unassigned
  ON public.beta_license_pool (is_assigned)
  WHERE is_assigned = FALSE;

CREATE INDEX IF NOT EXISTS idx_beta_pool_email
  ON public.beta_license_pool (assigned_to_email)
  WHERE assigned_to_email IS NOT NULL;

ALTER TABLE public.beta_license_pool ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'beta_license_pool'
      AND policyname = 'Service role full access to beta_license_pool'
  ) THEN
    EXECUTE 'CREATE POLICY "Service role full access to beta_license_pool"
      ON public.beta_license_pool FOR ALL USING (auth.role() = ''service_role'')';
  END IF;
END $$;
"""

# ── Key generation ─────────────────────────────────────────────────────────

def _generate_key() -> str:
    """Generate a unique HE-XXXX-XXXX-XXXX-XXXX beta license key."""
    raw = uuid.uuid4().hex.upper()
    return f"HE-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"


# ── Creem API helpers ──────────────────────────────────────────────────────

def _creem_headers() -> dict:
    return {"x-api-key": CREEM_TEST_API_KEY, "Content-Type": "application/json"}


def _create_checkout(seed_index: int) -> dict | None:
    """Create a Creem test checkout. Returns {id, checkout_url} or None."""
    if not CREEM_TEST_API_KEY:
        return None
    test_email = f"beta-seed-{seed_index:04d}@hedgedge-internal.test"
    r = requests.post(
        f"{CREEM_TEST_API_URL}/v1/checkouts",
        headers=_creem_headers(),
        json={
            "product_id": PRODUCT_ID,
            "success_url": "https://hedgedge.info/beta-success",
            "customer": {"email": test_email},
            "metadata": {"purpose": "beta_pool_seed", "index": str(seed_index)},
        },
        timeout=15,
    )
    if not r.ok:
        print(f"    ⚠ Checkout create failed ({r.status_code}): {r.text[:100]}")
        return None
    return r.json()


# ── Playwright checkout completion ─────────────────────────────────────────

def _complete_checkout_playwright(checkout_url: str, headless: bool = True) -> bool:
    """
    Complete a Creem test checkout via Playwright headless browser.
    Returns True if the page reached a success state, False otherwise.

    Test card: 4242 4242 4242 4242 | 12/30 | 123
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("    ✗ playwright not installed — run: pip install playwright && playwright install chromium")
        return False

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context()
        page = ctx.new_page()
        success = False
        try:
            page.goto(checkout_url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_load_state("networkidle", timeout=15_000)

            # ── fill card number ───────────────────────────────────────────
            _fill_field(page, [
                'input[placeholder*="1234"]',
                'input[placeholder*="4242"]',
                'input[name*="cardNumber"]',
                'input[name*="card-number"]',
                'input[id*="cardNumber"]',
                '[data-testid*="card-number"] input',
            ], "4242424242424242")

            # ── fill expiry ────────────────────────────────────────────────
            _fill_field(page, [
                'input[placeholder*="MM"]',
                'input[placeholder*="MM / YY"]',
                'input[name*="expiry"]',
                'input[name*="exp"]',
                'input[id*="expiry"]',
            ], "12/30")

            # ── fill CVV ───────────────────────────────────────────────────
            _fill_field(page, [
                'input[placeholder*="CVC"]',
                'input[placeholder*="CVV"]',
                'input[name*="cvc"]',
                'input[name*="cvv"]',
                'input[id*="cvc"]',
            ], "123")

            # ── fill cardholder name if present ────────────────────────────
            _fill_field(page, [
                'input[placeholder*="Name on card"]',
                'input[placeholder*="Full name"]',
                'input[name*="cardholderName"]',
                'input[name*="name"]',
            ], "Beta Tester", required=False)

            # ── submit ─────────────────────────────────────────────────────
            submitted = False
            for sel in [
                'button[type="submit"]',
                'button:has-text("Pay")',
                'button:has-text("Subscribe")',
                'button:has-text("Confirm")',
                'button:has-text("Complete")',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2_000):
                        btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if not submitted:
                print("    ⚠ No submit button found — checkout may have auto-completed")

            # ── wait for success signal ────────────────────────────────────
            try:
                page.wait_for_url("**/beta-success**", timeout=20_000)
                success = True
            except PWTimeout:
                # Check for success text on page as fallback
                try:
                    if page.locator(
                        ":has-text('success'), :has-text('Thank you'), :has-text('complete')"
                    ).first.is_visible(timeout=3_000):
                        success = True
                except Exception:
                    pass

        except Exception as e:
            print(f"    ⚠ Playwright error: {e}")
        finally:
            ctx.close()
            browser.close()

    return success


def _fill_field(page, selectors: list[str], value: str, required: bool = True) -> bool:
    """Try each selector in order; fill and return True on first match."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1_500):
                el.fill(value)
                return True
        except Exception:
            continue
    # Try frames
    for frame in page.frames:
        for sel in selectors:
            try:
                el = frame.locator(sel).first
                if el.is_visible(timeout=1_000):
                    el.fill(value)
                    return True
            except Exception:
                continue
    if required:
        print(f"    ⚠ Could not fill field (tried: {selectors[0]}, ...)")
    return False


# ── Supabase writes ────────────────────────────────────────────────────────

def _insert_to_pool(db, key: str, creem_checkout_id: str | None) -> bool:
    """
    Insert a key into beta_license_pool.
    Returns True if inserted, False if it already existed (skipped).
    """
    try:
        db.table(BETA_KEY_POOL_TABLE).insert({
            "license_key": key,
            "creem_checkout_id": creem_checkout_id,
            "product_id": PRODUCT_ID,
            "is_assigned": False,
        }).execute()
        return True
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg or "23505" in msg:
            return False
        print(f"  ✗ Pool insert error: {e}")
        return False


def _upsert_to_licenses(db, key: str, email: str | None = None) -> None:
    """
    Upsert key into the licenses table so the Railway backend can validate it.
    Sets plan='Hedge Edge Beta', is_active=True, expires_at=now+180d.
    Pool keys not yet assigned to a user use a placeholder email; it gets
    overwritten when the key is claimed via claim-beta.
    """
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=BETA_DURATION_DAYS)
    ).isoformat()
    db.table(LICENSES_TABLE).upsert(
        {
            "license_key": key,
            "email": email or "pool-unassigned@beta.hedgedge-internal",
            "plan": BETA_PLAN,
            "features": ["trade-copying", "hedge-detection", "multi-account"],
            "max_devices": BETA_MAX_DEVICES,
            "is_active": True,
            "expires_at": expires_at,
            "deactivated_at": None,
        },
        on_conflict="license_key",
    ).execute()


# ── Actions ─────────────────────────────────────────────────────────────────

def action_setup_table(_args):
    """Print the SQL needed to create beta_license_pool in Supabase."""
    print()
    print("Run this in your Supabase SQL Editor:")
    print("=" * 64)
    print(SETUP_SQL)
    print("=" * 64)


def action_status(_args):
    """Show current pool statistics."""
    db = get_supabase(use_service_role=True)
    try:
        total_r     = db.table(BETA_KEY_POOL_TABLE).select("id", count="exact").execute()
        avail_r     = db.table(BETA_KEY_POOL_TABLE).select("id", count="exact").eq("is_assigned", False).execute()
        assigned_r  = db.table(BETA_KEY_POOL_TABLE).select("id", count="exact").eq("is_assigned", True).execute()
    except Exception as e:
        print(f"✗ Could not query beta_license_pool: {e}")
        print("  Did you run --action setup-table and execute the SQL in Supabase?")
        sys.exit(1)

    total    = total_r.count    or 0
    avail    = avail_r.count    or 0
    assigned = assigned_r.count or 0

    print()
    print("Beta License Key Pool — Status")
    print("=" * 40)
    print(f"  Total keys       : {total}")
    print(f"  Available        : {avail}")
    print(f"  Assigned         : {assigned}")
    if total > 0:
        pct = assigned / total * 100
        print(f"  Usage            : {pct:.0f}%")
        if avail < 10:
            print("  ⚠ WARNING: pool is low — generate more keys soon")
    print()


def action_generate(args):
    """
    Generate N HE-XXXX-XXXX-XXXX-XXXX keys locally and write them to Supabase.
    This is the fast path — no browser or Creem API call needed.
    """
    count = args.count
    db = get_supabase(use_service_role=True)

    print(f"\nGenerating {count} local HE-XXXX keys → Supabase...")
    print("-" * 52)

    inserted = 0
    skipped  = 0

    for i in range(1, count + 1):
        key = _generate_key()
        ok = _insert_to_pool(db, key, creem_checkout_id=None)
        if ok:
            _upsert_to_licenses(db, key)
            inserted += 1
            if inserted % 10 == 0 or inserted == 1:
                print(f"  [{inserted:3d}/{count}] {key} ✓")
        else:
            skipped += 1

    print()
    print("=" * 52)
    print(f"  ✓ Keys inserted into beta_license_pool : {inserted}")
    print(f"  ✓ Keys inserted into licenses table    : {inserted}")
    if skipped:
        print(f"  ⚠ Skipped (already existed)            : {skipped}")
    print()
    print("Run --action status to confirm pool size.")
    print()
    print("IMPORTANT — Railway backend requires a 2-line patch to skip the")
    print("Creem cross-check for HE-* keys. See the note in this file's docstring.")


def action_generate_playwright(args):
    """
    Create N Creem test checkouts via the API, complete each via Playwright,
    then generate a custom HE-XXXX key linked to that checkout ID.

    This links each pool key to a real Creem checkout record (useful for
    tracking and when LKM is later enabled on the product).
    If checkout creation fails, falls back to a pure local key.
    """
    count   = args.count
    headless = not args.headed
    db = get_supabase(use_service_role=True)

    if not CREEM_TEST_API_KEY:
        print("✗ CREEM_TEST_API_KEY not set in .env — aborting")
        sys.exit(1)

    print(f"\nGenerating {count} keys via Playwright + Creem checkouts...")
    print(f"Product : {PRODUCT_ID}")
    print(f"Headless: {headless}")
    print("-" * 55)

    inserted          = 0
    checkout_linked   = 0
    checkout_fallback = 0

    for i in range(1, count + 1):
        print(f"\n[{i:3d}/{count}] Creating checkout...")
        checkout = _create_checkout(i)

        if not checkout:
            key           = _generate_key()
            checkout_id   = None
            checkout_fallback += 1
            print(f"       Fallback key (no checkout): {key}")
        else:
            checkout_id  = checkout.get("id", "")
            checkout_url = checkout.get("checkout_url", "")
            print(f"       Checkout : {checkout_id}")
            print(f"       Completing via browser...")
            completed = _complete_checkout_playwright(checkout_url, headless=headless)
            if completed:
                print("       ✓ Checkout completed")
                checkout_linked += 1
            else:
                print("       ⚠ Checkout completion uncertain — key still generated")
                checkout_fallback += 1
            key = _generate_key()
            print(f"       Key: {key}")

        ok = _insert_to_pool(db, key, creem_checkout_id=checkout_id)
        if ok:
            _upsert_to_licenses(db, key)
            inserted += 1

        time.sleep(1.2)  # Brief pause — avoids Creem rate limits

    print()
    print("=" * 55)
    print(f"  ✓ Keys inserted            : {inserted}")
    print(f"  ✓ Checkouts completed      : {checkout_linked}")
    print(f"  ⚠ Checkout fallbacks       : {checkout_fallback}")
    print()
    print("Run --action status to confirm pool size.")


def action_list(args):
    """Print keys in the pool."""
    db    = get_supabase(use_service_role=True)
    limit = args.limit
    rows  = (
        db.table(BETA_KEY_POOL_TABLE)
        .select("license_key, is_assigned, assigned_to_email, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    print(f"\nBeta License Key Pool — last {limit} rows")
    print(f"{'LICENSE KEY':44s}  {'STATUS':10s}  {'ASSIGNED TO':32s}  CREATED")
    print("-" * 105)
    for r in rows.data or []:
        status  = "ASSIGNED" if r["is_assigned"] else "available"
        email   = r["assigned_to_email"] or "-"
        created = (r.get("created_at") or "")[:10]
        print(f"{r['license_key']:44s}  {status:10s}  {email:32s}  {created}")
    print()


# ── CLI ──────────────────────────────────────────────────────────────────────

ACTIONS = {
    "setup-table":          action_setup_table,
    "status":               action_status,
    "generate":             action_generate,
    "generate-playwright":  action_generate_playwright,
    "list":                 action_list,
}


def main():
    p = argparse.ArgumentParser(
        description="Hedge Edge — Beta license key pool seeder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--action", choices=list(ACTIONS.keys()), default="status",
                   help="Action to run (default: status)")
    p.add_argument("--count",  type=int, default=100,
                   help="Number of keys to generate (default: 100)")
    p.add_argument("--headed", action="store_true",
                   help="Show browser window when using generate-playwright")
    p.add_argument("--limit",  type=int, default=50,
                   help="Max rows to display in --action list (default: 50)")
    args = p.parse_args()
    ACTIONS[args.action](args)


if __name__ == "__main__":
    main()
