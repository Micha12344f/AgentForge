#!/usr/bin/env python3
"""
linkedin_scraper.py — LinkedIn Connections Scraper

Scrapes your LinkedIn connections added in the last N days (default: 7).
Uses Playwright with persistent session storage — no repeated logins.

WORKFLOW
--------
Step 1 — Login (run once, opens headed browser):
    python linkedin_scraper.py --login

Step 2 — Scrape (uses saved session):
    python linkedin_scraper.py --scrape
    python linkedin_scraper.py --scrape --days 7

Auto mode (login if no session, then scrape):
    python linkedin_scraper.py

VPS / headless (after session is already saved):
    python linkedin_scraper.py --scrape --headless

OUTPUT
------
Writes: Business/GROWTH/executions/Marketing/linkedin_connections_YYYY-MM-DD.json
Each record: { name, occupation, company, profile_url, connected_on_text, connected_date, scraped_at }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _find_ws_root() -> Path:
    d = Path(__file__).resolve().parent
    for _ in range(10):
        if (d / "shared").is_dir() and (d / "Business").is_dir():
            return d
        d = d.parent
    raise RuntimeError("Cannot locate workspace root")


WS_ROOT = _find_ws_root()
sys.path.insert(0, str(WS_ROOT))

from shared.env_loader import load_env_for_source  # noqa: E402

load_env_for_source(__file__)

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = WS_ROOT / "Business" / "GROWTH" / "executions" / "Marketing"
CONNECTIONS_URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"

# ---------------------------------------------------------------------------
# Multi-account support
# ---------------------------------------------------------------------------

def _account_session_file(account: str | None = None) -> Path:
    """Return session file path for a given account (None = default)."""
    suffix = f"_{account}" if account else ""
    return OUTPUT_DIR / f".linkedin_session{suffix}.json"

def _account_credentials(account: str | None = None) -> tuple[str, str]:
    """Return (email, password) for the given account."""
    if account:
        prefix = account.upper() + "_"
    else:
        prefix = ""
    email = os.getenv(f"{prefix}LINKEDIN_EMAIL", "")
    password = os.getenv(f"{prefix}LINKEDIN_PASSWORD", "")
    return email, password

# Chrome user-agent to pass LinkedIn's basic bot detection
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# Playwright launch args — suppress automation flag
LAUNCH_ARGS = ["--disable-blink-features=AutomationControlled"]

# Script injected into every page to remove navigator.webdriver fingerprint
STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
"""


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def session_exists(account: str | None = None) -> bool:
    sf = _account_session_file(account)
    return sf.exists() and sf.stat().st_size > 200


def save_session(context, account: str | None = None) -> None:
    sf = _account_session_file(account)
    state = context.storage_state()
    sf.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"[session] Saved → {sf.name}")


def load_session(account: str | None = None) -> dict:
    sf = _account_session_file(account)
    return json.loads(sf.read_text(encoding="utf-8"))


def _new_context(browser, storage_state: dict | None = None):
    kwargs = dict(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
    )
    if storage_state:
        kwargs["storage_state"] = storage_state
    return browser.new_context(**kwargs)


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------


def parse_connection_date(text: str) -> datetime | None:
    """
    Parse LinkedIn's connection date text into UTC datetime.

    Handles:
      "Connected on March 29, 2026", "Connected on Mar 15, 2025",
      "Connected today", "Connected 1 day ago", "Connected 3 days ago",
      "Connected 2 hours ago", "Connected 1 week ago"
    """
    if not text:
        return None

    now = datetime.now(timezone.utc)
    # Strip "Connected on" / "Connected" prefix
    t = re.sub(r"^connected\s+on\s+", "", text.strip(), flags=re.IGNORECASE)
    t = re.sub(r"^connected\s+", "", t, flags=re.IGNORECASE)
    t = t.strip().lower()

    if "today" in t or "just now" in t:
        return now
    if "yesterday" in t:
        return now - timedelta(days=1)

    m = re.search(r"(\d+)\s*hour", t)
    if m:
        return now - timedelta(hours=int(m.group(1)))

    m = re.search(r"(\d+)\s*day", t)
    if m:
        return now - timedelta(days=int(m.group(1)))

    m = re.search(r"(\d+)\s*week", t)
    if m:
        return now - timedelta(weeks=int(m.group(1)))

    m = re.search(r"(\d+)\s*month", t)
    if m:
        return now - timedelta(days=int(m.group(1)) * 30)

    # Absolute dates: "march 29, 2026" or "mar 15" or "march 15, 2025"
    month_names = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12,
    }
    m = re.search(r"(\w+)\s+(\d{1,2})(?:,\s*(\d{4}))?", t)
    if m:
        month_str = m.group(1)
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else now.year
        month_num = month_names.get(month_str)
        if month_num:
            try:
                return datetime(year, month_num, day, tzinfo=timezone.utc)
            except ValueError:
                pass

    return None


