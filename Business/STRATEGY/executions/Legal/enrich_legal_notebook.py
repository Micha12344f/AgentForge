#!/usr/bin/env python3
"""
enrich_legal_notebook.py — Download UK legislation PDFs and enrich "Hedge Edge Legal" notebook
==============================================================================================
Downloads official UK Government legislation PDFs from legislation.gov.uk and
adds them to the existing "Hedge Edge Legal" NotebookLM notebook.

PDFs downloaded:
  1. Data Protection Act 2018 (ukpga_20180012)
  2. UK GDPR — Retained EU Regulation 2016/679
  3. Privacy & Electronic Communications Regulations 2003 / PECR (uksi_20032426)
  4. Financial Services and Markets Act 2000 / FSMA (ukpga_20000008)

Usage:
    python enrich_legal_notebook.py              # Download PDFs + add to notebook
    python enrich_legal_notebook.py --download   # Download only (no notebook update)
    python enrich_legal_notebook.py --add        # Add already-downloaded PDFs only
    python enrich_legal_notebook.py --list       # Show download status

Prerequisites:
    pip install notebooklm-py[browser] requests
    notebooklm login               # one-time Google auth (run from venv)
"""

import argparse
import asyncio
import sys
from pathlib import Path

import requests

# ── Path setup ───────────────────────────────────────────────────────
_SCRIPT_DIR  = Path(__file__).resolve().parent
_SKILL_DIR   = _SCRIPT_DIR.parent
_RESOURCES_DIR = _SKILL_DIR / "resources"
_DOWNLOADS_DIR = _RESOURCES_DIR / "downloads"

NOTEBOOK_NAME = "Hedge Edge Legal"

