#!/usr/bin/env python3
"""Generate a viability PDF for every idea in the Strategy idea backlog."""

from __future__ import annotations

import math
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "idea_backlog.db"
OUTPUT_PDF = SCRIPT_DIR / f"Idea_Backlog_Viability_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
CHART_DIR = SCRIPT_DIR / "_idea_backlog_viability_charts"
CHART_DIR.mkdir(exist_ok=True)

NAVY = colors.HexColor("#10243f")
BLUE = colors.HexColor("#1f5b99")
TEAL = colors.HexColor("#127475")
GREEN = colors.HexColor("#2f855a")
AMBER = colors.HexColor("#b7791f")
RED = colors.HexColor("#c53030")
LIGHT_BG = colors.HexColor("#f5f7fa")
MID_BG = colors.HexColor("#e6ecf2")
DARK_TEXT = colors.HexColor("#1a202c")
MUTED = colors.HexColor("#4a5568")

EDGE_PROFILE = {
    "strengths": [
        "Existing multi-agent orchestration stack, multi-LLM routing, memory patterns, and workflow integrations map directly onto agentic AI setup for businesses.",
        "Finance plus Computer Science gives enough business credibility to sell ROI-led workflow systems, not just technical prototypes.",
        "The strongest wedge is setting up, governing, and improving agentic workflows inside existing business tools rather than pitching frontier R&D.",
        "A UK Reading base is viable for SMB and mid-market deployment offers where buyers want practical setup help, faster rollout, and visible time savings.",
    ],
    "constraints": [
        "Graduate-team credibility is weaker for broad transformation programmes, so every offer needs a narrow first workflow and a concrete pilot.",
        "Anything that collapses into generic AI consulting should be penalized; setup, orchestration, QA, and managed agent ops are the defensible layer.",
        "No cybersecurity edge means security-only or infra-hardening offers should stay out of the shortlist.",
        "The first version must show ROI inside 30-60 days, which favors inbox, exception, approval, onboarding, reporting, and knowledge workflows.",
    ],
}

KEYWORD_BUCKETS = {
    "sales": (
        "sales",
        "lead",
        "qualification",
        "meeting",
        "pipeline",
    ),
    "support": (
        "support",
        "ticket",
        "customer support",
        "resolution",
        "escalation",
    ),
    "finance": (
        "finance",
        "controller",
        "close",
        "cfo",
        "approval",
        "cash",
    ),
    "revops": (
        "revops",
        "crm",
        "revenue",
        "handoff",
        "forecast",
    ),
    "people": (
        "people",
        "hr",
        "employee",
        "candidate",
        "onboarding hire",
    ),
    "client_onboarding": (
        "client onboarding",
        "implementation",
        "service delivery",
        "time-to-value",
        "new client",
    ),
    "procurement": (
        "procurement",
        "vendor",
        "supplier",
        "po approvals",
        "purchase",
    ),
    "compliance": (
        "compliance",
        "risk",
        "policy",
        "audit",
        "legal",
        "evidence",
    ),
    "operations": (
        "operations",
        "supply chain",
        "queue",
        "sla",
        "exceptions",
        "ops",
    ),
    "knowledge": (
        "knowledge",
        "chief of staff",
        "reporting",
        "meeting",
        "execution",
        "internal assistant",
    ),
}


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSub",
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            textColor=MUTED,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=24,
            textColor=NAVY,
            spaceBefore=16,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "SubTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=BLUE,
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "IdeaTitle",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=DARK_TEXT,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyTight",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "BulletBody",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
            leftIndent=16,
            bulletIndent=8,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "CenterSmall",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    return styles


