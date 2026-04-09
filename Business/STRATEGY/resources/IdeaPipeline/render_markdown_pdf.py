#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "agentic-ai-business-strategy-2026-04-08.md"
DEFAULT_OUTPUT = DEFAULT_INPUT.with_suffix(".pdf")

NAVY = colors.HexColor("#10243f")
BLUE = colors.HexColor("#1f5b99")
TEAL = colors.HexColor("#127475")
LIGHT_BG = colors.HexColor("#f5f7fa")
MID_BG = colors.HexColor("#e6ecf2")
DARK_TEXT = colors.HexColor("#1a202c")
MUTED = colors.HexColor("#4a5568")
WHITE = colors.white

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
ORDERED_RE = re.compile(r"^(\d+)\.\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+(.*)$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def register_fonts() -> dict[str, str]:
    font_candidates = [
        {
            "base": "ArialUnicode",
            "regular": Path("C:/Windows/Fonts/arial.ttf"),
            "bold": Path("C:/Windows/Fonts/arialbd.ttf"),
            "italic": Path("C:/Windows/Fonts/ariali.ttf"),
            "bold_italic": Path("C:/Windows/Fonts/arialbi.ttf"),
        },
        {
            "base": "SegoeUI",
            "regular": Path("C:/Windows/Fonts/segoeui.ttf"),
            "bold": Path("C:/Windows/Fonts/segoeuib.ttf"),
            "italic": Path("C:/Windows/Fonts/segoeuii.ttf"),
            "bold_italic": Path("C:/Windows/Fonts/segoeuiz.ttf"),
        },
        {
            "base": "Calibri",
            "regular": Path("C:/Windows/Fonts/calibri.ttf"),
            "bold": Path("C:/Windows/Fonts/calibrib.ttf"),
            "italic": Path("C:/Windows/Fonts/calibrii.ttf"),
            "bold_italic": Path("C:/Windows/Fonts/calibriz.ttf"),
        },
    ]

    for candidate in font_candidates:
        regular = candidate["regular"]
        bold = candidate["bold"]
        italic = candidate["italic"]
        bold_italic = candidate["bold_italic"]
        if not regular.exists() or not bold.exists():
            continue

        pdfmetrics.registerFont(TTFont(candidate["base"], str(regular)))
        pdfmetrics.registerFont(TTFont(f"{candidate['base']}-Bold", str(bold)))
        if italic.exists():
            pdfmetrics.registerFont(TTFont(f"{candidate['base']}-Italic", str(italic)))
        if bold_italic.exists():
            pdfmetrics.registerFont(TTFont(f"{candidate['base']}-BoldItalic", str(bold_italic)))

        return {
            "regular": candidate["base"],
            "bold": f"{candidate['base']}-Bold",
            "italic": f"{candidate['base']}-Italic" if italic.exists() else candidate["base"],
            "bold_italic": f"{candidate['base']}-BoldItalic" if bold_italic.exists() else f"{candidate['base']}-Bold",
            "mono": "Courier",
        }

    return {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique",
        "bold_italic": "Helvetica-BoldOblique",
        "mono": "Courier",
    }


def build_styles(fonts: dict[str, str]) -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    styles = {
        "cover": ParagraphStyle(
            "Cover",
            parent=sample["Heading1"],
            fontName=fonts["bold"],
            fontSize=24,
            leading=30,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=sample["BodyText"],
            fontName=fonts["regular"],
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=sample["Heading2"],
            fontName=fonts["bold"],
            fontSize=16,
            leading=22,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=sample["Heading3"],
            fontName=fonts["bold"],
            fontSize=12,
            leading=16,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "h4": ParagraphStyle(
            "H4",
            parent=sample["Heading4"],
            fontName=fonts["bold"],
            fontSize=10,
            leading=14,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName=fonts["regular"],
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=sample["BodyText"],
            fontName=fonts["regular"],
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=sample["BodyText"],
            fontName=fonts["bold"],
            fontSize=7.5,
            leading=9,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=sample["BodyText"],
            fontName=fonts["regular"],
            fontSize=7.3,
            leading=9,
            textColor=DARK_TEXT,
            alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=sample["BodyText"],
            fontName=fonts["regular"],
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
    }
    return styles


def markdown_inline_to_rl(text: str, fonts: dict[str, str]) -> str:
    escaped = html.escape(text.strip(), quote=False)
    escaped = CODE_RE.sub(lambda match: f'<font name="{fonts["mono"]}">{html.escape(match.group(1), quote=False)}</font>', escaped)
    escaped = BOLD_RE.sub(r"<b>\1</b>", escaped)
    escaped = ITALIC_RE.sub(r"<i>\1</i>", escaped)
    return escaped.replace("\n", "<br/>")


def split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [part.strip() for part in re.split(r"(?<!\\)\|", stripped)]


def is_separator_row(row: list[str]) -> bool:
    if not row:
        return False
    for cell in row:
        token = cell.replace(" ", "")
        if not re.fullmatch(r":?-{3,}:?", token):
            return False
    return True


def compute_col_widths(rows: list[list[str]], available_width: float) -> list[float]:
    col_count = max(len(row) for row in rows)
    normalized = [row + [""] * (col_count - len(row)) for row in rows]
    raw_lengths: list[int] = []
    for index in range(col_count):
        max_len = max(len(re.sub(r"[*`<>]", "", row[index])) for row in normalized)
        raw_lengths.append(min(max(max_len, 8), 42))

    if col_count <= 4:
        min_width = 24 * mm
    elif col_count <= 6:
        min_width = 18 * mm
    else:
        min_width = 12 * mm

    if min_width * col_count >= available_width:
        return [available_width / col_count] * col_count

    base_total = min_width * col_count
    flex = available_width - base_total
    flex_weights = [max(length - 8, 1) for length in raw_lengths]
    weight_total = sum(flex_weights)
    return [min_width + flex * (weight / weight_total) for weight in flex_weights]


def render_table(table_lines: list[str], styles: dict[str, ParagraphStyle], fonts: dict[str, str], available_width: float) -> Table:
    rows = [split_table_row(line) for line in table_lines if line.strip()]
    if len(rows) > 1 and is_separator_row(rows[1]):
        rows.pop(1)

    col_count = max(len(row) for row in rows)
    normalized = [row + [""] * (col_count - len(row)) for row in rows]
    formatted_rows = []
    for row_index, row in enumerate(normalized):
        style = styles["table_header"] if row_index == 0 else styles["table_cell"]
        formatted_rows.append([Paragraph(markdown_inline_to_rl(cell, fonts), style) for cell in row])

    table = Table(
        formatted_rows,
        colWidths=compute_col_widths(normalized, available_width),
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
                ("GRID", (0, 0), (-1, -1), 0.35, MID_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, MID_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def collect_blocks(lines: list[str]) -> list[tuple[str, object]]:
    blocks: list[tuple[str, object]] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        if stripped == "---":
            blocks.append(("hr", None))
            index += 1
            continue

        if stripped.startswith(">"):
            meta_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                meta_lines.append(lines[index].strip()[1:].strip())
                index += 1
            blocks.append(("meta", meta_lines))
            continue

        if stripped.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].rstrip())
                index += 1
            blocks.append(("table", table_lines))
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            blocks.append(("heading", (len(heading_match.group(1)), heading_match.group(2).strip())))
            index += 1
            continue

        if BULLET_RE.match(stripped):
            items: list[str] = []
            while index < len(lines):
                match = BULLET_RE.match(lines[index].strip())
                if not match:
                    break
                items.append(match.group(1).strip())
                index += 1
            blocks.append(("bullet_list", items))
            continue

        if ORDERED_RE.match(stripped):
            items: list[tuple[str, str]] = []
            while index < len(lines):
                match = ORDERED_RE.match(lines[index].strip())
                if not match:
                    break
                items.append((match.group(1), match.group(2).strip()))
                index += 1
            blocks.append(("ordered_list", items))
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                break
            if candidate == "---" or candidate.startswith(">") or candidate.startswith("|"):
                break
            if HEADING_RE.match(candidate) or BULLET_RE.match(candidate) or ORDERED_RE.match(candidate):
                break
            paragraph_lines.append(candidate)
            index += 1
        blocks.append(("paragraph", " ".join(paragraph_lines)))

    return blocks


def build_story(markdown_text: str, styles: dict[str, ParagraphStyle], fonts: dict[str, str], available_width: float) -> list:
    story = []
    first_h2_seen = False
    blocks = collect_blocks(markdown_text.splitlines())

    for block_type, payload in blocks:
        if block_type == "heading":
            level, text = payload
            if level == 1:
                story.append(Paragraph(markdown_inline_to_rl(text, fonts), styles["cover"]))
                story.append(Spacer(1, 2 * mm))
            elif level == 2:
                if first_h2_seen:
                    story.append(Spacer(1, 3 * mm))
                first_h2_seen = True
                story.append(Paragraph(markdown_inline_to_rl(text, fonts), styles["h2"]))
            elif level == 3:
                story.append(Paragraph(markdown_inline_to_rl(text, fonts), styles["h3"]))
            else:
                story.append(Paragraph(markdown_inline_to_rl(text, fonts), styles["h4"]))
            continue

        if block_type == "meta":
            rows = [[Paragraph(markdown_inline_to_rl(item, fonts), styles["meta"])] for item in payload]
            meta_box = Table(rows, colWidths=[available_width], hAlign="LEFT")
            meta_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                        ("BOX", (0, 0), (-1, -1), 0.5, MID_BG),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(meta_box)
            story.append(Spacer(1, 4 * mm))
            continue

        if block_type == "hr":
            story.append(HRFlowable(width="100%", thickness=0.8, color=MID_BG, spaceBefore=4, spaceAfter=6))
            continue

        if block_type == "table":
            story.append(render_table(payload, styles, fonts, available_width))
            story.append(Spacer(1, 3 * mm))
            continue

        if block_type == "bullet_list":
            for item in payload:
                story.append(Paragraph(f"• {markdown_inline_to_rl(item, fonts)}", styles["bullet"]))
            story.append(Spacer(1, 1 * mm))
            continue

        if block_type == "ordered_list":
            for number, item in payload:
                story.append(Paragraph(f"{number}. {markdown_inline_to_rl(item, fonts)}", styles["bullet"]))
            story.append(Spacer(1, 1 * mm))
            continue

        if block_type == "paragraph":
            story.append(Paragraph(markdown_inline_to_rl(payload, fonts), styles["body"]))
            continue

    return story


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(MID_BG)
    canvas.line(doc.leftMargin, 11 * mm, doc.pagesize[0] - doc.rightMargin, 11 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(doc._font_regular, 8)
    canvas.drawString(doc.leftMargin, 7 * mm, doc._footer_title)
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 7 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def build_pdf(input_path: Path, output_path: Path) -> None:
    fonts = register_fonts()
    styles = build_styles(fonts)
    markdown_text = input_path.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=input_path.stem,
        author="GitHub Copilot",
        allowSplitting=1,
    )
    doc._font_regular = fonts["regular"]
    doc._footer_title = input_path.stem.replace("-", " ").title()

    story = build_story(markdown_text, styles, fonts, doc.width)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a markdown strategy document to PDF.")
    parser.add_argument("input", nargs="?", default=str(DEFAULT_INPUT), help="Path to the markdown input file")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="Path to the output PDF")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input markdown file not found: {input_path}")
    build_pdf(input_path, output_path)
    print(f"Created PDF: {output_path}")


if __name__ == "__main__":
    main()