from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
MARGIN_X = 44
MARGIN_Y = 34
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN_X)

BRAND_RED = HexColor("#9D0000")
BRAND_RED_DARK = HexColor("#7F0000")
BRAND_RED_LIGHT = HexColor("#F4E3E3")
INK = HexColor("#1F1F1F")
SOFT_INK = HexColor("#494949")
OFF_WHITE = HexColor("#FCF7F7")
PANEL = HexColor("#F7EEEE")
GRID = HexColor("#D6B8B8")

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_name: str,
    font_size: float,
    leading: float,
    color,
) -> float:
    lines = simpleSplit(text, font_name, font_size, width)
    pdf.setFillColor(color)
    pdf.setFont(font_name, font_size)
    cursor = y
    for line in lines:
        pdf.drawString(x, cursor, line)
        cursor -= leading
    return cursor


def draw_center_text(
    pdf: canvas.Canvas,
    text: str,
    x_center: float,
    y: float,
    font_name: str,
    font_size: float,
    color,
) -> None:
    pdf.setFont(font_name, font_size)
    pdf.setFillColor(color)
    width = stringWidth(text, font_name, font_size)
    pdf.drawString(x_center - (width / 2), y, text)


def draw_bullet_item(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_name: str,
    font_size: float,
    leading: float,
    text_color,
    bullet_color,
    bullet_radius: float = 3.4,
) -> float:
    pdf.setFillColor(bullet_color)
    pdf.circle(x + bullet_radius, y - (font_size * 0.18), bullet_radius, stroke=0, fill=1)
    return draw_wrapped_text(
        pdf,
        text,
        x + 14,
        y,
        width - 14,
        font_name,
        font_size,
        leading,
        text_color,
    )


def draw_wordmark(pdf: canvas.Canvas, x: float, y: float, size: float) -> None:
    left = "Mee"
    right = "six"
    pdf.setFont(FONT_BOLD, size)
    left_width = stringWidth(left, FONT_BOLD, size)
    pdf.setFillColor(INK)
    pdf.drawString(x, y, left)
    pdf.setFillColor(white)
    pdf.drawString(x + left_width, y, right)


def draw_logo_dice(pdf: canvas.Canvas, x: float, y: float, size: float) -> None:
    top = (x + (size * 0.50), y + (size * 0.88))
    left_top = (x + (size * 0.02), y + (size * 0.63))
    center = (x + (size * 0.50), y + (size * 0.45))
    right_top = (x + (size * 0.98), y + (size * 0.63))
    left_bottom = (x + (size * 0.02), y + (size * 0.21))
    bottom = (x + (size * 0.50), y)
    right_bottom = (x + (size * 0.98), y + (size * 0.21))

    pdf.setLineJoin(1)
    pdf.setLineCap(1)
    pdf.setStrokeColor(INK)
    pdf.setLineWidth(size * 0.024)

    path = pdf.beginPath()
    path.moveTo(*left_top)
    path.lineTo(*top)
    path.lineTo(*right_top)
    path.lineTo(*center)
    path.close()
    pdf.drawPath(path, stroke=1, fill=0)

    path = pdf.beginPath()
    path.moveTo(*left_bottom)
    path.lineTo(*left_top)
    path.lineTo(*center)
    path.lineTo(*bottom)
    path.close()
    pdf.drawPath(path, stroke=1, fill=0)

    path = pdf.beginPath()
    path.moveTo(*bottom)
    path.lineTo(*center)
    path.lineTo(*right_top)
    path.lineTo(*right_bottom)
    path.close()
    pdf.drawPath(path, stroke=1, fill=0)

    top_dots = [
        (x + (size * 0.24), y + (size * 0.73)),
        (x + (size * 0.36), y + (size * 0.81)),
        (x + (size * 0.50), y + (size * 0.86)),
        (x + (size * 0.66), y + (size * 0.80)),
        (x + (size * 0.80), y + (size * 0.73)),
        (x + (size * 0.52), y + (size * 0.61)),
    ]
    side_dots = [
        (x + (size * 0.14), y + (size * 0.42)),
        (x + (size * 0.10), y + (size * 0.22)),
        (x + (size * 0.27), y + (size * 0.29)),
        (x + (size * 0.40), y + (size * 0.36)),
        (x + (size * 0.28), y + (size * 0.10)),
        (x + (size * 0.76), y + (size * 0.42)),
        (x + (size * 0.73), y + (size * 0.24)),
        (x + (size * 0.60), y + (size * 0.14)),
    ]

    pdf.setFillColor(white)
    for dot_x, dot_y in top_dots:
        pdf.circle(dot_x, dot_y, size * 0.024, stroke=0, fill=1)

    pdf.setFillColor(INK)
    for dot_x, dot_y in side_dots:
        pdf.circle(dot_x, dot_y, size * 0.024, stroke=0, fill=1)