# ---------------------------------------------------------------------------
# JS extraction snippet — injected into the page to pull card data
# ---------------------------------------------------------------------------

EXTRACT_JS = """
() => {
    const results = [];
    const links = [...document.querySelectorAll('a[href*=\\'/in/\\']')];
    for (const a of links) {
        const raw = (a.href || '');
        const href = raw.split('?')[0].replace(/\\/$/, '');
        if (!href.includes('/in/')) continue;

        let name = '';
        let occupation = '';
        let dateText = '';

        // Walk up up to 10 ancestors to find the card container
        let node = a;
        for (let i = 0; i < 10; i++) {
            node = node.parentElement;
            if (!node) break;

            // Name: from img alt (profile pics have person name in alt)
            if (!name) {
                const img = node.querySelector('img[alt]');
                if (img) {
                    const alt = (img.getAttribute('alt') || '').trim();
                    if (alt && alt.length > 1 && !/^(LinkedIn|logo)/i.test(alt)) {
                        name = alt;
                    }
                }
            }
            // Name fallback: svg aria-label "X's profile picture"
            if (!name) {
                const svg = node.querySelector('svg[aria-label*="profile picture"]');
                if (svg) {
                    name = (svg.getAttribute('aria-label') || '');
                }
            }
            // Strip "NAME's profile picture" / "NAME profile picture" suffixes
            if (name) {
                name = name.replace(/['\u2018\u2019'\u02bc]s? profile picture.*/i, '').trim();
                name = name.replace(/ profile picture.*/i, '').trim();
            }

            // Date: look for "Connected on ..." text
            if (!dateText) {
                const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
                let n;
                while ((n = walker.nextNode())) {
                    const t = n.textContent.trim();
                    if (/connected/i.test(t) && t.length < 80) {
                        dateText = t;
                        break;
                    }
                }
            }

            // Occupation: spans/p with meaningful text (not name, buttons, date)
            if (!occupation && name && dateText) {
                const els = [...node.querySelectorAll('span, p')];
                for (const el of els) {
                    const t = (el.innerText || '').trim();
                    if (!t || t.length < 3 || t.length > 150) continue;
                    // Skip if it IS the name (case-insensitive, partial match)
                    if (t.toLowerCase() === name.toLowerCase()) continue;
                    if (t.toLowerCase().includes(name.toLowerCase())) continue;
                    if (/message|connect|follow|withdraw|ignore|pending|connected/i.test(t)) continue;
                    if (/^[0-9]+$/.test(t)) continue;
                    occupation = t;
                    break;
                }
            }

            if (name && dateText) break;
        }

        if (href && name) {
            results.push({ href, name, occupation, dateText });
        }
    }

    // Deduplicate by href
    const seen = new Set();
    return results.filter(r => {
        if (seen.has(r.href)) return false;
        seen.add(r.href);
        return true;
    });
}
"""


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def scrape_connections(page, days: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    connections: list[dict] = []
    seen_urls: set[str] = set()

    print(f"[scrape] Navigating to connections page…")
    try:
        page.goto(CONNECTIONS_URL, wait_until="domcontentloaded", timeout=30_000)
    except PlaywrightTimeoutError:
        page.goto(CONNECTIONS_URL, wait_until="commit", timeout=30_000)

    page.wait_for_timeout(7_000)

    if "login" in page.url or "checkpoint" in page.url or "authwall" in page.url:
        raise RuntimeError(
            "Session expired or not logged in — re-run with --login first."
        )

    # Wait for any /in/ profile link to appear (means cards have rendered)
    try:
        page.wait_for_selector("a[href*='/in/']", timeout=15_000)
    except PlaywrightTimeoutError:
        raise RuntimeError(
            "No profile links appeared on the connections page. "
            "Session may be invalid — re-run with --login."
        )

    print(f"[scrape] Page loaded. Collecting connections from the last {days} day(s)…")

    consecutive_old = 0
    scroll_round = 0
    max_scrolls = 80

    while scroll_round < max_scrolls:
        raw_cards = page.evaluate(EXTRACT_JS)
        new_this_pass = 0
        stop_early = False

        for card in raw_cards:
            profile_url = card.get("href", "").rstrip("/")
            if not profile_url or profile_url in seen_urls:
                continue

            name = card.get("name") or "Unknown"
            occupation_raw = card.get("occupation") or ""
            date_text = card.get("dateText") or ""

            # Post-clean: if occupation == name, it's a LinkedIn display glitch
            if occupation_raw.strip().lower() == name.strip().lower():
                occupation_raw = ""

            # Extract just the "Connected on ..." line if mixed with other text
            date_match = re.search(r"connected[^\n]*", date_text, re.IGNORECASE)
            clean_date_text = date_match.group(0).strip() if date_match else date_text

            # Split occupation into title + company if " at " present
            company = ""
            occupation = occupation_raw
            if " at " in occupation_raw:
                parts = occupation_raw.split(" at ", 1)
                occupation = parts[0].strip()
                company = parts[1].strip()

            conn_date = parse_connection_date(clean_date_text)

            # Stop if this card is older than our window
            if conn_date and conn_date < cutoff:
                consecutive_old += 1
                if consecutive_old >= 5:
                    stop_early = True
                    break
                continue
            else:
                consecutive_old = 0

            seen_urls.add(profile_url)
            connections.append(
                {
                    "name": name,
                    "occupation": occupation,
                    "company": company,
                    "profile_url": profile_url,
                    "connected_on_text": clean_date_text,
                    "connected_date": conn_date.isoformat() if conn_date else None,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            new_this_pass += 1

        print(
            f"[scrape] Scroll {scroll_round + 1:>2}: "
            f"{len(connections):>4} collected | {new_this_pass} new | "
            f"{consecutive_old} consecutive-old"
        )

        if stop_early:
            print("[scrape] Reached connections older than cutoff — done.")
            break

        if new_this_pass == 0:
            empty_scrolls = getattr(scrape_connections, '_empty', 0) + 1
            scrape_connections._empty = empty_scrolls
            if empty_scrolls >= 8:
                print("[scrape] No new connections after 8 empty scrolls — end of list.")
                break
        else:
            scrape_connections._empty = 0

        # Scroll down — try the lazy-column container first, then window
        page.evaluate("""
            () => {
                const col = document.querySelector('[data-testid="lazy-column"]')
                          || document.querySelector('[data-component-type="LazyColumn"]');
                if (col) {
                    col.scrollTop += 4000;
                }
                window.scrollTo(0, document.body.scrollHeight);
            }
        """)
        page.wait_for_timeout(2_000)

        # Click "Load more" / "Show more results" button if present
        load_more = page.query_selector("button:has-text('Load more'), button:has-text('Show more')")
        if load_more:
            try:
                load_more.scroll_into_view_if_needed()
                load_more.click()
                page.wait_for_timeout(4_000)
            except Exception:
                pass

        page.wait_for_timeout(2_000)
        scroll_round += 1

    return connections


# ---------------------------------------------------------------------------
# Email enrichment — visit each profile and click "Contact info"
# ---------------------------------------------------------------------------


def fetch_email_from_profile(page, profile_url: str) -> str:
    """
    Visit a LinkedIn profile page, open the Contact Info overlay,
    and return the email address (or "" if not exposed).
    """
    try:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_timeout(2_500)

        # Click the "Contact info" link — LinkedIn renders it as an <a> with
        # href="/in/SLUG/overlay/contact-info/"
        contact_link = page.query_selector("a[href*='overlay/contact-info']")
        if not contact_link:
            # Fallback: find by visible text
            contact_link = page.query_selector("a:has-text('Contact info')")
        if not contact_link:
            return ""

        contact_link.click()
        page.wait_for_timeout(2_000)

        # Email is inside the modal as a mailto: link
        email_el = page.query_selector("a[href^='mailto:']")
        if email_el:
            href = email_el.get_attribute("href") or ""
            email = href.replace("mailto:", "").strip()
            # Close the modal before returning
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception:
                pass
            return email

        # Close modal even if no email found
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass
        return ""

    except Exception as exc:
        print(f"[enrich] Error fetching {profile_url}: {exc}")
        return ""


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def do_login(headless: bool = False, account: str | None = None) -> None:
    """Open browser, log in, save session state."""
    email, password = _account_credentials(account)
    label = account or "default"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=LAUNCH_ARGS)
        context = _new_context(browser)
        page = context.new_page()
        page.add_init_script(STEALTH_SCRIPT)

        print(f"[login] Opening LinkedIn login page… (account: {label})")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2_000)

        if email and password:
            print(f"[login] Auto-filling credentials for: {email}")

            # Type slowly to look more human
            page.click("#username")
            page.wait_for_timeout(400)
            page.type("#username", email, delay=60)

            page.click("#password")
            page.wait_for_timeout(300)
            page.type("#password", password, delay=50)

            page.wait_for_timeout(800)
            page.click("button[type='submit']")
            page.wait_for_timeout(6_000)

            current = page.url
            print(f"[login] After submit, URL: {current}")

            if "checkpoint" in current or "challenge" in current or "verification" in current:
                print("\n[login] ⚠  Security check detected.")
                print("[login]    Complete the verification in the browser, then press Enter here.")
                if headless:
                    browser.close()
                    raise RuntimeError(
                        "Cannot complete 2FA/verification in headless mode. "
                        "Run without --headless first to save a valid session."
                    )
                input("[login] Press Enter when verification is complete → ")
            elif "feed" in current or current.rstrip("/") == "https://www.linkedin.com":
                print("[login] ✓ Login successful!")
            else:
                print(f"[login] Unexpected URL: {current}")
                if not headless:
                    input("[login] Complete login manually, then press Enter → ")
        else:
            if headless:
                browser.close()
                raise RuntimeError(
                    "LINKEDIN_EMAIL / LINKEDIN_PASSWORD not set in .env. "
                    "Cannot auto-login in headless mode."
                )
            print("[login] No credentials found in .env.")
            print("[login] Please log in manually in the browser window.")
            input("[login] Press Enter when you are on the LinkedIn feed → ")

        # Navigate to feed to confirm logged in
        if "feed" not in page.url:
            try:
                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
                page.wait_for_timeout(2_000)
            except Exception:
                # LinkedIn may already be navigating to feed — that's fine
                page.wait_for_timeout(2_000)

        save_session(context, account=account)
        browser.close()
        print(f"[login] Session saved ({label}). Run --scrape to collect connections.")


# ---------------------------------------------------------------------------
# Scrape (uses saved session)
# ---------------------------------------------------------------------------


def do_scrape(headless: bool = False, days: int = 7, account: str | None = None) -> list[dict]:
    label = account or "default"
    if not session_exists(account):
        raise RuntimeError(f"No saved session found for '{label}'. Run --login --account {label} first.")

    storage = load_session(account)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=LAUNCH_ARGS)
        context = _new_context(browser, storage_state=storage)
        page = context.new_page()
        page.add_init_script(STEALTH_SCRIPT)

        try:
            raw = scrape_connections(page, days=days)

            # Enrich: visit each profile to fetch email via Contact info overlay
            print(f"\n[enrich] Fetching emails for {len(raw)} connection(s)…")
            connections = []
            for idx, c in enumerate(raw, 1):
                email = fetch_email_from_profile(page, c["profile_url"])
                first_name = c["name"].split()[0] if c["name"] else c["name"]
                connections.append({
                    "first_name": first_name,
                    "full_name": c["name"],
                    "email": email,
                    "profile_url": c["profile_url"],
                    "connected_date": c["connected_date"],
                    "connected_on_text": c["connected_on_text"],
                    "occupation": c["occupation"],
                    "company": c["company"],
                    "scraped_at": c["scraped_at"],
                })
                status = email if email else "(no email)"
                print(f"  [{idx:>2}/{len(raw)}] {first_name:<20} {status}")
                # Small delay between profile visits — be polite
                page.wait_for_timeout(1_500)

        finally:
            # Always refresh session after use
            save_session(context, account=account)
            browser.close()

    # Persist output
    date_str = datetime.now().strftime("%Y-%m-%d")
    acct_tag = f"_{account}" if account else ""
    output_file = OUTPUT_DIR / f"linkedin_connections{acct_tag}_{date_str}.json"
    output_file.write_text(
        json.dumps(connections, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with_email = [c for c in connections if c["email"]]
    print(f"\n{'='*60}")
    print(f"Scraped {len(connections)} connection(s) | {len(with_email)} with email.")
    print(f"Output → {output_file.name}")
    print("=" * 60)

    for c in connections[:15]:
        print(f"  • {c['first_name']:<20}  {c['email'] or '—'}")
    if len(connections) > 15:
        print(f"  … and {len(connections) - 15} more")

    return connections


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LinkedIn Connections Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Log in and save session (opens headed browser).",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape connections using saved session.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        metavar="N",
        help="Collect connections added in the last N days (default: 7).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (for VPS).",
    )
    parser.add_argument(
        "--account",
        type=str,
        default=None,
        metavar="NAME",
        help="Account name (reads NAME_LINKEDIN_EMAIL / NAME_LINKEDIN_PASSWORD from .env, "
             "and stores a separate session file). Default uses LINKEDIN_EMAIL.",
    )
    args = parser.parse_args()

    if args.login:
        do_login(headless=args.headless, account=args.account)
    elif args.scrape:
        do_scrape(headless=args.headless, days=args.days, account=args.account)
    else:
        # Auto-mode: login if needed, then scrape
        if not session_exists(args.account):
            print("[auto] No session found — starting login flow first.")
            do_login(headless=args.headless, account=args.account)
        do_scrape(headless=args.headless, days=args.days, account=args.account)


if __name__ == "__main__":
    main()
