"""
Generate agency-closed-won-mcp-plan.pdf using reportlab.
Run once, output lands next to this script, then this script can be deleted.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUTPUT = os.path.join(os.path.dirname(__file__), "agency-closed-won-mcp-plan.pdf")

# ── Palette ──────────────────────────────────────────────────────────────────
DARK      = colors.HexColor("#1A1A2E")
ACCENT    = colors.HexColor("#0F3460")
ACCENT2   = colors.HexColor("#16213E")
LIGHT_ROW = colors.HexColor("#F0F4F8")
MID_ROW   = colors.HexColor("#D9E4F0")
WHITE     = colors.white
RED_LITE  = colors.HexColor("#FDECEA")
GREEN_HDR = colors.HexColor("#0F3460")

# ── Styles ───────────────────────────────────────────────────────────────────
SS = getSampleStyleSheet()

def style(name, **kwargs):
    return ParagraphStyle(name, **kwargs)

TITLE_S = style("Title", fontName="Helvetica-Bold", fontSize=20,
                textColor=WHITE, alignment=TA_LEFT, spaceAfter=6)
SUBTITLE_S = style("Subtitle", fontName="Helvetica", fontSize=11,
                   textColor=colors.HexColor("#AAAACC"), spaceAfter=20)
H1_S = style("H1", fontName="Helvetica-Bold", fontSize=14,
             textColor=ACCENT, spaceBefore=18, spaceAfter=6)
H2_S = style("H2", fontName="Helvetica-Bold", fontSize=11,
             textColor=ACCENT2, spaceBefore=12, spaceAfter=4)
BODY_S = style("Body", fontName="Helvetica", fontSize=9,
               leading=13, textColor=colors.black, spaceAfter=4)
SMALL_S = style("Small", fontName="Helvetica", fontSize=8,
                leading=11, textColor=colors.HexColor("#444444"))
BOLD_S = style("Bold", fontName="Helvetica-Bold", fontSize=9,
               textColor=colors.black)
NOTE_S = style("Note", fontName="Helvetica-Oblique", fontSize=8,
               textColor=colors.HexColor("#555555"), leading=11)
TABLE_HDR = style("TH", fontName="Helvetica-Bold", fontSize=8,
                  textColor=WHITE, alignment=TA_CENTER)
TABLE_CELL = style("TD", fontName="Helvetica", fontSize=8,
                   leading=11, textColor=colors.black)
TABLE_CELL_BOLD = style("TDB", fontName="Helvetica-Bold", fontSize=8,
                        leading=11, textColor=ACCENT2)
TABLE_CELL_READ = style("TDR", fontName="Helvetica", fontSize=8,
                        leading=11, textColor=colors.HexColor("#1A6B3A"))
TABLE_CELL_WRITE = style("TDW", fontName="Helvetica-Bold", fontSize=8,
                         leading=11, textColor=colors.HexColor("#8B0000"))

def th(text): return Paragraph(text, TABLE_HDR)
def td(text): return Paragraph(text, TABLE_CELL)
def tdb(text): return Paragraph(text, TABLE_CELL_BOLD)
def tddir(text, direction):
    if direction == "Read":
        return Paragraph(text, TABLE_CELL_READ)
    return Paragraph(text, TABLE_CELL_WRITE)

BASE_TABLE = TableStyle([
    ("BACKGROUND",  (0, 0), (-1, 0), ACCENT),
    ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",    (0, 0), (-1, 0), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_ROW, WHITE]),
    ("FONTSIZE",    (0, 1), (-1, -1), 8),
    ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
    ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
    ("VALIGN",      (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING",  (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
])

def tool_table(rows, col_widths):
    hdr = [th("Tool"), th("Direction"), th("Description")]
    data = [hdr] + [
        [tdb(r[0]), tddir(r[1], r[1]), td(r[2])]
        for r in rows
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(BASE_TABLE)
    return t

def kv_table(rows, col_widths):
    hdr = [th("Requirement"), th("Detail")]
    data = [hdr] + [[tdb(r[0]), td(r[1])] for r in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(BASE_TABLE)
    return t

def priority_table(rows, col_widths):
    hdr = [th("Phase"), th("Server"), th("Rationale")]
    data = [hdr] + [[td(r[0]), tdb(r[1]), td(r[2])] for r in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(BASE_TABLE)
    return t

# ── Cover band ───────────────────────────────────────────────────────────────
def cover_band():
    data = [[Paragraph("MCP Server Plan\nAgency Closed-Won Onboarding Orchestrator", TITLE_S),
             Paragraph("AgentForge · Engineering · April 2026", SUBTITLE_S)]]
    t = Table(data, colWidths=[14 * cm, 5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("TOPPADDING",  (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t

# ── Build story ───────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.8 * cm,
        title="Agency Closed-Won MCP Server Plan",
        author="AgentForge Engineering",
    )
    W = A4[0] - 3.6 * cm  # usable width

    story = []

    # Cover
    story.append(cover_band())
    story.append(Spacer(1, 0.5 * cm))

    # Strategy
    story.append(Paragraph("Strategy", H1_S))
    story.append(Paragraph(
        "Each MCP server maps to one external system boundary. All servers follow the AgentForge "
        "standard: <b>FastMCP</b> + <b>streamable-http</b>, <b>stateless_http=True</b>, "
        "<b>json_response=True</b>, Dockerized for remote deployment on the WSL2 host. "
        "Every tool is <b>narrow and non-destructive</b> in v1.",
        BODY_S
    ))
    story.append(Spacer(1, 0.3 * cm))

    # ── Server 1 ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6))
    story.append(Paragraph("Server 1 — hubspot-onboarding-mcp", H1_S))
    story.append(Paragraph(
        "<b>Purpose:</b> CRM reads + limited property writes for onboarding status tracking.",
        BODY_S
    ))
    story.append(tool_table([
        ("get_deal",              "Read",  "Fetch deal by ID (amount, stage, owner, close date, service type)"),
        ("get_company",           "Read",  "Fetch associated company record"),
        ("get_contact",           "Read",  "Fetch primary contact for the deal"),
        ("list_closed_won_deals", "Read",  "Poll for recently closed-won deals (trigger source)"),
        ("update_deal_property",  "Write", "Set onboarding status field or add a note — single-property, audit-logged"),
    ], [3.5*cm, 2*cm, W - 5.5*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Auth:</b> OAuth2 private app (scopes: crm.objects.deals.read, crm.objects.companies.read, "
        "crm.objects.contacts.read, crm.objects.deals.write)",
        SMALL_S
    ))
    story.append(Paragraph(
        "<b>Build vs. buy:</b> Community HubSpot MCP servers exist but expose broad admin tools. "
        "<b>Build custom</b> — we need a narrow, onboarding-scoped surface only.",
        SMALL_S
    ))

    # ── Server 2 ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Server 2 — asana-provisioning-mcp", H1_S))
    story.append(Paragraph(
        "<b>Purpose:</b> Create delivery projects and tasks from templates; update safe fields only.",
        BODY_S
    ))
    story.append(tool_table([
        ("create_project_from_template", "Write", "Instantiate a project from a named template with dates and owner"),
        ("create_task",                  "Write", "Add a task to a project with assignee, due date, and section"),
        ("update_task",                  "Write", "Update due date, assignee, or custom field (no delete/archive)"),
        ("get_project_status",           "Read",  "Fetch project completion summary"),
        ("list_project_tasks",           "Read",  "List tasks with statuses for readiness checks"),
    ], [4.5*cm, 2*cm, W - 6.5*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Auth:</b> Service account or OAuth2 (scopes: project/task create + read, no workspace admin)",
        SMALL_S
    ))
    story.append(Paragraph(
        "<b>Build vs. buy:</b> Existing Asana MCP servers are generic CRUD. <b>Build custom</b> — "
        "template-based provisioning needs opinionated logic (template selection rules, date population, owner mapping).",
        SMALL_S
    ))

    # ── Server 3 ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Server 3 — slack-notifications-mcp", H1_S))
    story.append(Paragraph(
        "<b>Purpose:</b> Internal notifications and optional channel creation.",
        BODY_S
    ))
    story.append(tool_table([
        ("post_message",       "Write", "Send a message to a specific channel (internal onboarding updates, reminders)"),
        ("create_channel",     "Write", "Create a client-specific internal channel with a naming convention"),
        ("invite_to_channel",  "Write", "Add assigned team members to the channel"),
        ("get_channel_info",   "Read",  "Check if a channel already exists (idempotency guard)"),
    ], [3.5*cm, 2*cm, W - 5.5*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Auth:</b> Slack Bot Token (scopes: chat:write, channels:manage, channels:read, groups:write)",
        SMALL_S
    ))
    story.append(Paragraph(
        "<b>Build vs. buy:</b> Official Slack MCP server exists but exposes full workspace scope. "
        "<b>Build custom</b> — constrain to notification + channel ops only; no message deletion, no workspace-level admin.",
        SMALL_S
    ))

    # ── Server 4 ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Server 4 — google-workspace-mcp", H1_S))
    story.append(Paragraph(
        "<b>Purpose:</b> Send onboarding emails via Gmail and create kickoff calendar events. "
        "Combined into one server because they share the same Google OAuth boundary.",
        BODY_S
    ))
    story.append(tool_table([
        ("send_template_email",      "Write", "Send a pre-approved email template (onboarding welcome, follow-up, access request) with merge fields"),
        ("create_calendar_event",    "Write", "Create a kickoff meeting with attendees, agenda, and proposed time slots"),
        ("get_calendar_availability","Read",  "Check free/busy for agency-side participants"),
        ("list_sent_emails",         "Read",  "Verify a specific onboarding email was delivered (audit trail)"),
    ], [4.2*cm, 2*cm, W - 6.2*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Auth:</b> Google OAuth2 service account or domain-wide delegation "
        "(scopes: gmail.send, calendar.events, calendar.readonly)",
        SMALL_S
    ))
    story.append(Paragraph(
        "<b>Build vs. buy:</b> Google MCP servers exist but are broad. <b>Build custom</b> — "
        "template-only email sends (no arbitrary compose); scoped calendar ops. Highest-risk MCP "
        "(client-facing emails), must enforce template constraints at the tool level.",
        SMALL_S
    ))

    # ── Server 5 ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Server 5 — billing-status-mcp", H1_S))
    story.append(Paragraph(
        "<b>Purpose:</b> Read-only payment/invoice status. No mutations.",
        BODY_S
    ))
    story.append(tool_table([
        ("get_invoice_status",   "Read", "Fetch invoice status by customer or reference ID"),
        ("get_payment_status",   "Read", "Check whether first payment has been received"),
        ("list_recent_invoices", "Read", "List invoices for a customer within a date range"),
    ], [3.5*cm, 2*cm, W - 5.5*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Auth:</b> Stripe restricted API key (read-only: invoices:read, charges:read) "
        "or Xero OAuth2 (read-only scope)",
        SMALL_S
    ))
    story.append(Paragraph(
        "<b>Build vs. buy:</b> Stripe MCP servers exist but expose charge creation. <b>Build custom</b> — "
        "read-only enforcement must be guaranteed at the tool level. Start with Stripe; add Xero as a v1.5 variant.",
        SMALL_S
    ))

    # ── Cross-cutting ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Cross-Cutting Requirements (All Servers)", H1_S))
    story.append(kv_table([
        ("Tenant isolation",    "Every tool call accepts an explicit tenant_id parameter; no inferred scoping"),
        ("Audit metadata",      "Every response includes action_id, timestamp, tenant_id, and tool_name"),
        ("Idempotency",         "Write tools accept an optional idempotency_key; duplicate calls return the original result"),
        ("structured_output",   "All smolagents connections use structured_output=True"),
        ("Health endpoint",     "Each server exposes /healthz alongside /mcp"),
        ("Transport",           "streamable-http, stateless_http=True, json_response=True"),
        ("Container policy",    "Non-root, read-only FS, no Docker socket, CPU/memory limits, secrets injected at runtime"),
    ], [4*cm, W - 4*cm]))

    # ── Build priority ────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Build Priority", H1_S))
    story.append(priority_table([
        ("Phase 1", "hubspot-onboarding-mcp",    "Trigger source — nothing starts without the deal data"),
        ("Phase 1", "asana-provisioning-mcp",     "Core delivery output — project creation is the first visible internal value"),
        ("Phase 1", "slack-notifications-mcp",    "Lowest risk write surface; immediate internal visibility"),
        ("Phase 2", "google-workspace-mcp",       "Client-facing emails = highest trust requirement; needs template enforcement + approval gates first"),
        ("Phase 2", "billing-status-mcp",         "Read-only, low complexity, but less urgent than the coordination loop"),
    ], [2*cm, 5*cm, W - 7*cm]))

    # ── Open questions ────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6, spaceBefore=14))
    story.append(Paragraph("Open Questions Before Build", H1_S))
    questions = [
        ("1. HubSpot app type",
         "Private app (single-tenant pilot) or public OAuth app (multi-tenant SaaS)? "
         "Private is faster for pilot; public is required for scale."),
        ("2. Asana template strategy",
         "Are templates managed inside Asana natively, or does AgentForge maintain its own "
         "template definitions mapped to Asana structures?"),
        ("3. Gmail sender identity",
         "Does the agent send as a shared agency mailbox, a per-user delegated sender, "
         "or a branded no-reply address?"),
        ("4. Stripe vs. Xero first",
         "Which billing system do the pilot agencies use?"),
        ("5. Approval gate placement",
         "Should approval gates live inside each MCP server (tool-level) or in the agent policy "
         "layer above? Recommendation: policy layer above, with MCP servers enforcing hard "
         "constraints (no destructive tools exist at all)."),
    ]
    for q, a in questions:
        story.append(Paragraph(f"<b>{q}</b>", BODY_S))
        story.append(Paragraph(a, NOTE_S))
        story.append(Spacer(1, 0.15 * cm))

    doc.build(story)
    print(f"PDF written to: {OUTPUT}")

if __name__ == "__main__":
    build()
