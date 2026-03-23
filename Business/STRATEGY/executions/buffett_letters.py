#!/usr/bin/env python3
"""
Buffett Letters Downloader & Wisdom Extractor — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Downloads all Warren Buffett shareholder letters (1977-2024) from
berkshirehathaway.com and extracts actionable business wisdom.

Actions:
  --action download   Download all shareholder letters as PDFs/HTML
  --action extract    Extract key lessons from downloaded letters
  --action wisdom     Get Buffett's wisdom on a specific business topic
  --action principles List Buffett's core investment/business principles

Usage:
  python buffett_letters.py --action download
  python buffett_letters.py --action wisdom --query "competitive moats"
  python buffett_letters.py --action principles
"""

import sys, os, json, argparse, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import log_task

AGENT = "Strategy"
AGENT_KEY = "legal"

RESOURCES_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / "resources"
LETTERS_DIR = RESOURCES_DIR / "buffett_letters"

# ──────────────────────────────────────────────
# Berkshire Hathaway shareholder letter URL map
# Older letters are HTML, newer ones are PDF
# ──────────────────────────────────────────────

BASE = "https://www.berkshirehathaway.com/letters"

# Year → (relative_path, format)
LETTER_URLS = {}

# 1977-1997: HTML format
for y in range(1977, 1998):
    LETTER_URLS[y] = (f"{BASE}/{y}.html", "html")

# 1998-2024: PDF format (with some naming quirks)
LETTER_URLS[1998] = (f"{BASE}/1998pdf.pdf", "pdf")
LETTER_URLS[1999] = (f"{BASE}/1999htm.html", "html")
LETTER_URLS[2000] = (f"{BASE}/2000pdf.pdf", "pdf")
LETTER_URLS[2001] = (f"{BASE}/2001pdf.pdf", "pdf")
LETTER_URLS[2002] = (f"{BASE}/2002pdf.pdf", "pdf")

for y in range(2003, 2025):
    suffix = "ltr" if y <= 2019 else ""
    LETTER_URLS[y] = (f"{BASE}/{y}{suffix}.pdf", "pdf")

# Fix known URL patterns
LETTER_URLS[2003] = (f"{BASE}/2003ltr.pdf", "pdf")
LETTER_URLS[2004] = (f"{BASE}/2004ltr.pdf", "pdf")
LETTER_URLS[2005] = (f"{BASE}/2005ltr.pdf", "pdf")
LETTER_URLS[2006] = (f"{BASE}/2006ltr.pdf", "pdf")
LETTER_URLS[2007] = (f"{BASE}/2007ltr.pdf", "pdf")
LETTER_URLS[2008] = (f"{BASE}/2008ltr.pdf", "pdf")
LETTER_URLS[2009] = (f"{BASE}/2009ltr.pdf", "pdf")
LETTER_URLS[2010] = (f"{BASE}/2010ltr.pdf", "pdf")
LETTER_URLS[2011] = (f"{BASE}/2011ltr.pdf", "pdf")
LETTER_URLS[2012] = (f"{BASE}/2012ltr.pdf", "pdf")
LETTER_URLS[2013] = (f"{BASE}/2013ltr.pdf", "pdf")
LETTER_URLS[2014] = (f"{BASE}/2014ltr.pdf", "pdf")
LETTER_URLS[2015] = (f"{BASE}/2015ltr.pdf", "pdf")
LETTER_URLS[2016] = (f"{BASE}/2016ltr.pdf", "pdf")
LETTER_URLS[2017] = (f"{BASE}/2017ltr.pdf", "pdf")
LETTER_URLS[2018] = (f"{BASE}/2018ltr.pdf", "pdf")
LETTER_URLS[2019] = (f"{BASE}/2019ltr.pdf", "pdf")
LETTER_URLS[2020] = (f"{BASE}/2020ltr.pdf", "pdf")
LETTER_URLS[2021] = (f"{BASE}/2021ltr.pdf", "pdf")
LETTER_URLS[2022] = (f"{BASE}/2022ltr.pdf", "pdf")
LETTER_URLS[2023] = (f"{BASE}/2023ltr.pdf", "pdf")
LETTER_URLS[2024] = (f"{BASE}/2024ltr.pdf", "pdf")