def row_to_dict(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {description[0]: row[idx] for idx, description in enumerate(cursor.description)}


def load_ideas() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = [
        dict(row)
        for row in cur.execute(
            """
            SELECT *
            FROM idea_backlog
            ORDER BY mandate_score_10 DESC, founder_fit_rank DESC, pain_est_gbp_year DESC, mvp_weeks ASC, idea_id ASC
            """
        ).fetchall()
    ]
    conn.close()
    return rows


def bucket_for_idea(idea: dict) -> str:
    haystack = " ".join(
        [
            idea["idea_name"],
            idea["sector"],
            idea["target_buyer"],
            idea["moat_path"],
            idea["first_test"],
        ]
    ).lower()
    for bucket, terms in KEYWORD_BUCKETS.items():
        if any(term in haystack for term in terms):
            return bucket
    return "general_b2b"


def bucket_label(bucket: str) -> str:
    labels = {
        "sales": "Sales and Lead Response",
        "support": "Customer Support and Service",
        "finance": "Finance and Approvals",
        "revops": "Revenue Operations and CRM",
        "people": "People Operations",
        "client_onboarding": "Client Onboarding and Delivery",
        "procurement": "Procurement and Vendor Ops",
        "compliance": "Legal, Risk, and Compliance",
        "operations": "Operations and Supply Chain",
        "knowledge": "Executive and Knowledge Ops",
        "general_b2b": "General B2B Workflows",
    }
    return labels.get(bucket, bucket)


def adjacency_score(bucket: str) -> int:
    scores = {
        "sales": 13,
        "support": 13,
        "finance": 15,
        "revops": 14,
        "people": 10,
        "client_onboarding": 14,
        "procurement": 11,
        "compliance": 14,
        "operations": 10,
        "knowledge": 12,
        "general_b2b": 10,
    }
    return scores.get(bucket, 10)


def execution_score(idea: dict) -> int:
    haystack = " ".join(
        [
            idea["idea_name"],
            idea.get("core_problem", ""),
            idea.get("recurring_model", ""),
            idea["first_test"],
            idea["moat_path"],
        ]
    ).lower()
    strong_terms = (
        "orchestration",
        "managed agent ops",
        "observability",
        "approval cockpit",
        "exception",
        "deployment kit",
        "inbox triage",
        "knowledge copilot",
        "reporting layer",
    )
    medium_terms = (
        "rollout blueprint",
        "agentic ai",
        "agent",
        "workflow",
        "setup",
    )
    if any(term in haystack for term in strong_terms):
        return 15
    if any(term in haystack for term in medium_terms):
        return 12
    return 10


def speed_score(mvp_weeks: int) -> int:
    if mvp_weeks <= 4:
        return 10
    if mvp_weeks == 5:
        return 8
    if mvp_weeks == 6:
        return 6
    if mvp_weeks == 7:
        return 4
    return 2


def fit_score(founder_fit: str) -> int:
    return {"High": 20, "Medium": 12, "Low": 5}.get(founder_fit, 8)


def quality_score(mandate_score_10: int) -> int:
    return round((mandate_score_10 / 10) * 40)


def pain_bonus(pain_est_gbp_year: int) -> int:
    if pain_est_gbp_year >= 20000:
        return 10
    if pain_est_gbp_year >= 12000:
        return 7
    return 4


def viability_score(idea: dict) -> int:
    bucket = bucket_for_idea(idea)
    score = 0
    score += quality_score(int(idea["mandate_score_10"]))
    score += fit_score(idea["founder_fit"])
    score += adjacency_score(bucket)
    score += execution_score(idea)
    score += speed_score(int(idea["mvp_weeks"]))
    score += pain_bonus(int(idea["pain_est_gbp_year"]))
    return min(100, score)


def priority_band(score: int) -> str:
    if score >= 90:
        return "Tier 1 - Best fit now"
    if score >= 82:
        return "Tier 2 - Strong shortlist"
    if score >= 72:
        return "Tier 3 - Conditional"
    return "Tier 4 - Lower priority"


def band_color(band: str):
    if band.startswith("Tier 1"):
        return GREEN
    if band.startswith("Tier 2"):
        return TEAL
    if band.startswith("Tier 3"):
        return AMBER
    return RED


def rationale_points(idea: dict) -> list[str]:
    bucket = bucket_for_idea(idea)
    points = []
    if bucket == "finance":
        points.append("Direct overlap with Finance plus CS and a clear line to ROI through faster close, approvals, reporting, and exception handling.")
    elif bucket == "revops":
        points.append("Strong fit for a cross-tool orchestration wedge because RevOps pain already lives between CRM, billing, spreadsheets, and inboxes.")
    elif bucket == "client_onboarding":
        points.append("Onboarding and implementation teams are ideal for agentic setup offers because the before-and-after metrics are visible quickly.")
    elif bucket == "compliance":
        points.append("Agentic setup plus approval trails is stronger than generic AI automation in audit-heavy workflows where control matters as much as speed.")
    else:
        points.append("This is still a business-facing setup offer, not a generic AI product, which keeps it closer to the current orchestration edge.")

    execution_haystack = " ".join([idea["idea_name"], idea.get("core_problem", ""), idea["first_test"]]).lower()
    if any(term in execution_haystack for term in ("triage", "approval", "exception", "orchestration", "knowledge", "reporting", "managed agent ops")):
        points.append("The workflow is a good candidate for agentic AI because it combines routing, retrieval, action-taking, and human oversight instead of simple single-step automation.")
    else:
        points.append("The setup wedge is viable, but the first workflow still needs clear boundaries so it does not become a vague AI transformation project.")

    if "Switching costs" in idea["moat_path"]:
        points.append("The offer gets stronger once agents are wired into the customer's existing tools, approvals, and operating rhythms, creating real switching costs.")
    elif "Counter-positioning" in idea["moat_path"]:
        points.append("A setup-first model can beat big consultancies because it ships actual workflows fast instead of selling large change programmes.")
    else:
        points.append("Defensibility will come from deployment playbooks, managed optimization, and workflow depth more than from raw model access.")

    return points[:3]


def risk_points(idea: dict) -> list[str]:
    bucket = bucket_for_idea(idea)
    points = []
    name = idea["idea_name"].lower()
    if "blueprint" in name:
        points.append("Blueprint and readiness offers can collapse into consulting unless they lead directly into a standardized deployment package.")
    if "orchestration" in name:
        points.append("Cross-tool orchestration is powerful but can sprawl into custom systems work unless the first workflow is tightly bounded.")
    if "observability" in name:
        points.append("Observability is strategically strong but assumes the customer already has live agents worth measuring, so demand may come later in the journey.")
    if bucket == "finance" and any(token in idea["target_buyer"].lower() for token in ("cfo", "controller", "head")):
        points.append("Finance buyers will want visible control and error containment, so human-in-the-loop design matters from day one.")
    if bucket in {"operations", "people"}:
        points.append("These teams can be harder to win early if outcomes are harder to quantify than time saved, throughput, or queue reduction.")
    if int(idea["mvp_weeks"]) >= 8:
        points.append("MVP scope is at the top end of the 3-month limit, so it should be narrowed before any build decision.")
    if idea["founder_fit"] != "High":
        points.append("Founder fit is not top-tier, so warm introductions or a sharper functional niche may matter more here than in finance-adjacent offers.")
    if not points:
        points.append("Main risk is go-to-market focus: if the setup offer is too broad, it drifts back toward a generic AI agency with weak differentiation.")
    return points[:3]


def recommendation_line(idea: dict, score: int) -> str:
    band = priority_band(score)
    if band.startswith("Tier 1"):
        return "Strong immediate candidate. Worth turning into a concrete agentic AI deployment offer and a real pilot design now."
    if band.startswith("Tier 2"):
        return "Good shortlist candidate. Keep it live, but narrow the buyer, first workflow, and integration scope before deeper research."
    if band.startswith("Tier 3"):
        return "Conditional candidate. Only pursue if a warm intro, customer signal, or clearer deployment package materially reduces sales risk."
    return "Lower-priority candidate. Keep it in the backlog, but do not spend real build time on it before stronger agentic-setup wedges are exhausted."


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(doc.pagesize[0] - 16 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def chart_score_distribution(ideas: list[dict]) -> Path:
    scores = [idea["viability_score"] for idea in ideas]
    plt.figure(figsize=(7.2, 3.8))
    plt.hist(scores, bins=[60, 68, 76, 84, 92, 100], color="#1f5b99", edgecolor="white")
    plt.title("Viability Score Distribution", fontsize=13, fontweight="bold")
    plt.xlabel("Composite viability score")
    plt.ylabel("Ideas")
    plt.grid(alpha=0.25)
    path = CHART_DIR / "01_score_distribution.png"
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def chart_priority_mix(ideas: list[dict]) -> Path:
    counter = Counter(idea["priority_band"] for idea in ideas)
    ordered = [
        "Tier 1 - Best fit now",
        "Tier 2 - Strong shortlist",
        "Tier 3 - Conditional",
        "Tier 4 - Lower priority",
    ]
    values = [counter.get(label, 0) for label in ordered]
    colors_list = ["#2f855a", "#127475", "#b7791f", "#c53030"]
    plt.figure(figsize=(7.2, 3.8))
    bars = plt.bar(ordered, values, color=colors_list, edgecolor="white")
    plt.title("Priority Mix Across the 100-Idea Backlog", fontsize=13, fontweight="bold")
    plt.ylabel("Ideas")
    plt.xticks(rotation=15, ha="right")
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, value + 0.5, str(value), ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", alpha=0.25)
    path = CHART_DIR / "02_priority_mix.png"
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def chart_bucket_scores(ideas: list[dict]) -> Path:
    buckets = defaultdict(list)
    for idea in ideas:
        buckets[bucket_label(idea["macro_bucket"])] .append(idea["viability_score"])
    ordered = sorted(((bucket, sum(values) / len(values), len(values)) for bucket, values in buckets.items()), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in ordered]
    values = [item[1] for item in ordered]
    counts = [item[2] for item in ordered]
    plt.figure(figsize=(7.2, 4.6))
    bars = plt.barh(labels, values, color="#127475", edgecolor="white")
    plt.title("Average Viability Score by Macro Bucket", fontsize=13, fontweight="bold")
    plt.xlabel("Average score")
    plt.xlim(60, 100)
    for bar, count, value in zip(bars, counts, values):
        plt.text(value + 0.4, bar.get_y() + bar.get_height() / 2, f"n={count}", va="center", fontsize=8)
    plt.grid(axis="x", alpha=0.25)
    path = CHART_DIR / "03_bucket_scores.png"
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def score_kpi_table(styles, ideas: list[dict]) -> Table:
    tier_counts = Counter(idea["priority_band"] for idea in ideas)
    data = [
        [
            Paragraph("<b>Ideas Screened</b>", styles["CenterSmall"]),
            Paragraph("<b>Tier 1</b>", styles["CenterSmall"]),
            Paragraph("<b>Tier 2</b>", styles["CenterSmall"]),
            Paragraph("<b>Avg Score</b>", styles["CenterSmall"]),
        ],
        [
            Paragraph(f"<b>{len(ideas)}</b>", styles["SubTitle"]),
            Paragraph(f"<b>{tier_counts.get('Tier 1 - Best fit now', 0)}</b>", styles["SubTitle"]),
            Paragraph(f"<b>{tier_counts.get('Tier 2 - Strong shortlist', 0)}</b>", styles["SubTitle"]),
            Paragraph(f"<b>{sum(idea['viability_score'] for idea in ideas) / len(ideas):.1f}</b>", styles["SubTitle"]),
        ],
    ]
    table = Table(data, colWidths=[42 * mm, 35 * mm, 35 * mm, 35 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), MID_BG),
                ("BACKGROUND", (0, 1), (-1, 1), LIGHT_BG),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def rank_table(styles, ideas: list[dict], limit: int = 15) -> Table:
    rows = [["Rank", "Idea", "Bucket", "Score", "Band"]]
    for index, idea in enumerate(ideas[:limit], start=1):
        rows.append(
            [
                str(index),
                Paragraph(f"<b>{idea['idea_name']}</b><br/>{idea['target_buyer']}", styles["BodyTight"]),
                Paragraph(bucket_label(idea["macro_bucket"]), styles["BodyTight"]),
                str(idea["viability_score"]),
                Paragraph(idea["priority_band"], styles["BodyTight"]),
            ]
        )
    table = Table(rows, colWidths=[12 * mm, 74 * mm, 40 * mm, 16 * mm, 38 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def idea_card(styles, idea: dict) -> list:
    band = idea["priority_band"]
    band_hex = band_color(band).hexval()
    title = (
        f"<b>{idea['rank']}. {idea['idea_name']}</b> "
        f"<font color='{band_hex}'>[{band}]</font>"
    )
    metrics = Table(
        [
            ["Idea ID", idea["idea_id"], "Score", str(idea["viability_score"])],
            ["Bucket", bucket_label(idea["macro_bucket"]), "Founder fit", idea["founder_fit"]],
            ["Pain", f"GBP {idea['pain_est_gbp_year']:,}/yr", "MVP", f"{idea['mvp_weeks']} weeks"],
            ["Buyer", idea["target_buyer"], "Recurring", idea.get("recurring_model", "")],
            ["Integrations", idea.get("integration_anchor", ""), "Moat path", idea["moat_path"]],
        ],
        colWidths=[18 * mm, 62 * mm, 16 * mm, 62 * mm],
    )
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("TEXTCOLOR", (0, 0), (-1, -1), DARK_TEXT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story = [Paragraph(title, styles["IdeaTitle"]), metrics, Spacer(1, 4)]
    story.append(Paragraph(f"<b>Core problem:</b> {idea.get('core_problem', '')}", styles["BodyTight"]))
    story.append(Paragraph("<b>Why it fits our edge</b>", styles["Small"]))
    for point in idea["rationale_points"]:
        story.append(Paragraph(point, styles["BulletBody"], bulletText="-"))
    story.append(Paragraph("<b>Main risks</b>", styles["Small"]))
    for point in idea["risk_points"]:
        story.append(Paragraph(point, styles["BulletBody"], bulletText="-"))
    story.append(Paragraph(f"<b>Recommendation:</b> {idea['recommendation']}", styles["BodyTight"]))
    story.append(Paragraph(f"<b>First test:</b> {idea['first_test']}", styles["BodyTight"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d6dde6"), spaceBefore=2, spaceAfter=8))
    return story


def enrich_ideas(ideas: list[dict]) -> list[dict]:
    enriched = []
    for raw in ideas:
        idea = dict(raw)
        idea["macro_bucket"] = bucket_for_idea(idea)
        idea["viability_score"] = viability_score(idea)
        idea["priority_band"] = priority_band(idea["viability_score"])
        idea["rationale_points"] = rationale_points(idea)
        idea["risk_points"] = risk_points(idea)
        idea["recommendation"] = recommendation_line(idea, idea["viability_score"])
        enriched.append(idea)
    enriched.sort(key=lambda item: (-item["viability_score"], -item["mandate_score_10"], item["mvp_weeks"], item["idea_id"]))
    for index, idea in enumerate(enriched, start=1):
        idea["rank"] = index
    return enriched


def build_pdf(ideas: list[dict]):
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Agentic AI Setup Backlog Viability Report",
        author="GitHub Copilot",
    )

    score_chart = chart_score_distribution(ideas)
    mix_chart = chart_priority_mix(ideas)
    bucket_chart = chart_bucket_scores(ideas)

    tier_counts = Counter(idea["priority_band"] for idea in ideas)
    strongest_buckets = Counter(bucket_label(idea["macro_bucket"]) for idea in ideas[:20]).most_common(4)
    story = []

    story.append(Paragraph("Agentic AI Setup Backlog Viability Report", styles["CoverTitle"]))
    story.append(Paragraph("100 business-facing agentic AI setup offers screened against the current team edge.", styles["CoverSub"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y')} | Source: idea_backlog.db | Scope: Gate 0 / edge-based viability screen", styles["Small"]))
    story.append(Spacer(1, 10))
    story.append(score_kpi_table(styles, ideas))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Method", styles["SectionTitle"]))
    story.append(
        Paragraph(
            "This report is not full market diligence on all 100 ideas. It is a disciplined Gate 0 viability screen based on the current founder edge: Finance plus CS background, existing multi-agent orchestration infrastructure, UK location, graduate-team credibility limits, and a thesis that the most credible wedge is agentic AI setup for business workflows. Each idea is scored for mandate quality, founder fit, adjacency to that edge, execution pattern, launch speed, and problem pain.",
            styles["BodyTight"],
        )
    )
    story.append(Paragraph("Current edge strengths", styles["SubTitle"]))
    for line in EDGE_PROFILE["strengths"]:
        story.append(Paragraph(line, styles["BulletBody"], bulletText="-"))
    story.append(Paragraph("Current edge constraints", styles["SubTitle"]))
    for line in EDGE_PROFILE["constraints"]:
        story.append(Paragraph(line, styles["BulletBody"], bulletText="-"))
    story.append(PageBreak())

    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    summary = (
        f"The backlog contains <b>{tier_counts.get('Tier 1 - Best fit now', 0)}</b> Tier 1 ideas and "
        f"<b>{tier_counts.get('Tier 2 - Strong shortlist', 0)}</b> Tier 2 ideas. The strongest concentration sits in agentic setup offers for finance, revops, onboarding, compliance, and support where the team can deploy cross-tool workflows quickly and defend them through integration depth, managed optimization, and human-in-the-loop control. The weakest ideas are the ones that look too much like generic consulting or need large enterprise trust before proving ROI."
    )
    story.append(Paragraph(summary, styles["BodyTight"]))
    story.append(Paragraph("Best-performing clusters in the current shortlist:", styles["BodyTight"]))
    for name, count in strongest_buckets:
        story.append(Paragraph(f"{name} appears {count} times in the top 20 ranked ideas.", styles["BulletBody"], bulletText="-"))
    story.append(Spacer(1, 6))
    story.append(Image(str(score_chart), width=82 * mm, height=44 * mm))
    story.append(Spacer(1, 6))
    story.append(Image(str(mix_chart), width=82 * mm, height=44 * mm))
    story.append(Spacer(1, 6))
    story.append(Image(str(bucket_chart), width=82 * mm, height=50 * mm))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Top 15 agentic AI setup ideas to investigate first", styles["SubTitle"]))
    story.append(rank_table(styles, ideas, limit=15))
    story.append(PageBreak())

    story.append(Paragraph("Full Idea-by-Idea Screen", styles["SectionTitle"]))
    story.append(
        Paragraph(
            "Each card below is a viability note based on our edge today. It should be read as a prioritization layer for what deserves a full Gate 0 or Gate 1 write-up next, not as a substitute for real market research.",
            styles["BodyTight"],
        )
    )
    story.append(Spacer(1, 4))

    for idea in ideas:
        story.extend(idea_card(styles, idea))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Idea backlog database not found: {DB_PATH}")
    ideas = enrich_ideas(load_ideas())
    build_pdf(ideas)
    print(f"Generated PDF: {OUTPUT_PDF}")
    print(f"Ideas included: {len(ideas)}")


if __name__ == "__main__":
    main()