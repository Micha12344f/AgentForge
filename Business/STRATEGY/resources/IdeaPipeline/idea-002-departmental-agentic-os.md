# Idea Evaluation: Departmental Agents in Public for SMEs

> **ID**: idea-002
> **Date Created**: 2026-04-09
> **Current Gate**: Gate 2
> **Status**: GO TO GATE 2
> **Kill Reason** (if applicable): -

---

## GATE 0 - Idea Capture

**Problem Statement** (one sentence):
> COOs, founders, and department heads in SMEs lose significant time and margin to fragmented cross-tool execution inside each department because their software stores records but does not reliably run the work.

**Who Has This Problem?**
- Job title / role: Founder, COO, Head of Operations, VP Customer Success, Finance Manager, Head of Sales Ops
- Industry / vertical: B2B SaaS, agencies, consultancies, outsourced service firms, professional services, selected e-commerce operators
- Company size: 20-300 employees
- Estimated number of these people/companies: Large enough UK and European SME base to support a wedge-by-wedge vertical entry strategy

**How Do They Currently Solve It?**
- Status quo solution: CRM + PM tool + Slack/Teams + spreadsheets + email + point tools + ops staff doing manual coordination
- What they pay for it (time and/or money): Headcount cost, delay cost, implementation leakage, missed follow-ups, poor handoffs, slower cash collection, lower retention
- Why the status quo is inadequate: Systems of record exist, but no system of execution owns the workflow end to end across departments

**Why Now?**
- What changed recently (regulation, technology, market shift, macro trend): LLM quality is now good enough for bounded workflow execution; APIs and webhooks are standard; SMEs are under margin pressure and more willing to automate internal ops
- Why this wasn't viable 2 years ago: Model reliability, tool connectivity, and approval-driven agent patterns were weaker and harder to productionise

**Your Unfair Advantage**
- Domain knowledge: Strong focus on workflow decomposition, automation risk, and honest moat assessment
- Existing code/infrastructure: Multi-model routing, orchestration patterns, shared integration clients, approval-oriented agent design principles, PDF/reporting capability
- Relationships/access: Can sell into founder-led and operator-led SME environments through a workflow pain lens and turn early deployments into public proof
- Skills that transfer: Strategy, product framing, orchestration, integration architecture, agent operations

### Entry Criteria Check

| # | Criterion | Pass? | Notes |
|---|-----------|-------|-------|
| 1 | Credible path to B2B/prosumer recurring revenue | Yes | Department-specific SaaS + implementation + expansion revenue |
| 2 | Not dependent on a single platform's TOS | Yes | Strategy requires multi-system integrations, not a single host platform |
| 3 | Plausible path to data moat / network effect / regulatory barrier | Yes | Workflow telemetry, approvals, exception data, templates, and integration depth compound over time |
| 4 | Customer cost of problem > $1,000/year | Yes | Even one department's coordination waste or leakage usually exceeds this threshold |
| 5 | Buildable to MVP in <= 3 months lean | Yes | Only if wedge starts with one department and 3-5 core integrations |

**Gate 0 Decision**: GO TO GATE 1

---

## GATE 1 - Quick Kill Screen

### Market Existence Check

The market exists. This is not a speculative category.

- Capterra lists **115 client onboarding software products** in 2026, confirming dense category demand.
- Rocketlane now markets an **agentic, all-in-one PSA** with Nitro agents across delivery execution, resourcing, and customer intelligence.
- GUIDEcx positions itself around **AI customer onboarding**, transparency, accountability, and faster time-to-value.
- Process Street markets **AI-powered workflows, approvals, and compliance operations** across onboarding, IT, HR, and operations use cases.
- HubSpot continues expanding Service Hub and programmable automation, which validates demand for AI-supported workflow execution inside established systems of record.

**Competitors Found**:

| Competitor | Founded | Funding / Scale Signal | Pricing / Packaging Signal | Notes |
|-----------|---------|------------------------|----------------------------|-------|
| Rocketlane | 2020 | Category leader in onboarding / PSA | Free trial + pricing page | Strongest direct threat; moving hard into agentic delivery |
| GUIDEcx | 2017 | Established onboarding platform | Demo / tour-led | Strong workflow and client transparency story |
| Process Street | 2014 | 1M+ users claim | PLG + enterprise | Broad process platform with approvals and AI |
| HubSpot Service Hub + Data Hub | Incumbent | CRM ecosystem giant | Free to enterprise tiers | Can approximate adjacent workflows via automation |
| Asana / Monday / generic PM tools | Mature incumbents | Large public-company scale | Seat-based SaaS | Status quo alternative for many teams |