def _download_letter(year: int) -> tuple[bool, str]:
    """Download a single letter. Returns (success, filepath_or_error)."""
    if year not in LETTER_URLS:
        return False, f"No URL for {year}"

    url, fmt = LETTER_URLS[year]
    ext = "pdf" if fmt == "pdf" else "html"
    filepath = LETTERS_DIR / f"buffett_{year}.{ext}"

    if filepath.exists():
        return True, str(filepath)

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return True, str(filepath)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        return False, str(e)


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_download(args):
    """Download all Buffett shareholder letters."""
    LETTERS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"  📚 BUFFETT SHAREHOLDER LETTERS DOWNLOADER")
    print(f"{'=' * 60}")
    print(f"\n  Target: {len(LETTER_URLS)} letters (1977-2024)")
    print(f"  Save to: {LETTERS_DIR}\n")

    success = 0
    failed = []

    for year in sorted(LETTER_URLS.keys()):
        ok, result = _download_letter(year)
        if ok:
            symbol = "✅" if "already" not in result else "⏭️"
            existed = LETTERS_DIR / f"buffett_{year}.pdf"
            existed2 = LETTERS_DIR / f"buffett_{year}.html"
            if existed.exists() or existed2.exists():
                print(f"  ✅ {year}")
            else:
                print(f"  ✅ {year} — downloaded")
            success += 1
        else:
            print(f"  ❌ {year} — {result}")
            failed.append((year, result))
        time.sleep(0.3)  # Be polite to Berkshire's server

    print(f"\n{'─' * 60}")
    print(f"  Downloaded: {success}/{len(LETTER_URLS)}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for y, err in failed:
            print(f"    {y}: {err}")
    print(f"  Location: {LETTERS_DIR}")
    print(f"{'─' * 60}")

    log_task(AGENT, "Buffett letters download",
             "Complete", "P2",
             f"downloaded={success}, failed={len(failed)}")


def action_wisdom(args):
    """Get Buffett's wisdom on a specific business topic."""
    query = args.query
    if not query:
        print("  ❌ --query required (e.g. --query 'competitive moats')")
        return

    print(f"\n{'=' * 60}")
    print(f"  🦉 BUFFETT'S WISDOM: {query}")
    print(f"{'=' * 60}\n")

    result = chat(AGENT_KEY, [
        {"role": "system", "content": """You are a scholar who has studied every single Warren Buffett
shareholder letter (1977-2024), all Berkshire Hathaway annual meeting transcripts,
Charlie Munger's writings, and their public interviews.

When answering, always:
1. Quote specific Buffett/Munger passages with the year of the letter
2. Explain the principle behind the quote
3. Apply it specifically to Hedge Edge (UK prop-firm hedging SaaS)
4. Provide contrarian views where Buffett might disagree with conventional wisdom
5. Include at least one relevant Munger mental model

Structure as:
## The Buffett Principle
## Key Quotes (with years)
## Applied to Hedge Edge
## Munger's Perspective
## Contrarian Take
## Action Items for Hedge Edge"""},
        {"role": "user", "content": f"What would Buffett say about: {query}"},
    ], temperature=0.3, max_tokens=4096)

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in query)[:40].strip().replace(" ", "_")
    filepath = RESOURCES_DIR / f"buffett_wisdom_{safe}_{ts}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Buffett's Wisdom: {query}\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {filepath.name}")
    log_task(AGENT, f"Buffett wisdom: {query[:60]}", "Complete", "P2",
             f"file={filepath.name}")


def action_principles(args):
    """List Buffett's core investment and business principles."""
    print(f"\n{'=' * 60}")
    print(f"  📜 BUFFETT-MUNGER CORE PRINCIPLES")
    print(f"{'=' * 60}\n")

    result = chat(AGENT_KEY, [
        {"role": "system", "content": """You are the world's leading Buffett-Munger scholar.
Compile the definitive list of their business and investment principles,
specifically filtered for relevance to a SaaS startup."""},
        {"role": "user", "content": """Compile Buffett and Munger's core principles that are most
relevant to building Hedge Edge (UK prop-firm hedging SaaS).

For each principle:
1. **Principle name** — a memorable label
2. **Original quote** — with letter year
3. **Core idea** — 1-2 sentence explanation
4. **SaaS application** — how it applies to a subscription software business
5. **Hedge Edge specific** — concrete action for our business

Group into:
- **Business Quality Principles** (moats, management, economics)
- **Capital Allocation Principles** (when to spend, when to save)
- **Growth Principles** (when to grow fast, when to be patient)
- **Risk Management Principles** (especially relevant given we're in hedging!)
- **Culture & Team Principles** (building the right organisation)

Include at least 20 principles total. End with "The Anti-Buffett" — 3 conventional
Buffett principles that DON'T apply to early-stage startups and why."""},
    ], temperature=0.3, max_tokens=4096)

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = RESOURCES_DIR / f"buffett_principles_{ts}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Buffett-Munger Principles for Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {filepath.name}")
    log_task(AGENT, "Buffett-Munger principles compiled", "Complete", "P2",
             f"file={filepath.name}")


ACTIONS = {
    "download": action_download,
    "wisdom": action_wisdom,
    "principles": action_principles,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Buffett Letters — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--query", help="Topic for wisdom extraction")
    args = parser.parse_args()
    ACTIONS[args.action](args)
