#!/usr/bin/env python3
"""
legal_query_engine.py — RAG-powered legal Q&A via NotebookLM
=============================================================
Queries the "Hedge Edge Legal" NotebookLM notebook for grounded,
cited answers to legal and compliance questions.

Falls back to local resources/ docs when NotebookLM is unavailable.

Usage:
    python legal_query_engine.py --question "Do we need ICO registration?"
    python legal_query_engine.py --question "GDPR impact of Supabase" --jurisdiction uk
    python legal_query_engine.py --question "IB disclosure requirements" --doc-type ib-agreement
    python legal_query_engine.py --setup   # Create the NotebookLM notebook with legal sources
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────
_SKILL_DIR = Path(__file__).resolve().parent.parent
_RESOURCES_DIR = _SKILL_DIR / "resources"
_WORKSPACE = _SKILL_DIR.parents[4]  # up to IDE 1 root
sys.path.insert(0, str(_WORKSPACE.parent.parent.parent))  # Orchestrator root

from shared.notebooklm_client import aquery as nb_aquery, budget_remaining
from shared.notion_client import log_task

_log = logging.getLogger("legal_query_engine")
logging.basicConfig(level=logging.INFO, format="%(message)s")

NOTEBOOK_NAME = "Hedge Edge Legal"

# ── Risk classification ──────────────────────────────────────────────

RISK_KEYWORDS = {
    "CRITICAL": ["breach", "fine", "penalty", "lawsuit", "injunction", "ico enforcement"],
    "HIGH": ["non-compliant", "violation", "mandatory", "must", "shall", "prohibited"],
    "MEDIUM": ["should", "recommended", "advisable", "risk", "consider"],
    "LOW": ["optional", "best practice", "may", "minor"],
}


def classify_risk(text: str) -> str:
    """Classify risk level based on keywords in the response."""
    lower = text.lower()
    for level, keywords in RISK_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return level
    return "LOW"


# ── Local fallback: load resources docs ──────────────────────────────

_doc_cache: str = ""


def _load_legal_docs(doc_type: str = "all") -> str:
    """Load legal resource documents from the resources/ directory."""
    global _doc_cache
    if not _RESOURCES_DIR.is_dir():
        _log.warning(f"Resources dir not found: {_RESOURCES_DIR}")
        return ""

    texts = []
    for f in sorted(_RESOURCES_DIR.iterdir()):
        if not f.suffix == ".md":
            continue
        if doc_type != "all" and doc_type not in f.stem:
            continue
        texts.append(f.read_text(encoding="utf-8"))

    combined = "\n\n---\n\n".join(texts)
    _log.info(f"[Legal] Loaded {len(texts)} resource docs ({len(combined)} chars)")
    return combined


# ── NotebookLM notebook setup ───────────────────────────────────────

IDE1_ROOT = _WORKSPACE

LEGAL_SOURCES = [
    ("UK GDPR Summary", _RESOURCES_DIR / "uk-gdpr-summary.md", "text"),
    ("FCA Financial Promotions", _RESOURCES_DIR / "fca-financial-promotions.md", "text"),
    ("Privacy Policy Template", _RESOURCES_DIR / "privacy-policy-template.md", "text"),
    ("Terms of Service Template", _RESOURCES_DIR / "terms-of-service-template.md", "text"),
    ("Risk Disclaimers", _RESOURCES_DIR / "risk-disclaimers.md", "text"),
    ("Data Processing Register", _RESOURCES_DIR / "data-processing-register.md", "text"),
    ("IB Agreement Checklist", _RESOURCES_DIR / "ib-agreement-checklist.md", "text"),
    ("DSAR Process", _RESOURCES_DIR / "dsar-process.md", "text"),
    ("Prop Firm Regulatory Landscape", _RESOURCES_DIR / "prop-firm-regulatory-landscape.md", "text"),
    # External PDF sources from Context/
    (
        "Vantage IB Agreement",
        IDE1_ROOT / "Context" / "IB agreement" / "Vantage_IB_agreement.pdf",
        "file",
    ),
    (
        "BlackBull Partners T&C",
        IDE1_ROOT / "Context" / "IB agreement" / "Blackbull_Partners-Terms-and-Conditions-29-March-2024.pdf",
        "file",
    ),
]


async def setup_notebook():
    """Create the Hedge Edge Legal NotebookLM notebook and load sources."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("ERROR: Install notebooklm-py[browser]: pip install notebooklm-py[browser]")
        sys.exit(1)

    print(f"Setting up '{NOTEBOOK_NAME}' notebook...")

    missing = []
    for label, path, _ in LEGAL_SOURCES:
        if not path.exists():
            missing.append((label, str(path)))
            print(f"  SKIP: {label} (not found)")
        else:
            print(f"  OK:   {label}")

    available = [(l, p, t) for l, p, t in LEGAL_SOURCES if p.exists()]
    if not available:
        print("\nERROR: No source files found. Create resources first.")
        sys.exit(1)

    async with (await NotebookLMClient.from_storage()) as client:
        notebooks = await client.notebooks.list()
        existing = next(
            (nb for nb in notebooks if NOTEBOOK_NAME.lower() in nb.title.lower()),
            None,
        )

        if existing:
            print(f"\nNotebook already exists (id={existing.id})")
            notebook = existing
        else:
            notebook = await client.notebooks.create(title=NOTEBOOK_NAME)
            print(f"\nCreated notebook: {notebook.id}")

        print(f"\nLoading {len(available)} sources...")
        for label, path, source_type in available:
            print(f"  Loading: {label}...", end=" ", flush=True)
            try:
                if source_type == "file":
                    await client.sources.add_file(notebook.id, file_path=str(path), wait=True)
                else:
                    text = path.read_text(encoding="utf-8")
                    await client.sources.add_text(notebook.id, title=label, text=text, wait=True)
                print("done")
            except Exception as exc:
                print(f"FAILED: {exc}")

    print(f"\nNotebook '{NOTEBOOK_NAME}' ready with {len(available)} sources.")
    if missing:
        print(f"  {len(missing)} sources skipped (files not found)")