**Market Signal Summary**:
- Customer onboarding pain is already budgeted and searched for.
- AI language is now mainstream in adjacent tools, which confirms timing.
- The risk is not absence of demand; the risk is entering a crowded category without a sharp enough wedge.

### Structural Moat Assessment

| # | Moat Dimension | Score (0-2) | Evidence |
|---|---------------|-------------|----------|
| 1 | Winner-take-all dynamics | 1 | Many tools can coexist, but multi-department stacking can create local ecosystem gravity over time |
| 2 | Switching costs | 2 | Once runbooks, approvals, telemetry, and integrations sit inside daily operations, removal is painful |
| 3 | Data advantage | 1 | Workflow traces, exception histories, approval patterns, and template performance can compound into proprietary operational data |
| 4 | Regulatory barrier | 0 | No meaningful barrier at entry beyond standard trust and security requirements |
| 5 | Distribution advantage | 1 | Building in public with real business use cases can create trust, case studies, and speed, but it is not a protected moat by itself |
| **Total** | | **5/10** | |

**Gate 1 Decision**: GO TO GATE 2

**Decision rationale**:
The idea clears Gate 1 because the market is clearly real, the onboarding-first wedge is concrete, and the multi-department expansion path creates credible switching-cost upside. The main weakness is not demand; it is competitive crowding. That makes positioning critical: start with real onboarding use cases, sell outcomes, and use public proof as a distribution lever rather than pretending "build in public" is the moat.

---

## Operating Thesis

The broader business should not start as a generic "AI for the whole company" platform. It should start as a department-specific execution layer, prove ROI, then expand into adjacent departments until it becomes the shared operating system for agentic work.

The sequence is:
1. Win one department with a painful, repetitive, approval-sensitive workflow.
2. Build deep integrations and runbooks in that department.
3. Use the resulting trust, telemetry, and integrations to expand into the next department.
4. Add cross-department orchestration only after two or more departments are live.

This keeps the entry wedge vertical while preserving the bigger end-state you want: a multi-department agentic operating capability for SMEs.

---

## Department Decomposition for SMEs

### 1. Revenue Department

**Functions**: Marketing, sales, revops, proposals, lead routing, CRM hygiene, outreach follow-up

**Agentic opportunities**:
- Lead qualification and routing
- CRM hygiene repair and enrichment
- Proposal and follow-up orchestration
- Meeting prep and account research
- Pipeline risk flagging

**Assessment**:
- Ease to agentify: Medium
- Willingness to pay: High
- Competition density: High
- Expansion value: High because CRM becomes a shared data anchor

### 2. Delivery / Operations Department

**Functions**: Client onboarding, implementation, project coordination, document chase, internal handoffs, status reporting

**Agentic opportunities**:
- Client onboarding operating system
- Project kickoff generation
- Missing-input chase loops
- Internal handoff orchestration
- Delay and risk escalation

**Assessment**:
- Ease to agentify: High
- Willingness to pay: High
- Competition density: Medium
- Expansion value: Very high because it sits between sales, finance, and customer success

### 3. Customer Success / Support Department

**Functions**: Ticket triage, health monitoring, QBR prep, renewal risk detection, escalation routing

**Agentic opportunities**:
- Support triage and drafting
- Renewal and churn risk monitoring
- Customer health summaries
- QBR preparation
- Expansion opportunity surfacing

**Assessment**:
- Ease to agentify: Medium to high
- Willingness to pay: High
- Competition density: High
- Expansion value: High because it links product usage, support, and revenue retention

### 4. Finance Department

**Functions**: Accounts receivable, invoicing, collections, accounts payable, month-end close prep, spend controls

**Agentic opportunities**:
- Invoice chase and collections workflows
- AP coding and approval routing
- Close checklist orchestration
- Exception detection across billing and cash collection
- Procurement intake and approval routing

**Assessment**:
- Ease to agentify: Medium
- Willingness to pay: Very high
- Competition density: Medium
- Expansion value: High because finance touches every department and makes ROI easy to quantify

### 5. People / HR Department

**Functions**: Recruiting coordination, interview scheduling, candidate screening support, employee onboarding, policy administration

**Agentic opportunities**:
- Candidate pipeline coordination
- Interview prep packs
- Offer and document workflows
- New hire onboarding orchestration
- Internal policy Q&A with approval checkpoints

**Assessment**:
- Ease to agentify: Medium
- Willingness to pay: Medium
- Competition density: Medium to high
- Expansion value: Medium

### 6. Legal / Compliance Department

**Functions**: Contract intake, review coordination, vendor due diligence, policy enforcement, data request handling