def draw_chip(pdf: canvas.Canvas, x: float, y: float, width: float, text: str) -> None:
    pdf.setFillColor(INK)
    pdf.roundRect(x, y, width, 28, 10, stroke=0, fill=1)
    draw_center_text(pdf, text, x + (width / 2), y + 8.5, FONT_BOLD, 10.5, white)


def draw_small_brand(pdf: canvas.Canvas, page_number: int) -> None:
    band_height = 56
    band_y = PAGE_HEIGHT - band_height

    pdf.setFillColor(BRAND_RED)
    pdf.rect(0, band_y, PAGE_WIDTH, band_height, fill=1, stroke=0)
    draw_logo_dice(pdf, MARGIN_X, band_y + 10, 30)
    draw_wordmark(pdf, MARGIN_X + 40, band_y + 16, 18)
    pdf.setFillColor(BRAND_RED_LIGHT)
    pdf.setFont(FONT_BOLD, 10)
    page_label = f"0{page_number}"
    pdf.drawRightString(PAGE_WIDTH - MARGIN_X, band_y + 18, page_label)


def draw_metric_card(pdf: canvas.Canvas, x: float, y: float, width: float, height: float, metric: str, label: str, body: str) -> None:
    pdf.setFillColor(PANEL)
    pdf.roundRect(x, y, width, height, 18, stroke=0, fill=1)
    pdf.setStrokeColor(GRID)
    pdf.setLineWidth(1)
    pdf.roundRect(x, y, width, height, 18, stroke=1, fill=0)

    pdf.setFillColor(BRAND_RED)
    pdf.setFont(FONT_BOLD, 24)
    pdf.drawString(x + 18, y + height - 42, metric)

    label_bottom = draw_wrapped_text(
        pdf,
        label,
        x + 18,
        y + height - 64,
        width - 36,
        FONT_BOLD,
        10.8,
        12,
        INK,
    )

    draw_wrapped_text(pdf, body, x + 18, label_bottom - 10, width - 36, FONT, 10.5, 13, SOFT_INK)


def draw_flow_box(pdf: canvas.Canvas, x: float, y: float, width: float, height: float, number: str, title: str, body: str) -> None:
    pdf.setFillColor(white)
    pdf.roundRect(x, y, width, height, 18, stroke=0, fill=1)
    pdf.setStrokeColor(BRAND_RED_LIGHT)
    pdf.setLineWidth(1.2)
    pdf.roundRect(x, y, width, height, 18, stroke=1, fill=0)

    pdf.setFillColor(BRAND_RED)
    pdf.circle(x + 24, y + height - 24, 12, stroke=0, fill=1)
    draw_center_text(pdf, number, x + 24, y + height - 29, FONT_BOLD, 10, white)

    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(x + 46, y + height - 29, title)

    draw_wrapped_text(pdf, body, x + 18, y + height - 56, width - 36, FONT, 10, 12.5, SOFT_INK)


