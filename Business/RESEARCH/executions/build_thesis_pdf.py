"""
Business Thesis PDF Builder — RESEARCH Execution Script

Directive: Business/RESEARCH/directives/business-thesis.md
Resource:  Business/RESEARCH/resources/business-thesis-template.md

Generates a professionally formatted PDF thesis document from structured
JSON input. The JSON contains the completed thesis sections following the
canonical template.

Usage:
    python build_thesis_pdf.py --input thesis_data.json
    python build_thesis_pdf.py --input thesis_data.json --output custom_name.pdf

Dependencies:
    pip install reportlab

The input JSON schema is documented at the bottom of this file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        HRFlowable,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required. Install with: pip install reportlab")
    sys.exit(1)


# ── Paths ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RESEARCH_DIR / "resources" / "outputs"


# ── Page Layout ─────────────────────────────────────────────────────────

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 2.5 * cm
RIGHT_MARGIN = 2.5 * cm
TOP_MARGIN = 2.5 * cm
BOTTOM_MARGIN = 2.5 * cm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


# ── Styles ──────────────────────────────────────────────────────────────

def build_styles() -> dict[str, ParagraphStyle]:
    """Build the document paragraph styles."""
    base = getSampleStyleSheet()

    styles = {}

    styles["header_company"] = ParagraphStyle(
        "header_company",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.black,
    )

    styles["header_date"] = ParagraphStyle(
        "header_date",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=colors.black,
    )

    styles["page_number"] = ParagraphStyle(
        "page_number",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )

    styles["section_heading"] = ParagraphStyle(
        "section_heading",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceAfter=12,
        spaceBefore=24,
        underline=True,
        textColor=colors.black,
    )

    styles["subsection_heading"] = ParagraphStyle(
        "subsection_heading",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        spaceAfter=8,
        spaceBefore=16,
        textColor=colors.black,
    )

    styles["sub_subsection_heading"] = ParagraphStyle(
        "sub_subsection_heading",
        parent=base["Heading3"],
        fontName="Helvetica-BoldOblique",
        fontSize=11,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.black,
    )

    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        textColor=colors.black,
    )

    styles["body_bold"] = ParagraphStyle(
        "body_bold",
        parent=styles["body"],
        fontName="Helvetica-Bold",
    )

    styles["body_italic"] = ParagraphStyle(
        "body_italic",
        parent=styles["body"],
        fontName="Helvetica-Oblique",
    )

    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=styles["body"],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4,
    )

    styles["reference"] = ParagraphStyle(
        "reference",
        parent=styles["body"],
        fontSize=9,
        leading=12,
        leftIndent=20,
        firstLineIndent=-20,
        spaceAfter=4,
    )

    styles["prompt_text"] = ParagraphStyle(
        "prompt_text",
        parent=styles["body"],
        fontName="Helvetica-Oblique",
        textColor=colors.Color(0.8, 0, 0),
        fontSize=9,
    )

    return styles


# ── Document Builder ────────────────────────────────────────────────────

class ThesisBuilder:
    """Builds a PDF thesis document from structured data."""

    def __init__(self, data: dict, output_path: Path) -> None:
        self.data = data
        self.output_path = output_path
        self.styles = build_styles()
        self.story: list = []
        self.company_name = data.get("company_name", "COMPANY NAME")
        self.date_str = data.get("date", datetime.now().strftime("%B %Y").upper())

    def _add_header_footer(self, canvas, doc):
        """Draw header and footer on each page."""
        canvas.saveState()

        # Header
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - 1.5 * cm, self.company_name.upper())
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 1.5 * cm, self.date_str
        )

        # Header line
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        canvas.line(
            LEFT_MARGIN,
            PAGE_HEIGHT - 1.8 * cm,
            PAGE_WIDTH - RIGHT_MARGIN,
            PAGE_HEIGHT - 1.8 * cm,
        )

        # Footer - page number
        canvas.setFont("Helvetica", 8)
        page_text = f"Page {doc.page} of {{total_pages}}"
        canvas.drawCentredString(PAGE_WIDTH / 2, BOTTOM_MARGIN - 0.5 * cm, page_text)

        canvas.restoreState()

    def _heading(self, number: int, title: str) -> None:
        """Add a numbered section heading."""
        self.story.append(
            Paragraph(f"{number}. {title}:", self.styles["section_heading"])
        )

    def _subheading(self, title: str) -> None:
        """Add a subsection heading."""
        self.story.append(Paragraph(title, self.styles["subsection_heading"]))

    def _sub_subheading(self, title: str) -> None:
        """Add a sub-subsection heading."""
        self.story.append(Paragraph(title, self.styles["sub_subsection_heading"]))

    def _body(self, text: str) -> None:
        """Add a body paragraph."""
        if text and text.strip():
            # Escape XML entities for reportlab
            safe_text = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self.story.append(Paragraph(safe_text, self.styles["body"]))

    def _body_bold(self, text: str) -> None:
        """Add a bold body paragraph."""
        if text and text.strip():
            safe_text = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self.story.append(Paragraph(safe_text, self.styles["body_bold"]))

    def _body_italic(self, text: str) -> None:
        """Add an italic body paragraph."""
        if text and text.strip():
            safe_text = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self.story.append(Paragraph(safe_text, self.styles["body_italic"]))

    def _spacer(self, height: float = 6) -> None:
        """Add vertical space."""
        self.story.append(Spacer(1, height))

    def _hr(self) -> None:
        """Add a horizontal rule."""
        self.story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

    def _bullet_list(self, items: list[str]) -> None:
        """Add a bulleted list."""
        for item in items:
            safe = (
                item.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self.story.append(
                Paragraph(f"• {safe}", self.styles["bullet"])
            )

    def _table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Add a formatted comparison table."""
        data = [headers] + rows

        # Escape all cell content
        safe_data = []
        for row in data:
            safe_row = []
            for cell in row:
                s = str(cell) if cell else ""
                s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe_row.append(Paragraph(s, ParagraphStyle(
                    "table_cell",
                    fontName="Helvetica",
                    fontSize=8,
                    leading=10,
                )))
            safe_data.append(safe_row)

        # Calculate column widths
        n_cols = len(headers)
        col_width = CONTENT_WIDTH / n_cols

        table = Table(safe_data, colWidths=[col_width] * n_cols)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.85, 0.89, 0.96)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
        ]))
        self.story.append(table)
        self._spacer(8)

    def _page_break(self) -> None:
        """Insert a page break."""
        self.story.append(PageBreak())

    # ── Section builders ────────────────────────────────────────────────

    def _build_summary(self) -> None:
        summary = self.data.get("summary", {})
        self._heading(1, "Summary")

        for key in [
            "target_customer_and_problem",
            "product_and_value_proposition",
            "distinctive_features_and_team",
            "current_stage",
            "financial_requirement",
            "risks_and_return",
        ]:
            text = summary.get(key, "")
            self._body(text)

    def _build_history(self) -> None:
        history = self.data.get("history", {})
        self._page_break()
        self._heading(2, "History")
        self._subheading("Current stage and progress to date")
        self._body(history.get("current_stage", ""))
        self._body(history.get("progress_milestones", ""))

    def _build_product(self) -> None:
        product = self.data.get("product", {})
        self._page_break()
        self._heading(3, "Product and service")

        # 3.1
        self._body_italic(
            "A precise description of what the product or service is and what it will be used for."
        )
        self._body(product.get("description", ""))

        # 3.2
        self._body_italic(
            "A realistic assessment of your product's unique or distinctive advantages and "
            "the way in which these advantages will translate into benefits for your customers."
        )
        self._body(product.get("advantages_and_benefits", ""))

        # 3.3
        self._body_italic(
            "An evaluation of the ease with which competitors might imitate your advantages "
            "and match your benefits, plus quantification of these benefits if possible."
        )
        self._body(product.get("competitor_imitation_analysis", ""))

        # Moat table if provided
        moat = product.get("moat_scores")
        if moat:
            headers = ["Moat Type", "Score (0-3)", "Evidence"]
            rows = [[m["type"], str(m["score"]), m["evidence"]] for m in moat]
            self._table(headers, rows)
            total = sum(m["score"] for m in moat)
            self._body_bold(f"Overall moat score: {total}/18")
            if total < 6:
                self._body(
                    "A score below 6 indicates a race position — timing advantage only, "
                    "no structural moat."
                )

        # 3.4
        self._body_italic(
            "A simple, but not simplistic, analysis of the technology you are using and "
            "an appraisal of the risks associated with it."
        )
        self._body(product.get("technology_analysis", ""))

    def _build_market(self) -> None:
        market = self.data.get("market", {})
        self._page_break()
        self._heading(4, "Market and competitors")

        # Part 1
        self._subheading("Market and Competitors — Part 1: General Market Description")
        self._body(market.get("general_description", ""))

        # Part 2
        self._page_break()
        self._subheading("Market and Competitors — Part 2: Target Market Segment")

        self._sub_subheading("Market segment")
        self._body(market.get("segment_definition", ""))

        self._sub_subheading("Geographic Scope")
        self._body(market.get("geographic_scope", ""))

        self._sub_subheading("Segment Size and Growth")
        self._body(market.get("segment_size_and_growth", ""))

        self._sub_subheading("Buying Patterns and Customer Priorities")
        self._body(market.get("buying_patterns", ""))

        self._sub_subheading("Customer Adjustments Required")
        self._body(market.get("customer_adjustments", ""))

        # Part 3
        self._page_break()
        self._subheading(
            "Market and Competitors — Part 3: Who Are the Competitors, "
            "How Large Are They, and How Are They Organised?"
        )

        # Tier 1
        self._sub_subheading("Tier 1 — Direct Competitors")
        for comp in market.get("competitors_tier_1", []):
            self._body_bold(f"{comp.get('name', '')} ({comp.get('url', '')})")
            self._body(comp.get("description", ""))

        # Tier 2
        self._sub_subheading("Tier 2 — Broader / Adjacent Competitors")
        for comp in market.get("competitors_tier_2", []):
            self._body_bold(f"{comp.get('name', '')} ({comp.get('url', '')})")
            self._body(comp.get("description", ""))

        # Basis of competition
        self._sub_subheading("On What Basis Do Rivals Compete?")
        self._body(market.get("basis_of_competition", ""))

        # Comparison table
        comp_table = market.get("comparison_table")
        if comp_table:
            self._sub_subheading("Comparative Analysis")
            self._table(
                comp_table.get("headers", []),
                comp_table.get("rows", []),
            )

        # Differentiation
        self._sub_subheading(
            "What Makes the Product Superior or Different, "
            "and How Can Unique Features Be Protected?"
        )
        self._body(market.get("differentiation_analysis", ""))

        # Barriers
        self._sub_subheading(
            "What Barriers Does a New Entrant Face, "
            "and How Is Competition Likely to React?"
        )
        self._body(market.get("barriers_and_response", ""))

        # Customer perception
        self._sub_subheading("How Do Potential Customers See the Competition?")
        self._body(market.get("customer_perception", ""))

    def _build_risk_return_exit(self) -> None:
        rre = self.data.get("risk_return_exit", {})
        self._page_break()
        self._heading(5, "Risk, Return, Exit")

        self._body(rre.get("intro", ""))

        # Risks
        self._subheading("The Risks")
        for risk in rre.get("risks", []):
            self._body_bold(f"{risk.get('number', '')}. {risk.get('title', '')}")
            self._body(risk.get("description", ""))

        # Expected return
        self._subheading("Expected Return")
        self._body(rre.get("expected_return", ""))

        # Exit routes
        self._subheading("Exit Routes")
        self._body(rre.get("exit_routes", ""))

        # Investor objections
        self._subheading("Investor Objections and Responses")
        self._body(rre.get("investor_objections", ""))

    def _build_references(self) -> None:
        refs = self.data.get("references", [])
        if refs:
            self._page_break()
            self._subheading("Reference List")
            for ref in refs:
                safe = (
                    ref.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                self.story.append(Paragraph(safe, self.styles["reference"]))

    # ── Main build ──────────────────────────────────────────────────────

    def build(self) -> Path:
        """Build the complete PDF and return the output path."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=f"{self.company_name} — Business Thesis",
            author="AgentForge Research Department",
        )

        # Build all sections
        self._build_summary()
        self._build_history()
        self._build_product()
        self._build_market()
        self._build_risk_return_exit()
        self._build_references()

        # Build PDF
        doc.build(self.story, onFirstPage=self._add_header_footer,
                  onLaterPages=self._add_header_footer)

        # Fix page count placeholder
        # (reportlab doesn't natively support total page count in headers,
        # but the placeholder is written for visual consistency)

        return self.output_path


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point for the thesis PDF builder."""
    parser = argparse.ArgumentParser(
        description="Generate a business thesis PDF from structured JSON input."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSON file containing thesis data.",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Output PDF filename (saved in resources/outputs/). "
             "Defaults to <company-slug>-thesis-<YYYY-MM>.pdf",
    )
    args = parser.parse_args()

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Determine output path
    if args.output:
        output_path = OUTPUT_DIR / args.output
    else:
        slug = data.get("company_slug", "unknown")
        date_str = datetime.now().strftime("%Y-%m")
        output_path = OUTPUT_DIR / f"{slug}-thesis-{date_str}.pdf"

    # Build
    builder = ThesisBuilder(data, output_path)
    result = builder.build()
    print(f"PDF generated: {result}")


# ── Input JSON Schema Reference ─────────────────────────────────────────
#
# {
#   "company_name": "Hedge Edge Ltd",
#   "company_slug": "hedge-edge",
#   "date": "APRIL 2026",
#   "summary": {
#     "target_customer_and_problem": "...",
#     "product_and_value_proposition": "...",
#     "distinctive_features_and_team": "...",
#     "current_stage": "...",
#     "financial_requirement": "...",
#     "risks_and_return": "..."
#   },
#   "history": {
#     "current_stage": "...",
#     "progress_milestones": "..."
#   },
#   "product": {
#     "description": "...",
#     "advantages_and_benefits": "...",
#     "competitor_imitation_analysis": "...",
#     "moat_scores": [
#       {"type": "Switching costs", "score": 1, "evidence": "..."},
#       {"type": "Network effects", "score": 0, "evidence": "..."},
#       {"type": "Brand / trust", "score": 1, "evidence": "..."},
#       {"type": "Proprietary data", "score": 0, "evidence": "..."},
#       {"type": "Regulatory / IP", "score": 0, "evidence": "..."},
#       {"type": "Integration complexity", "score": 1, "evidence": "..."}
#     ],
#     "technology_analysis": "..."
#   },
#   "market": {
#     "general_description": "...",
#     "segment_definition": "...",
#     "geographic_scope": "...",
#     "segment_size_and_growth": "...",
#     "buying_patterns": "...",
#     "customer_adjustments": "...",
#     "competitors_tier_1": [
#       {
#         "name": "Competitor A",
#         "url": "competitor-a.com",
#         "description": "..."
#       }
#     ],
#     "competitors_tier_2": [
#       {
#         "name": "Competitor B",
#         "url": "competitor-b.com",
#         "description": "..."
#       }
#     ],
#     "basis_of_competition": "...",
#     "comparison_table": {
#       "headers": ["Attribute", "Subject Co", "Comp A", "Comp B"],
#       "rows": [
#         ["Pricing", "$29/mo", "$19/mo", "$49/mo"],
#         ["Platform", "MT5", "MT4, MT5", "All"]
#       ]
#     },
#     "differentiation_analysis": "...",
#     "barriers_and_response": "...",
#     "customer_perception": "..."
#   },
#   "risk_return_exit": {
#     "intro": "...",
#     "risks": [
#       {
#         "number": 1,
#         "title": "Market adoption risk",
#         "description": "..."
#       }
#     ],
#     "expected_return": "...",
#     "exit_routes": "...",
#     "investor_objections": "..."
#   },
#   "references": [
#     "Author, A. (Year) Title. Available at: URL (Accessed: date).",
#     "..."
#   ]
# }


if __name__ == "__main__":
    main()
