"""
Investor Vetting — RESEARCH Execution Script

Directive: Business/RESEARCH/directives/investor-vetting.md
Resource:  Business/RESEARCH/resources/buffett-investor-corpus.md

Reads PDF thesis documents from the outputs folder and extracts their text
content so the Research agent can review previously generated theses for
investor-grade vetting without manual copy-paste.

Usage:
    # List all PDFs in the outputs folder
    python vet_business_idea.py --list

    # Extract text from a specific PDF
    python vet_business_idea.py --read "Kotob_Capitals_Business_Thesis.pdf"

    # Extract text from all PDFs in the outputs folder
    python vet_business_idea.py --read-all

Dependencies:
    pip install pymupdf   (imported as fitz)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RESEARCH_DIR / "resources" / "outputs"


def list_pdfs() -> list[Path]:
    """Return all PDF files in the outputs folder."""
    if not OUTPUT_DIR.exists():
        print(f"Output directory does not exist: {OUTPUT_DIR}")
        return []
    pdfs = sorted(OUTPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDF files found in outputs folder.")
    return pdfs


def extract_text(pdf_path: Path) -> str:
    """Extract text from a PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # pymupdf
    except ImportError:
        print("ERROR: pymupdf is required. Install with: pip install pymupdf")
        sys.exit(1)

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return ""

    text_parts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")

    return "\n\n".join(text_parts)


def cmd_list() -> None:
    """Print available PDFs."""
    pdfs = list_pdfs()
    if pdfs:
        print(f"Found {len(pdfs)} PDF(s) in {OUTPUT_DIR}:\n")
        for p in pdfs:
            size_kb = p.stat().st_size / 1024
            print(f"  {p.name}  ({size_kb:.0f} KB)")


def cmd_read(filename: str) -> None:
    """Extract and print text from a single PDF."""
    pdf_path = OUTPUT_DIR / filename
    if not pdf_path.exists():
        # Try case-insensitive match
        matches = [p for p in OUTPUT_DIR.glob("*.pdf") if p.name.lower() == filename.lower()]
        if matches:
            pdf_path = matches[0]
        else:
            print(f"PDF not found: {filename}")
            print(f"Available files: {[p.name for p in list_pdfs()]}")
            return

    text = extract_text(pdf_path)
    if text:
        print(f"=== {pdf_path.name} ===\n")
        print(text)
    else:
        print(f"No extractable text in {pdf_path.name}")


def cmd_read_all() -> None:
    """Extract and print text from all PDFs in outputs."""
    pdfs = list_pdfs()
    if not pdfs:
        return
    for pdf_path in pdfs:
        text = extract_text(pdf_path)
        print(f"\n{'=' * 60}")
        print(f"=== {pdf_path.name} ===")
        print(f"{'=' * 60}\n")
        if text:
            print(text)
        else:
            print("(No extractable text)")
        print()


def main() -> None:
    """Entry point for Investor Vetting PDF reader."""
    parser = argparse.ArgumentParser(
        description="Read thesis PDFs from the RESEARCH outputs folder for investor vetting."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all PDFs in the outputs folder")
    group.add_argument("--read", metavar="FILENAME", help="Extract text from a specific PDF")
    group.add_argument("--read-all", action="store_true", help="Extract text from all PDFs")

    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.read:
        cmd_read(args.read)
    elif args.read_all:
        cmd_read_all()


if __name__ == "__main__":
    main()
