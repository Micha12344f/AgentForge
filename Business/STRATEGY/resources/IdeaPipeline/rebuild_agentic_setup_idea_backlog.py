#!/usr/bin/env python3
"""Rebuild the Strategy idea backlog around agentic AI setup offers for businesses."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "idea_backlog.db"

FIT_RANK = {"High": 3, "Medium": 2, "Low": 1}

FUNCTIONS = [
    {
        "label": "Sales Teams",
        "sector": "Sales",
        "buyer": "Head of Sales or Sales Operations Manager",
        "pain": "lead response, qualification, and follow-up work still lives across inboxes, CRM queues, and calendars",
        "tools": "HubSpot or Salesforce + Gmail/Outlook + calendar + Slack",
        "queue": "lead qualification and follow-up queue",
        "roi_metric": "response speed, meeting conversion, and manual hours saved",
        "founder_fit": "High",
        "pain_base": 22000,
        "score_bias": 1,
    },
    {
        "label": "Customer Support Teams",
        "sector": "Customer Support",
        "buyer": "Head of Support or Support Operations Manager",
        "pain": "ticket triage, escalation, and follow-up work stays manual across support queues and internal teams",
        "tools": "Zendesk or Intercom + knowledge base + Slack",
        "queue": "support routing and escalation queue",
        "roi_metric": "first response time, escalation accuracy, and resolution throughput",
        "founder_fit": "High",
        "pain_base": 20000,
        "score_bias": 1,
    },
    {
        "label": "Finance Teams",
        "sector": "Finance Operations",
        "buyer": "Financial Controller or CFO",
        "pain": "close, approvals, cash tasks, and exception handling still depend on spreadsheets and inboxes",
        "tools": "Xero or NetSuite + email + spreadsheets + Slack",
        "queue": "close, approval, and finance exception queue",
        "roi_metric": "faster close, lower error rate, and reduced manual exception handling",
        "founder_fit": "High",
        "pain_base": 25000,
        "score_bias": 2,
    },
    {
        "label": "Revenue Operations Teams",
        "sector": "Revenue Operations",
        "buyer": "RevOps Lead or Revenue Systems Manager",
        "pain": "CRM hygiene, handoffs, and pipeline operations degrade because no one owns repetitive cross-tool work",
        "tools": "HubSpot or Salesforce + billing system + spreadsheets + Slack",
        "queue": "CRM handoff and pipeline exception queue",
        "roi_metric": "cleaner pipeline, fewer dropped handoffs, and better forecast confidence",
        "founder_fit": "High",
        "pain_base": 21000,
        "score_bias": 2,
    },
    {
        "label": "People Operations Teams",
        "sector": "People Operations",
        "buyer": "Head of People Operations",
        "pain": "candidate, onboarding, and employee service workflows are repetitive and fragmented across tools",
        "tools": "HiBob or Workday + email + docs + Slack",
        "queue": "people operations request and onboarding queue",
        "roi_metric": "faster onboarding, lower admin burden, and better SLA adherence",
        "founder_fit": "Medium",
        "pain_base": 15000,
        "score_bias": 0,
    },
    {
        "label": "Client Onboarding Teams",
        "sector": "Client Onboarding",
        "buyer": "COO or Head of Implementation",
        "pain": "new client setup requires repetitive document chase, task routing, and follow-up across systems",
        "tools": "CRM + Asana/Jira + shared docs + email",
        "queue": "new client setup and handoff queue",
        "roi_metric": "shorter time-to-value, fewer setup errors, and lower onboarding drag",
        "founder_fit": "High",
        "pain_base": 22000,
        "score_bias": 2,
    },
    {
        "label": "Procurement and Vendor Ops Teams",
        "sector": "Procurement and Vendor Ops",
        "buyer": "Procurement Operations Manager or Finance Director",
        "pain": "vendor onboarding, PO approvals, and supplier follow-up work is still manual across inbox and ERP",
        "tools": "ERP + contract store + email + Slack",
        "queue": "vendor onboarding and approval queue",
        "roi_metric": "faster vendor onboarding, better approval speed, and reduced chase work",
        "founder_fit": "Medium",
        "pain_base": 18000,
        "score_bias": 1,
    },
    {
        "label": "Legal and Compliance Teams",
        "sector": "Legal and Compliance",
        "buyer": "Head of Compliance, Risk Manager, or General Counsel",
        "pain": "approvals, evidence gathering, and policy workflows remain fragmented and audit-heavy",
        "tools": "SharePoint or Google Drive + Outlook + policy docs + Slack",
        "queue": "compliance evidence and policy workflow queue",
        "roi_metric": "faster audit prep, cleaner approvals, and better evidence traceability",
        "founder_fit": "High",
        "pain_base": 24000,
        "score_bias": 2,
    },
    {
        "label": "Operations and Supply Chain Teams",
        "sector": "Operations and Supply Chain",
        "buyer": "Operations Director or Supply Chain Manager",
        "pain": "exceptions, supplier coordination, and queue management still depend on human chase work",
        "tools": "ERP + WMS/TMS + email + Teams",
        "queue": "operations exception and coordination queue",
        "roi_metric": "lower queue time, better SLA adherence, and fewer manual escalations",
        "founder_fit": "Medium",
        "pain_base": 20000,
        "score_bias": 1,
    },
    {
        "label": "Executive and Knowledge Ops Teams",
        "sector": "Executive and Knowledge Ops",
        "buyer": "COO, Chief of Staff, or Operations Lead",
        "pain": "knowledge, reporting, and action follow-through are scattered across meetings, docs, and chat",
        "tools": "Notion or Confluence + Drive + Slack + calendar",
        "queue": "meeting follow-through and reporting queue",
        "roi_metric": "better follow-through, faster reporting, and less time lost to context hunting",
        "founder_fit": "High",
        "pain_base": 17000,
        "score_bias": 1,
    },
]

PATTERNS = [
    {
        "name": "Agentic AI Rollout Blueprint for {function_label}",
        "focus": "readiness mapping, workflow selection, and agent rollout design",
        "recurring_model": "Fixed-fee deployment blueprint plus quarterly optimization retainer",
        "moat_path": "Counter-positioning + process power",
        "mvp_weeks": 2,
        "pain_delta": 0,
        "score_bias": -1,
        "first_test": "Run a 2-week readiness sprint for one {function_short} team and define the first 3 automatable workflows with ROI estimates.",
    },
    {
        "name": "Agentic Inbox Triage Stack for {function_label}",
        "focus": "routing, summarization, first action, and escalation",
        "recurring_model": "Setup fee plus monthly managed workflow subscription",
        "moat_path": "Switching costs + workflow integration",
        "mvp_weeks": 4,
        "pain_delta": 1500,
        "score_bias": 1,
        "first_test": "Deploy supervised triage on one live {queue} and compare {roi_metric} over 2 weeks.",
    },
    {
        "name": "SOP-to-Agent Deployment Kit for {function_label}",
        "focus": "turning SOPs into executable agent flows with approvals and handoffs",
        "recurring_model": "Deployment fee plus seat or workflow subscription",
        "moat_path": "Switching costs + process power",
        "mvp_weeks": 5,
        "pain_delta": 1000,
        "score_bias": 1,
        "first_test": "Convert 3 existing SOPs into agent workflows and measure cycle time, exception rate, and human review load.",
    },
    {
        "name": "Agentic Knowledge Copilot for {function_label}",
        "focus": "retrieval, answer drafting, and next-action suggestion against live knowledge sources",
        "recurring_model": "Workspace subscription plus monthly tuning retainer",
        "moat_path": "Switching costs + data asset",
        "mvp_weeks": 4,
        "pain_delta": 500,
        "score_bias": 1,
        "first_test": "Connect the copilot to one live knowledge base and track answer acceptance, escalation rate, and time saved.",
    },
    {
        "name": "Human-in-the-Loop Agent Approval Cockpit for {function_label}",
        "focus": "agent recommendations with approval thresholds, routing logic, and audit trails",
        "recurring_model": "Platform subscription plus implementation fee",
        "moat_path": "Switching costs + governance barrier",
        "mvp_weeks": 6,
        "pain_delta": 2000,
        "score_bias": 1,
        "first_test": "Run one approval workflow with human review for 2 weeks and compare turnaround time, override rate, and queue depth.",
    },
    {
        "name": "Agentic Exception Resolution Stack for {function_label}",
        "focus": "detecting, diagnosing, and routing exceptions before they become manual fire drills",
        "recurring_model": "Usage-based subscription plus monitoring retainer",
        "moat_path": "Switching costs + process power",
        "mvp_weeks": 6,
        "pain_delta": 2500,
        "score_bias": 1,
        "first_test": "Monitor one high-volume exception workflow and compare resolution speed, escalation quality, and human time saved.",
    },
    {
        "name": "Agentic Reporting Layer for {function_label}",
        "focus": "assembling updates, explaining variances, and drafting next actions from live systems",
        "recurring_model": "Monthly reporting subscription plus setup fee",
        "moat_path": "Switching costs + proprietary workflow data",
        "mvp_weeks": 5,
        "pain_delta": 1000,
        "score_bias": 1,
        "first_test": "Generate one weekly or monthly reporting pack for 4 cycles and compare prep time, action quality, and manager satisfaction.",
    },
    {
        "name": "Cross-Tool Agent Orchestration for {function_label}",
        "focus": "moving work across existing tools without forcing a rip-and-replace",
        "recurring_model": "Platform subscription plus managed integration fee",
        "moat_path": "Switching costs + counter-positioning",
        "mvp_weeks": 7,
        "pain_delta": 3000,
        "score_bias": 2,
        "first_test": "Automate one cross-tool workflow spanning 3 systems and track cycle-time reduction, handoff accuracy, and human intervention rate.",
    },
    {
        "name": "Agent QA and Observability Layer for {function_label}",
        "focus": "measuring agent quality, failure modes, routing performance, and human override patterns",
        "recurring_model": "Monthly QA subscription plus implementation fee",
        "moat_path": "Process power + cornered resource",
        "mvp_weeks": 7,
        "pain_delta": 1500,
        "score_bias": 2,
        "first_test": "Instrument one active agent workflow and publish weekly quality, failure, and handoff dashboards for 30 days.",
    },
    {
        "name": "Managed Agent Ops for {function_label}",
        "focus": "ongoing tuning, prompt changes, failure triage, and new workflow rollout after deployment",
        "recurring_model": "Monthly managed service retainer with setup fee",
        "moat_path": "Switching costs + process power",
        "mvp_weeks": 4,
        "pain_delta": 2000,
        "score_bias": 2,
        "first_test": "Take over one live agent workflow for 30 days and compare uptime, output quality, and iteration speed against the prior baseline.",
    },
]


def mandate_score(founder_fit: str, pain_est_gbp_year: int, mvp_weeks: int, moat_path: str, function_bias: int, pattern_bias: int) -> int:
    score = 5
    if founder_fit == "High":
        score += 1
    if pain_est_gbp_year >= 22000:
        score += 1
    if mvp_weeks <= 5:
        score += 1
    if any(term in moat_path for term in ("Switching costs", "Counter-positioning", "cornered resource", "governance barrier", "proprietary workflow data", "Process power")):
        score += 1
    if function_bias >= 2:
        score += 1
    if pattern_bias >= 2:
        score += 1
    return max(6, min(9, score))


def build_rows() -> list[dict]:
    rows = []
    idea_index = 1
    for function in FUNCTIONS:
        function_short = function["label"].replace(" Teams", "").replace(" and ", " ").lower()
        for pattern in PATTERNS:
            pain_est = function["pain_base"] + pattern["pain_delta"]
            mvp_weeks = min(8, pattern["mvp_weeks"] + (0 if function["founder_fit"] == "High" else 1))
            rows.append(
                {
                    "idea_id": f"seed-{idea_index:03d}",
                    "idea_name": pattern["name"].format(function_label=function["label"]),
                    "sector": f"Agentic AI Setup - {function['sector']}",
                    "target_buyer": function["buyer"],
                    "core_problem": (
                        f"{function['buyer']} struggles to roll out agentic AI into {function['label'].lower()} because "
                        f"{function['pain']} and there is no reliable layer for {pattern['focus'].lower()}."
                    ),
                    "recurring_model": pattern["recurring_model"],
                    "integration_anchor": function["tools"],
                    "moat_path": pattern["moat_path"],
                    "founder_fit": function["founder_fit"],
                    "founder_fit_rank": FIT_RANK[function["founder_fit"]],
                    "pain_est_gbp_year": pain_est,
                    "mvp_weeks": mvp_weeks,
                    "mandate_score_10": mandate_score(
                        function["founder_fit"],
                        pain_est,
                        mvp_weeks,
                        pattern["moat_path"],
                        function["score_bias"],
                        pattern["score_bias"],
                    ),
                    "first_test": pattern["first_test"].format(
                        function_short=function_short,
                        queue=function["queue"],
                        roi_metric=function["roi_metric"],
                    ),
                }
            )
            idea_index += 1
    return rows


def rebuild_db(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS idea_backlog;
        DROP VIEW IF EXISTS v_top_ideas;

        CREATE TABLE idea_backlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id TEXT NOT NULL UNIQUE,
            idea_name TEXT NOT NULL,
            sector TEXT NOT NULL,
            target_buyer TEXT NOT NULL,
            core_problem TEXT NOT NULL,
            recurring_model TEXT NOT NULL,
            integration_anchor TEXT NOT NULL,
            moat_path TEXT NOT NULL,
            founder_fit TEXT NOT NULL,
            founder_fit_rank INTEGER NOT NULL,
            pain_est_gbp_year INTEGER NOT NULL,
            mvp_weeks INTEGER NOT NULL,
            mandate_score_10 INTEGER NOT NULL,
            first_test TEXT NOT NULL
        );

        CREATE INDEX idx_idea_backlog_sector ON idea_backlog(sector);
        CREATE INDEX idx_idea_backlog_score ON idea_backlog(mandate_score_10 DESC);
        CREATE INDEX idx_idea_backlog_fit_rank ON idea_backlog(founder_fit_rank DESC);

        CREATE VIEW v_top_ideas AS
        SELECT *
        FROM idea_backlog
        ORDER BY mandate_score_10 DESC, founder_fit_rank DESC, pain_est_gbp_year DESC, mvp_weeks ASC, idea_id ASC;
        """
    )
    cur.executemany(
        """
        INSERT INTO idea_backlog (
            idea_id, idea_name, sector, target_buyer, core_problem,
            recurring_model, integration_anchor, moat_path, founder_fit,
            founder_fit_rank, pain_est_gbp_year, mvp_weeks, mandate_score_10, first_test
        ) VALUES (
            :idea_id, :idea_name, :sector, :target_buyer, :core_problem,
            :recurring_model, :integration_anchor, :moat_path, :founder_fit,
            :founder_fit_rank, :pain_est_gbp_year, :mvp_weeks, :mandate_score_10, :first_test
        )
        """,
        rows,
    )
    conn.commit()
    conn.close()


def main() -> None:
    rows = build_rows()
    if len(rows) != 100:
        raise RuntimeError(f"Expected 100 ideas, got {len(rows)}")
    rebuild_db(rows)
    print(f"Rebuilt {DB_PATH.name} with {len(rows)} agentic AI setup ideas.")


if __name__ == "__main__":
    main()