**Agentic opportunities**:
- Contract intake and triage
- Redline workflow support
- Vendor due diligence coordination
- Policy exception routing
- Audit evidence collection

**Assessment**:
- Ease to agentify: Low to medium
- Willingness to pay: High
- Competition density: Medium
- Expansion value: Medium to high

### 7. Product / Engineering / IT Department

**Functions**: Internal request triage, incident routing, QA coordination, access provisioning, release checklists

**Agentic opportunities**:
- Internal ticket triage
- Release and QA checklist orchestration
- Access provisioning workflows
- Incident summarisation and routing
- Change management support

**Assessment**:
- Ease to agentify: Medium
- Willingness to pay: Medium
- Competition density: Medium
- Expansion value: Medium

---

## Recommended Entry Order

| Rank | Department Wedge | Why Start Here | Risk |
|------|------------------|----------------|------|
| 1 | Delivery / Operations | Structured workflows, visible ROI, cross-functional pain, easier to prove value with approvals and telemetry | Moderate implementation complexity |
| 2 | Finance Ops | Direct ROI, measurable cash impact, strong expansion case | Higher trust and data sensitivity requirements |
| 3 | Customer Success | Strong retention narrative and natural upsell after onboarding | Crowded market and incumbent competition |
| 4 | Revenue Ops | Large budgets and strong integration anchor in CRM | Heavy competition from CRM ecosystems |
| 5 | People Ops | Clear admin pain but weaker budget ownership | Lower urgency in many SMEs |
| 6 | Legal / Compliance | Valuable long-term moat if trust is earned | Slow sales cycles and higher risk of false confidence |
| 7 | Product / IT Ops | Useful adjacency, especially for tech-enabled SMEs | Less universal buyer urgency at the start |

---

## Strategic Position

The old onboarding idea is not discarded. It becomes the first wedge inside a larger platform strategy.

**Reframed positioning**:
- Phase 1: Agentic Client Onboarding OS inside Delivery / Operations
- Phase 2: Finance Ops or Customer Success expansion
- Phase 3: Shared control plane for approvals, telemetry, policy, and cross-department triggers
- Phase 4: Multi-department orchestration across the SME

The company should sell the first product as a department-specific ROI engine, not as a general AI transformation platform. The bigger story is used for roadmap and upsell, not for the initial sale.

---

## Shared Platform That Emerges Over Time

If this strategy works, the common platform layer across departments becomes:
- Shared identity and permission model
- Approval queue for sensitive actions
- Runbook engine for department workflows
- Cross-tool integration layer
- Audit trail and exception history
- Department-level and company-level telemetry
- Cross-department trigger graph

That shared layer is the real long-term moat. The department products are the acquisition wedges that justify building it.

---

## Initial Gate 1 Hypotheses to Test

1. SMEs prefer buying one department-specific agentic product over a broad transformation platform.
2. Delivery / Operations is the easiest first wedge because it has high pain, low ideological resistance, and measurable ROI.
3. Finance is the strongest second wedge because it converts automation into cash impact.
4. Cross-department orchestration becomes attractive only after trust is earned in one department first.
5. The moat comes from execution telemetry, templates, approvals, and integration depth, not generic model access.

---

## Strategic Positioning Rule (Added 2026-04-09)

Generic agent orchestration, prompt wiring, and workflow plumbing are being commoditised by model vendors (Claude managed agents, OpenAI Assistants, etc.) and low-code platforms (n8n, Make, Zapier AI). Do not build a business whose moat depends on these commodity layers.

The durable layer is:
- Department-specific runbooks and exception handling
- Approval logic and audit trails
- Operational telemetry that compounds
- Deep integrations around real workflows
- Cross-department data model and trigger graph

Sell outcomes, not agent infrastructure. Use commodity tooling internally where it helps, but never let it define the product category.

---

## Current Status

This is now the **selected active thesis**. The execution model is: build departmental agents in public with real business use cases, starting with client onboarding inside Delivery / Operations. The Agentic Capability Plan (`directives/Business/agentic-capability-plan.md`) is no longer a generic exploration plan; it is the execution plan for proving this idea in the market.

---

## Immediate Next Steps

1. Lock the Day 1 wedge: onboarding for B2B SaaS / agencies / consultancies with 10+ onboardings per month.
2. Define the exact first workflow: signed deal -> document chase -> kickoff prep -> project creation -> reminders -> status summary.
3. Select the first 3-5 integrations for the initial workspace: HubSpot, Slack, Google Workspace, Asana, email.
4. Start customer discovery with onboarding leaders and operators before writing more product code.
5. Use public build logs, demos, and case studies as the top-of-funnel motion while keeping the product outcome-led.