# ── Core query function ─────────────────────────────────────────────

async def query_legal(
    question: str,
    jurisdiction: str = "uk",
    doc_type: str = "all",
    use_notebooklm: bool = True,
) -> dict:
    """
    Query the legal RAG system.

    1. Try NotebookLM (grounded, cited answers from loaded legal docs)
    2. Fall back to local resources/ if NotebookLM unavailable
    """
    result = {
        "question": question,
        "jurisdiction": jurisdiction,
        "answer": "",
        "risk_level": "LOW",
        "action_items": [],
        "citations": [],
        "notebooklm_used": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    enriched_question = (
        f"[Jurisdiction: {jurisdiction.upper()}] "
        f"[Document scope: {doc_type}] "
        f"{question}"
    )

    # ── Try NotebookLM RAG ──
    if use_notebooklm and budget_remaining() > 0:
        try:
            answer = await nb_aquery(enriched_question, max_chars=6000)
            if answer:
                result["answer"] = answer
                result["notebooklm_used"] = True
                result["risk_level"] = classify_risk(answer)
                _log.info(f"[Legal] NotebookLM response: {len(answer)} chars")
        except Exception as exc:
            _log.warning(f"[Legal] NotebookLM query failed: {exc}")

    # ── Fallback: local docs ──
    if not result["answer"]:
        docs = _load_legal_docs(doc_type)
        if docs:
            result["answer"] = (
                f"[FALLBACK — Local resources, not NotebookLM]\n\n"
                f"Relevant legal documentation ({len(docs)} chars loaded):\n\n"
                f"{docs[:4000]}"
            )
            result["risk_level"] = classify_risk(docs)
            _log.info("[Legal] Using local fallback docs")
        else:
            result["answer"] = (
                "No legal resources available. Run:\n"
                "  python legal_query_engine.py --setup\n"
                "to create the NotebookLM notebook, or add .md files to resources/"
            )
            result["risk_level"] = "HIGH"

    return result


def query_legal_sync(question: str, **kwargs) -> dict:
    """Synchronous wrapper for query_legal."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, query_legal(question, **kwargs)).result(timeout=30)
    return asyncio.run(query_legal(question, **kwargs))


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Legal RAG Query Engine")
    parser.add_argument("--question", "-q", help="Legal question to ask")
    parser.add_argument("--jurisdiction", "-j", default="uk", choices=["uk", "eu", "us", "global"])
    parser.add_argument("--doc-type", "-d", default="all",
                        choices=["gdpr", "fca", "terms", "privacy", "ib-agreement",
                                 "financial-promotions", "dsar", "all"])
    parser.add_argument("--setup", action="store_true", help="Set up the NotebookLM notebook")
    parser.add_argument("--no-notebooklm", action="store_true", help="Skip NotebookLM, use local docs only")
    parser.add_argument("--budget", action="store_true", help="Show remaining NotebookLM budget")
    args = parser.parse_args()

    if args.budget:
        print(f"NotebookLM budget remaining: {budget_remaining()} queries")
        return

    if args.setup:
        asyncio.run(setup_notebook())
        return

    if not args.question:
        parser.print_help()
        return

    result = query_legal_sync(
        args.question,
        jurisdiction=args.jurisdiction,
        doc_type=args.doc_type,
        use_notebooklm=not args.no_notebooklm,
    )

    print("\n" + "=" * 70)
    print(f"  LEGAL QUERY: {result['question']}")
    print(f"  Jurisdiction: {result['jurisdiction'].upper()}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  NotebookLM: {'Yes' if result['notebooklm_used'] else 'No (fallback)'}")
    print("=" * 70)
    print(f"\n{result['answer']}\n")

    log_task(
        agent="Legal Compliance",
        task=f"Legal query: {args.question[:80]}",
        status="done",
        detail=f"Risk: {result['risk_level']}, NotebookLM: {result['notebooklm_used']}",
    )


if __name__ == "__main__":
    main()