# ── UK Legislation PDFs ──────────────────────────────────────────────
# All sourced from legislation.gov.uk (Crown Copyright — Open Government Licence v3.0)
UK_LEGISLATION = [
    {
        "label": "Data Protection Act 2018",
        "url":   "https://www.legislation.gov.uk/ukpga/2018/12/pdfs/ukpga_20180012_en.pdf",
        "filename": "DPA_2018_ukpga_20180012_en.pdf",
        "notes": "Core UK data protection statute; supplements UK GDPR; ICO registration, lawful bases, rights",
    },
    {
        "label": "UK GDPR — Retained EU Regulation 2016/679",
        "url":   "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679",
        "filename": "UK_GDPR_eur_20160679_en.pdf",
        "notes": "Full text of the GDPR retained verbatim into UK law (European Union (Withdrawal) Act 2018)",
    },
    {
        "label": "Privacy & Electronic Communications Regulations 2003 (PECR)",
        "url":   "https://www.legislation.gov.uk/uksi/2003/2426/pdfs/uksi_20032426_en.pdf",
        "filename": "PECR_2003_uksi_20032426_en.pdf",
        "notes": "Governs email marketing, cookies, and electronic communications; enforced by ICO",
    },
    {
        "label": "Financial Services and Markets Act 2000 (FSMA)",
        "url":   "https://www.legislation.gov.uk/ukpga/2000/8/pdfs/ukpga_20000008_en.pdf",
        "filename": "FSMA_2000_ukpga_20000008_en.pdf",
        "notes": "Foundation of UK financial regulation; FCA/PRA powers; financial promotions; IB activities",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-GB,en;q=0.9",
}


# ── Download logic ───────────────────────────────────────────────────

def download_pdf(item: dict, force: bool = False) -> Path | None:
    """Download a single PDF; return its Path or None on failure."""
    dest = _DOWNLOADS_DIR / item["filename"]
    if dest.exists() and not force:
        size_mb = dest.stat().st_size / 1_048_576
        print(f"  ✅ Already downloaded: {item['label']} ({size_mb:.1f} MB)")
        return dest

    print(f"  ⬇  {item['label']}... ", end="", flush=True)
    try:
        resp = requests.get(item["url"], headers=HEADERS, timeout=120, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type and "octet-stream" not in content_type:
            print(f"⚠  Unexpected Content-Type: {content_type}")

        total = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                fh.write(chunk)
                total += len(chunk)

        size_mb = total / 1_048_576
        print(f"✅ ({size_mb:.1f} MB)")
        return dest

    except requests.HTTPError as exc:
        print(f"❌ HTTP {exc.response.status_code}: {exc}")
        return None
    except Exception as exc:
        print(f"❌ {exc}")
        return None


def download_all(force: bool = False) -> list[tuple[str, Path]]:
    """Download all legislation PDFs; return list of (label, path) for successful ones."""
    _DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📥 Downloading UK Legislation PDFs → {_DOWNLOADS_DIR}\n")
    results = []
    for item in UK_LEGISLATION:
        path = download_pdf(item, force=force)
        if path:
            results.append((item["label"], path))
    print(f"\n  {len(results)}/{len(UK_LEGISLATION)} PDFs ready\n")
    return results


def list_status():
    """Print download status of each PDF."""
    print(f"\n{'=' * 65}")
    print("  UK Legislation PDFs — Download Status")
    print(f"{'=' * 65}")
    for item in UK_LEGISLATION:
        dest = _DOWNLOADS_DIR / item["filename"]
        if dest.exists():
            size_mb = dest.stat().st_size / 1_048_576
            print(f"  ✅ {item['label']}")
            print(f"       {dest.name}  ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {item['label']}  [NOT DOWNLOADED]")
            print(f"       {item['url']}")
        print(f"       {item['notes']}")
        print()


# ── NotebookLM logic ─────────────────────────────────────────────────

async def add_to_notebook(pdfs: list[tuple[str, Path]]):
    """Add downloaded PDFs to the existing Hedge Edge Legal notebook."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("ERROR: notebooklm-py not installed. Run: pip install notebooklm-py[browser]")
        sys.exit(1)

    print(f"📓 Adding PDFs to '{NOTEBOOK_NAME}' notebook...\n")

    async with (await NotebookLMClient.from_storage()) as client:
        notebooks = await client.notebooks.list()
        notebook = next(
            (nb for nb in notebooks if NOTEBOOK_NAME.lower() in nb.title.lower()),
            None,
        )

        if not notebook:
            print(f"  ERROR: '{NOTEBOOK_NAME}' notebook not found.")
            print("  Run setup_legal_notebook.py first to create it.")
            sys.exit(1)

        print(f"  Notebook found: {notebook.id}")

        # Get existing source titles to avoid duplicates
        try:
            existing_sources = await client.sources.list(notebook.id)
            existing_titles = {s.title.lower() for s in existing_sources}
            print(f"  Existing sources: {len(existing_sources)}")
        except Exception:
            existing_titles = set()

        loaded = 0
        skipped = 0
        for label, path in pdfs:
            if label.lower() in existing_titles:
                print(f"    SKIP (already exists): {label}")
                skipped += 1
                continue

            size_mb = path.stat().st_size / 1_048_576
            print(f"    {label} ({size_mb:.1f} MB)...", end=" ", flush=True)
            try:
                await client.sources.add_file(notebook.id, file_path=str(path), wait=True)
                print("✅")
                loaded += 1
            except Exception as exc:
                print(f"❌ {exc}")

    print(f"\n  Done: {loaded} added, {skipped} skipped (already present)")
    print(f"  Total PDFs in notebook now enriched with full UK legislation text")


# ── Entry point ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Enrich Hedge Edge Legal NotebookLM with UK legislation PDFs"
    )
    parser.add_argument("--download", action="store_true", help="Download PDFs only, skip notebook update")
    parser.add_argument("--add",      action="store_true", help="Add already-downloaded PDFs to notebook (no re-download)")
    parser.add_argument("--list",     action="store_true", help="Show download status for each PDF")
    parser.add_argument("--force",    action="store_true", help="Re-download PDFs even if already present")
    args = parser.parse_args()

    if args.list:
        list_status()
        return

    if args.add:
        # Only add, use whatever is already downloaded
        pdfs = [(item["label"], _DOWNLOADS_DIR / item["filename"])
                for item in UK_LEGISLATION
                if (_DOWNLOADS_DIR / item["filename"]).exists()]
        if not pdfs:
            print("No downloaded PDFs found. Run without --add to download first.")
            sys.exit(1)
        asyncio.run(add_to_notebook(pdfs))
        return

    # Default + --download: download everything
    pdfs = download_all(force=args.force)

    if not args.download and pdfs:
        asyncio.run(add_to_notebook(pdfs))
    elif args.download:
        print("Download complete. Run with --add to push to NotebookLM.")


if __name__ == "__main__":
    main()
