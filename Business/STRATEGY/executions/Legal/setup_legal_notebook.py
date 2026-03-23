#!/usr/bin/env python3
"""
setup_legal_notebook.py — Create "Hedge Edge Legal" NotebookLM notebook
========================================================================
Loads all legal/compliance resources into a dedicated NotebookLM notebook
for RAG-powered legal Q&A.

Sources loaded:
  ── Summary/template documents ──
  - UK GDPR Summary
  - FCA Financial Promotions Guide
  - Data Processing Register (ROPA)
  - Privacy Policy Template
  - Terms of Service Template
  - Risk Disclaimers
  - IB Agreement Checklist
  - DSAR Process
  - Prop Firm Regulatory Landscape
  - Vantage IB Agreement (PDF)
  - BlackBull Partners T&C (PDF)
  - Business Context
  ── Full UK legislation PDFs (auto-downloaded from legislation.gov.uk / EUR-Lex) ──
  - Data Protection Act 2018
  - UK GDPR — Retained EU Regulation 2016/679
  - Privacy & Electronic Communications Regulations 2003 (PECR)
  - Financial Services and Markets Act 2000 (FSMA)

Usage:
    python setup_legal_notebook.py                # Create notebook and load sources
    python setup_legal_notebook.py --list         # List all sources and check they exist
    python setup_legal_notebook.py --test "Do we need ICO registration?"

Prerequisites:
    pip install notebooklm-py[browser]
    notebooklm login               # one-time Google auth
"""

import asyncio
import os
import sys
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_RESOURCES_DIR = _SKILL_DIR / "resources"
# execution/ -> legal-compliance/ -> skills/ -> .agents/ -> STRATEGY/ -> agents/ -> IDE 1/
_IDE1_ROOT = _SKILL_DIR.parents[4]  # IDE 1 root
_ORCHESTRATOR_ROOT = _IDE1_ROOT.parent.parent.parent
sys.path.insert(0, str(_ORCHESTRATOR_ROOT))

NOTEBOOK_NAME = "Hedge Edge Legal"

# ── Sources ──────────────────────────────────────────────────────────

SOURCES = [
    # ── Summary / template documents ─────────────────────────────────
    ("UK GDPR Summary", _RESOURCES_DIR / "uk-gdpr-summary.md", "text"),
    ("FCA Financial Promotions", _RESOURCES_DIR / "fca-financial-promotions.md", "text"),
    ("Data Processing Register", _RESOURCES_DIR / "data-processing-register.md", "text"),
    ("Privacy Policy Template", _RESOURCES_DIR / "privacy-policy-template.md", "text"),
    ("Terms of Service Template", _RESOURCES_DIR / "terms-of-service-template.md", "text"),
    ("Risk Disclaimers", _RESOURCES_DIR / "risk-disclaimers.md", "text"),
    ("IB Agreement Checklist", _RESOURCES_DIR / "ib-agreement-checklist.md", "text"),
    ("DSAR Process", _RESOURCES_DIR / "dsar-process.md", "text"),
    ("Prop Firm Regulatory Landscape", _RESOURCES_DIR / "prop-firm-regulatory-landscape.md", "text"),
    (
        "Vantage IB Agreement",
        _IDE1_ROOT / "Context" / "IB agreement" / "Vantage_IB_agreement.pdf",
        "file",
    ),
    (
        "BlackBull Partners T&C",
        _IDE1_ROOT / "Context" / "IB agreement" / "Blackbull_Partners-Terms-and-Conditions-29-March-2024.pdf",
        "file",
    ),
    (
        "Business Context",
        _IDE1_ROOT / "Context" / "Other" / "hedge-edge-business-context.md",
        "text",
    ),
    # ── Full UK legislation PDFs (downloaded via enrich_legal_notebook.py) ──
    (
        "Data Protection Act 2018",
        _RESOURCES_DIR / "downloads" / "DPA_2018_ukpga_20180012_en.pdf",
        "file",
    ),
    (
        "UK GDPR — Retained EU Regulation 2016/679",
        _RESOURCES_DIR / "downloads" / "UK_GDPR_eur_20160679_en.pdf",
        "file",
    ),
    (
        "Privacy & Electronic Communications Regulations 2003 (PECR)",
        _RESOURCES_DIR / "downloads" / "PECR_2003_uksi_20032426_en.pdf",
        "file",
    ),
    (
        "Financial Services and Markets Act 2000 (FSMA)",
        _RESOURCES_DIR / "downloads" / "FSMA_2000_ukpga_20000008_en.pdf",
        "file",
    ),
]


def list_sources():
    """Check all source files exist and list them."""
    print(f"{'=' * 60}")
    print(f"  Hedge Edge Legal — NotebookLM Sources")
    print(f"{'=' * 60}")
    ok = 0
    missing = 0
    for label, path, stype in SOURCES:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {label} ({stype}, {size:,} bytes)")
            ok += 1
        else:
            print(f"  ❌ {label} — MISSING: {path}")
            missing += 1
    print(f"\n  {ok} found, {missing} missing")
    return missing == 0


async def setup():
    """Create notebook and load all sources."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("ERROR: Install notebooklm-py[browser]:")
        print("  pip install notebooklm-py[browser]")
        sys.exit(1)

    print(f"\nSetting up '{NOTEBOOK_NAME}' notebook...\n")

    available = [(l, p, t) for l, p, t in SOURCES if p.exists()]
    skipped = [(l, p) for l, p, t in SOURCES if not p.exists()]

    if not available:
        print("ERROR: No source files found.")
        sys.exit(1)

    for label, path in skipped:
        print(f"  SKIP: {label}")

    async with (await NotebookLMClient.from_storage()) as client:
        notebooks = await client.notebooks.list()
        existing = next(
            (nb for nb in notebooks if NOTEBOOK_NAME.lower() in nb.title.lower()),
            None,
        )

        if existing:
            print(f"  Notebook exists (id={existing.id})")
            notebook = existing
        else:
            notebook = await client.notebooks.create(title=NOTEBOOK_NAME)
            print(f"  Created notebook: {notebook.id}")

        print(f"\n  Loading {len(available)} sources...")
        loaded = 0
        for label, path, source_type in available:
            print(f"    {label}...", end=" ", flush=True)
            try:
                if source_type == "file":
                    await client.sources.add_file(notebook.id, file_path=str(path), wait=True)
                else:
                    text = path.read_text(encoding="utf-8")
                    await client.sources.add_text(notebook.id, title=label, content=text, wait=True)
                print("✅")
                loaded += 1
            except Exception as exc:
                print(f"❌ {exc}")

    print(f"\n  Done: {loaded}/{len(available)} sources loaded into '{NOTEBOOK_NAME}'")
    if skipped:
        print(f"  {len(skipped)} sources skipped (files missing)")


async def test_query(question: str):
    """Test a query against the legal notebook."""
    from shared.notebooklm_client import aquery
    print(f"\n  Testing: {question}")
    print(f"  {'─' * 50}")
    answer = await aquery(question, max_chars=4000)
    if answer:
        print(f"\n{answer}\n")
    else:
        print("\n  No response — check NotebookLM is set up and budget is available.\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Setup Hedge Edge Legal NotebookLM notebook")
    parser.add_argument("--list", action="store_true", help="List sources and check existence")
    parser.add_argument("--test", help="Test a query against the notebook")
    args = parser.parse_args()

    if args.list:
        list_sources()
    elif args.test:
        asyncio.run(test_query(args.test))
    else:
        asyncio.run(setup())


if __name__ == "__main__":
    main()