def draw_outcome_row(pdf: canvas.Canvas, x: float, y: float, width: float, title: str, body: str) -> None:
    pdf.setFillColor(PANEL)
    pdf.roundRect(x, y, width, 58, 14, stroke=0, fill=1)
    pdf.setFillColor(BRAND_RED)
    pdf.circle(x + 18, y + 29, 5.5, stroke=0, fill=1)
    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 11.5)
    pdf.drawString(x + 32, y + 36, title)
    pdf.setFont(FONT, 10)
    pdf.setFillColor(SOFT_INK)
    pdf.drawString(x + 32, y + 20, body)


def cover_page(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(BRAND_RED)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    draw_logo_dice(pdf, 56, 340, 170)
    draw_wordmark(pdf, 255, 430, 52)
    pdf.setFillColor(white)
    pdf.setFont(FONT, 21)
    pdf.drawString(255, 396, "AI agent for marketers")

    headline = "Checks, explains, and approves campaigns before money is spent."
    body = (
        "Meesix is the control layer for paid media launches. It validates campaign settings, "
        "protects attribution hygiene, flags expensive errors before spend goes live, and records "
        "a clean approval trail across Meta, Google Ads, and LinkedIn."
    )
    draw_wrapped_text(pdf, headline, 56, 288, 470, FONT_BOLD, 25, 30, white)
    draw_wrapped_text(pdf, body, 56, 210, 500, FONT, 12.5, 17, OFF_WHITE)

    panel_x = 556
    panel_y = 136
    panel_w = 224
    panel_h = 286
    pdf.setFillColor(INK)
    pdf.roundRect(panel_x, panel_y, panel_w, panel_h, 22, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(panel_x + 20, panel_y + panel_h - 34, "Why buyers care")
    points = [
        "Wrong budgets, geos, dates, or URLs waste real spend.",
        "Broken UTMs and tracking pollute reporting before anyone notices.",
        "Manual QA takes up to 60 to 110 minutes per launch and still misses things.",
        "Approval often lives in scattered Slack messages with no audit trail.",
    ]
    cursor = panel_y + panel_h - 68
    for point in points:
        cursor = draw_bullet_item(
            pdf,
            point,
            panel_x + 22,
            cursor,
            panel_w - 42,
            FONT,
            9.8,
            13.5,
            OFF_WHITE,
            BRAND_RED_LIGHT,
            3.4,
        ) - 10

    chips = [
        "Spend protection",
        "Faster QA",
        "Cleaner attribution",
        "Approval trail",
    ]
    chip_width = 165
    chip_gap = 12
    start_x = 56
    for index, label in enumerate(chips):
        row = index // 2
        col = index % 2
        draw_chip(pdf, start_x + (col * (chip_width + chip_gap)), 98 - (row * 38), chip_width, label)


def problem_page(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(OFF_WHITE)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_small_brand(pdf, 2)

    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 26)
    pdf.drawString(MARGIN_X, PAGE_HEIGHT - 110, "The pain is operational, expensive, and mostly invisible.")
    draw_wrapped_text(
        pdf,
        "Meesix exists because campaign launch quality still depends on manual checklists, tribal knowledge, and hurried review windows. The result is wasted spend, broken tracking, and approval processes nobody can audit later.",
        MARGIN_X,
        PAGE_HEIGHT - 138,
        720,
        FONT,
        11.5,
        15,
        SOFT_INK,
    )

    gap = 16
    card_width = (CONTENT_WIDTH - (2 * gap)) / 3
    card_y = 212
    card_h = 220
    cards = [
        (
            "60–110 min",
            "Manual QA per multi-platform launch",
            "Teams often spend an hour or more checking budgets, targeting, UTMs, schedules, landing pages, and naming conventions before a campaign can go live.",
        ),
        (
            "375–1,125 hrs",
            "Annual QA time per team",
            "That manual review burden can absorb the equivalent of months of skilled campaign manager time every year, even before error costs are counted.",
        ),
        (
            "USD 5–20B",
            "Estimated preventable configuration waste",
            "Misconfigured budgets, geos, scheduling, broken destinations, and corrupted tracking create a hidden but material waste layer across global paid media operations.",
        ),
    ]
    for index, card in enumerate(cards):
        draw_metric_card(pdf, MARGIN_X + (index * (card_width + gap)), card_y, card_width, card_h, *card)

    issue_panel_y = 58
    issue_panel_h = 134
    pdf.setFillColor(BRAND_RED)
    pdf.roundRect(MARGIN_X, issue_panel_y, CONTENT_WIDTH, issue_panel_h, 18, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(MARGIN_X + 20, issue_panel_y + issue_panel_h - 32, "What actually goes wrong")
    bullets = [
        "Budgets are set to the wrong level or against the wrong objective.",
        "Geo targeting and schedules drift from the approved launch plan.",
        "UTM hygiene and tracking setup fail silently, corrupting attribution.",
        "Landing pages break, redirect, or timeout after the ad is already approved.",
    ]
    bullet_x = MARGIN_X + 20
    bullet_y = issue_panel_y + issue_panel_h - 58
    for point in bullets:
        bullet_y = draw_bullet_item(
            pdf,
            point,
            bullet_x,
            bullet_y,
            CONTENT_WIDTH - 40,
            FONT,
            9.8,
            12.2,
            white,
            white,
            3.2,
        ) - 6


def solution_page(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(BRAND_RED)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_small_brand(pdf, 3)

    pdf.setFillColor(white)
    pdf.setFont(FONT_BOLD, 26)
    pdf.drawString(MARGIN_X, PAGE_HEIGHT - 110, "Meesix becomes the control plane before launch.")
    draw_wrapped_text(
        pdf,
        "Instead of relying on a person to remember every check, Meesix runs the campaign through a repeatable read-only validation flow, summarises the result in plain language, and routes a human decision before money is exposed.",
        MARGIN_X,
        PAGE_HEIGHT - 138,
        720,
        FONT,
        11.5,
        15,
        BRAND_RED_LIGHT,
    )

    flow_y = 240
    gap = 16
    box_width = (CONTENT_WIDTH - (2 * gap)) / 3
    flow_boxes = [
        (
            "1",
            "Connect and select",
            "Connect Meta, Google Ads, and LinkedIn in read-only mode, then choose the launch-ready campaign to validate.",
        ),
        (
            "2",
            "Run validation",
            "Check budget, scheduling, geo rules, naming, UTM hygiene, and destination health against the workspace rule set.",
        ),
        (
            "3",
            "Approve with context",
            "Return a pass, warn, or fail verdict, explain every issue clearly, push the summary to Slack, and store the decision trail.",
        ),
    ]
    for index, box in enumerate(flow_boxes):
        draw_flow_box(pdf, MARGIN_X + (index * (box_width + gap)), flow_y, box_width, 150, *box)

    pdf.setFillColor(white)
    pdf.roundRect(MARGIN_X, 64, CONTENT_WIDTH, 124, 18, stroke=0, fill=1)
    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(MARGIN_X + 20, 162, "What the buyer gets")

    row_width = (CONTENT_WIDTH - 58) / 2
    draw_outcome_row(pdf, MARGIN_X + 20, 122, row_width, "Spend protection", "Catch preventable launch errors before budget is spent.")
    draw_outcome_row(pdf, MARGIN_X + 20 + row_width + 18, 122, row_width, "Time compression", "Turn an hour of manual QA into a few minutes of review.")
    draw_outcome_row(pdf, MARGIN_X + 20, 64, row_width, "Attribution integrity", "Protect tracking, naming, and taxonomy before data is corrupted.")
    draw_outcome_row(pdf, MARGIN_X + 20 + row_width + 18, 64, row_width, "Approval accountability", "Create a timestamped record of what was checked and who signed off.")


def fit_page(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(OFF_WHITE)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_small_brand(pdf, 4)

    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 26)
    pdf.drawString(MARGIN_X, PAGE_HEIGHT - 110, "Who it is for and why it wins the first meeting.")

    left_w = 355
    right_x = MARGIN_X + left_w + 24
    right_w = CONTENT_WIDTH - left_w - 24

    pdf.setFillColor(PANEL)
    pdf.roundRect(MARGIN_X, 120, left_w, 300, 18, stroke=0, fill=1)
    pdf.setStrokeColor(GRID)
    pdf.roundRect(MARGIN_X, 120, left_w, 300, 18, stroke=1, fill=0)
    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(MARGIN_X + 20, 392, "Best initial buyers")

    buyer_points = [
        ("Performance marketing agencies", "High campaign volume, repeated launches, many clients, and visible downside when QA fails."),
        ("Mid-market in-house paid media teams", "Multi-platform spend with lean teams that cannot afford waste, delay, or bad attribution."),
        ("Multi-brand e-commerce operators", "Frequent launches and strict naming and tracking conventions make repeatable QA valuable fast."),
    ]
    cursor = 360
    for title, body in buyer_points:
        pdf.setFillColor(BRAND_RED)
        pdf.circle(MARGIN_X + 23, cursor + 2, 4, stroke=0, fill=1)
        pdf.setFillColor(INK)
        pdf.setFont(FONT_BOLD, 11.5)
        pdf.drawString(MARGIN_X + 35, cursor, title)
        cursor = draw_wrapped_text(pdf, body, MARGIN_X + 35, cursor - 16, left_w - 56, FONT, 10.3, 13, SOFT_INK) - 14

    pdf.setFillColor(BRAND_RED)
    pdf.roundRect(right_x, 284, right_w, 136, 18, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont(FONT_BOLD, 14)
    pdf.drawString(right_x + 20, 390, "Positioning line")
    draw_wrapped_text(
        pdf,
        "Meesix prevents paid media teams from shipping broken campaigns by checking, explaining, and approving launches before spend goes live.",
        right_x + 20,
        356,
        right_w - 40,
        FONT_BOLD,
        16,
        21,
        white,
    )

    pdf.setFillColor(white)
    pdf.roundRect(right_x, 120, right_w, 144, 18, stroke=0, fill=1)
    pdf.setStrokeColor(BRAND_RED_LIGHT)
    pdf.roundRect(right_x, 120, right_w, 144, 18, stroke=1, fill=0)
    pdf.setFillColor(INK)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(right_x + 20, 236, "Why the message is stronger than generic \"AI for marketers\"")
    differentiators = [
        "It leads with a concrete operational outcome, not a vague AI claim.",
        "It is anchored to measurable pain: wasted spend, slow QA, broken attribution, weak approval control.",
        "It positions Meesix as risk-control infrastructure rather than another martech dashboard.",
        "It gives buyers a safe adoption path because the MVP stays read-only while still proving value.",
    ]
    cursor = 206
    for point in differentiators:
        cursor = draw_bullet_item(
            pdf,
            point,
            right_x + 20,
            cursor,
            right_w - 40,
            FONT,
            10.2,
            13,
            SOFT_INK,
            BRAND_RED,
            3.4,
        ) - 3


def build_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    pdf.setTitle("Meesix Value Proposition")
    pdf.setAuthor("GitHub Copilot")
    pdf.setSubject("Value proposition overview for Meesix")

    cover_page(pdf)
    pdf.showPage()
    problem_page(pdf)
    pdf.showPage()
    solution_page(pdf)
    pdf.showPage()
    fit_page(pdf)
    pdf.save()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Meesix value proposition PDF.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Business/CONTENT/resources/meesix-value-proposition.pdf"),
        help="Output PDF path",
    )
    args = parser.parse_args()
    build_pdf(args.output)


if __name__ == "__main__":
    main()