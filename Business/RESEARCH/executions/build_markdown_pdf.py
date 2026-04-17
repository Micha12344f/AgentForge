"""
Simple Markdown to PDF exporter for research outputs.

Usage:
    python build_markdown_pdf.py --input path/to/file.md
    python build_markdown_pdf.py --input path/to/file.md --output path/to/file.pdf

Dependencies:
    pip install reportlab
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required. Install with: pip install reportlab")
    sys.exit(1)


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 2.25 * cm
RIGHT_MARGIN = 2.25 * cm
TOP_MARGIN = 2.25 * cm
BOTTOM_MARGIN = 2.25 * cm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {}
    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=18,
        alignment=TA_CENTER,
        textColor=colors.black,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        spaceBefore=14,
        spaceAfter=10,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=8,
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        parent=base["Heading3"],
        fontName="Helvetica-BoldOblique",
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=styles["body"],
        leftIndent=16,
        bulletIndent=4,
    )
    styles["code"] = ParagraphStyle(
        "code",
        parent=styles["body"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        leftIndent=10,
        rightIndent=10,
        backColor=colors.HexColor("#F5F5F5"),
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8,
    )
    styles["equation"] = ParagraphStyle(
        "equation",
        parent=styles["code"],
        alignment=TA_CENTER,
        leftIndent=0,
        rightIndent=0,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        parent=styles["body"],
        fontSize=7.5,
        leading=9,
        spaceAfter=0,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        parent=styles["table_cell"],
        fontName="Helvetica-Bold",
    )

    return styles


def escape_text(text: str) -> str:
    return html.escape(text, quote=False)


def format_inline(text: str) -> str:
    safe = escape_text(text)
    safe = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", safe)
    safe = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", safe)
    return safe.replace("\n", "<br/>")


def is_rule(line: str) -> bool:
    stripped = line.strip()
    return stripped in {"---", "***", "___"}


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:-1]


def is_table_separator(line: str) -> bool:
    stripped = line.strip().strip("|")
    if not stripped:
        return False
    cells = [cell.strip() for cell in stripped.split("|")]
    return all(cell and set(cell) <= {":", "-", " "} for cell in cells)


def clean_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(PAGE_WIDTH / 2, BOTTOM_MARGIN - 0.4 * cm, f"Page {doc.page}")
    canvas.restoreState()


class MarkdownPdfBuilder:
    def __init__(self, input_path: Path, output_path: Path) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.styles = build_styles()
        self.story = []

    def add_paragraph(self, text: str, style_name: str = "body") -> None:
        cleaned = text.strip()
        if cleaned:
            self.story.append(Paragraph(format_inline(cleaned), self.styles[style_name]))

    def add_bullet(self, text: str) -> None:
        cleaned = text.strip()
        if cleaned:
            self.story.append(
                Paragraph(format_inline(cleaned), self.styles["bullet"], bulletText="•")
            )

    def add_table(self, rows: list[list[str]]) -> None:
        if not rows:
            return

        column_count = max(len(row) for row in rows)
        normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
        col_widths = [CONTENT_WIDTH / column_count] * column_count

        table_rows = []
        for row_index, row in enumerate(normalized_rows):
            style_name = "table_header" if row_index == 0 else "table_cell"
            table_rows.append(
                [Paragraph(format_inline(cell), self.styles[style_name]) for cell in row]
            )

        table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EEF6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA5B1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ]
            )
        )
        self.story.append(table)
        self.story.append(Spacer(1, 0.2 * cm))

    def add_preformatted(self, text: str, style_name: str) -> None:
        cleaned = text.rstrip()
        if cleaned:
            self.story.append(Preformatted(cleaned, self.styles[style_name]))
            self.story.append(Spacer(1, 0.1 * cm))

    def parse(self, raw_text: str) -> None:
        lines = raw_text.splitlines()
        index = 0

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()

            if not stripped:
                index += 1
                continue

            if index == 0 and line.startswith("# "):
                self.story.append(Paragraph(format_inline(line[2:].strip()), self.styles["title"]))
                index += 1
                continue

            if line.startswith("# "):
                self.story.append(Paragraph(format_inline(line[2:].strip()), self.styles["h1"]))
                index += 1
                continue

            if line.startswith("## "):
                self.story.append(Paragraph(format_inline(line[3:].strip()), self.styles["h2"]))
                index += 1
                continue

            if line.startswith("### "):
                self.story.append(Paragraph(format_inline(line[4:].strip()), self.styles["h3"]))
                index += 1
                continue

            if is_rule(line):
                self.story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#6B7280")))
                self.story.append(Spacer(1, 0.18 * cm))
                index += 1
                continue

            if stripped.startswith("```"):
                code_lines = []
                index += 1
                while index < len(lines) and not lines[index].strip().startswith("```"):
                    code_lines.append(lines[index])
                    index += 1
                if index < len(lines):
                    index += 1
                self.add_preformatted("\n".join(code_lines), "code")
                continue

            if stripped.startswith("$$"):
                if stripped.endswith("$$") and len(stripped) > 4:
                    self.add_preformatted(stripped[2:-2].strip(), "equation")
                    index += 1
                    continue

                equation_lines = []
                index += 1
                while index < len(lines) and lines[index].strip() != "$$":
                    equation_lines.append(lines[index])
                    index += 1
                if index < len(lines):
                    index += 1
                self.add_preformatted("\n".join(equation_lines), "equation")
                continue

            if is_table_line(line):
                table_lines = []
                while index < len(lines) and is_table_line(lines[index]):
                    table_lines.append(lines[index])
                    index += 1

                rows = []
                for row_index, table_line in enumerate(table_lines):
                    if row_index == 1 and is_table_separator(table_line):
                        continue
                    rows.append(clean_table_row(table_line))

                self.add_table(rows)
                continue

            if stripped.startswith(("- ", "* ")):
                while index < len(lines) and lines[index].strip().startswith(("- ", "* ")):
                    self.add_bullet(lines[index].strip()[2:])
                    index += 1
                continue

            paragraph_lines = [line.strip()]
            index += 1
            while index < len(lines):
                next_line = lines[index]
                next_stripped = next_line.strip()
                if not next_stripped:
                    index += 1
                    break
                if next_line.startswith(("# ", "## ", "### ")):
                    break
                if is_rule(next_line) or is_table_line(next_line) or next_stripped.startswith(("- ", "* ", "```", "$$")):
                    break
                paragraph_lines.append(next_line.strip())
                index += 1

            self.add_paragraph(" ".join(paragraph_lines))

    def build(self) -> None:
        raw_text = self.input_path.read_text(encoding="utf-8")
        self.parse(raw_text)

        document = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=self.input_path.stem,
            author="GitHub Copilot",
        )
        document.build(self.story, onFirstPage=page_footer, onLaterPages=page_footer)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a markdown file to PDF.")
    parser.add_argument("--input", required=True, help="Path to the input markdown file.")
    parser.add_argument("--output", help="Path to the output PDF file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 1

    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    builder = MarkdownPdfBuilder(input_path=input_path, output_path=output_path)
    builder.build()
    print(f"Created PDF: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())