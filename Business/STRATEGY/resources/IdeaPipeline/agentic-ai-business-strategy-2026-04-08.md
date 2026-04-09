# AGENTIC AI BUSINESS STRATEGY — FULL PLAN

> **Author**: Strategy Agent (Orchestrator-routed)
> **Date**: 8 April 2026
> **Location**: London / Reading, UK
> **Founders**: Two graduate students (Finance + Computer Science), graduating July 2026
> **Governing document**: `directives/Business/idea-mandate-memo.md`
> **Status**: Gate 0–2 Composite — Three ideas evaluated to comparable depth

---

## 1. Summary

This document evaluates three business ideas centred on agentic AI — autonomous software agents that plan, act, and learn inside business workflows. Each idea is assessed against the Hedge Edge Idea Mandate Memo's four objectives (structural moat ≥ 6/10, platform independence, stable retention, commercial defensibility) and three hard constraints (no single-point dependency, B2C churn ceiling, workflow integration requirement).

The three ideas are:

| # | Idea | Core Buyer | Revenue Model |
|---|------|-----------|---------------|
| **1** | **Agentic Client Onboarding OS** | COO / Head of Ops at B2B SaaS, agencies, consultancies (20–300 employees) | Setup fee + monthly managed ops |
| **2** | **Agentic Support Resolution Platform** | VP Support / CX at mid-market B2B/B2C companies | Monthly platform + success-based |
| **3** | **AgentOps Control Plane for Mid-Market** | VP Engineering / Head of AI at companies running 3–20 agent workflows | Monthly SaaS |

**Recommended path**: Build Idea 1 first (strongest first-sale economics and clearest founder fit), expand into Idea 3 once deployment data compounds (strongest long-term moat). Idea 2 is viable but crowded — better as a feature of Idea 1's expansion than a standalone entry.

---

## 2. Market Context: The Agentic AI Opportunity

### The adoption gap is the business

McKinsey's State of AI 2025 survey (n = 1,993; field dates June–July 2025) establishes the core market signal:

- **88%** of respondents say their organisations use AI in at least one business function (up from 78% a year prior)
- **62%** are at least experimenting with AI agents
- **Only 23%** have scaled an agentic system somewhere in their enterprise
- In any given function, **no more than 10%** of respondents report scaling AI agents
- **Nearly two-thirds** have not begun scaling AI across the enterprise
- The strongest predictor of value capture is **workflow redesign**, not model sophistication
- AI high performers are **3x more likely** to fundamentally redesign individual workflows and **3x more likely** to scale agents across functions

(Source: McKinsey & Company, "The state of AI in 2025: Agents, innovation, and transformation," November 2025)

**Translation**: The market is not "will businesses use AI agents?" — it's "who helps them actually deploy and operate agents inside real workflows?" Most companies are stuck between experiment and production. The business opportunity is in the bridge.

### Anthropic's production agent architecture confirms the wedge

Anthropic's "Building Effective Agents" guide (December 2024, updated from production experience with dozens of enterprise teams) identifies the key production patterns:

- The most successful agent implementations use **simple, composable patterns** — not complex frameworks
- Production agents are typically **LLMs using tools in a loop**, with human checkpoints
- The critical design surface is the **agent-computer interface (ACI)** — tool definitions, approval flows, error handling
- The two highest-value production domains are **customer support** (conversation + action + measurable outcomes) and **coding** (verifiable outputs)

(Source: Anthropic, "Building effective agents," anthropic.com/engineering, December 2024)

**Translation**: The value is not in building the smartest agent. It's in designing the right tool interfaces, approval flows, and monitoring — the operational layer around the agent. That's a deployable, repeatable business.

### Market size signals

- The AI agents market was estimated at ~$5 billion in 2024 and projected to reach ~$50 billion by 2030 (Grand View Research, cited by IBM, 2026)
- The client onboarding software market alone lists 115 products on Capterra (Capterra, 2026), with the leading dedicated player (Rocketlane) pricing from $19–$109/user/month
- The AgentOps tooling ecosystem already has 17+ tools indexed on GitHub and code repositories (IBM, 2026)
- LangSmith serves Klarna, Rippling, Cloudflare, Home Depot, LinkedIn, Coinbase, and Bridgewater (LangChain, 2026)
- Arize AI has processed 1 trillion spans and serves DoorDash, Uber, Booking.com, PepsiCo, Siemens, and Priceline (Arize, 2026)

### UK / London / Reading context

- The UK is the largest single location for FX trading globally (38% of global turnover — BIS, 2022) and has the deepest financial services ecosystem in Europe
- London is a top-3 global AI hub with strong venture activity, talent from Imperial/UCL/Oxford/Cambridge, and a mature B2B SaaS buyer base
- Reading sits in the Thames Valley tech corridor — home to Microsoft UK, Oracle UK, Cisco UK, and hundreds of mid-market SaaS and services companies
- UK government AI strategy emphasises enterprise adoption, with the AI Safety Institute and DSIT driving regulatory frameworks that create compliance demand
- UK GDPR and the anticipated EU AI Act create a favourable environment for governance-first agentic AI products

---

## 3. Idea 1 — Agentic Client Onboarding OS

### 3.1 Product and Service

**What it does**: An agentic operations platform that automates B2B client onboarding workflows. When a new client is signed, the platform handles: document collection and chase, kickoff brief generation, project/task creation in PM tools, stakeholder reminders and follow-ups, risk and delay flagging, weekly status summaries, and human approval checkpoints before any sensitive action.

**How it works**: The platform connects to the customer's existing tools (HubSpot/Salesforce for CRM handoff, Slack for comms, Asana/Jira/Monday for project management, Google Drive/SharePoint for documents, email for external client communication). AI agents orchestrate the onboarding workflow according to configurable runbooks — but every client-facing action or data-sensitive step requires explicit human approval.

**What it is NOT**: It is not a generic project management tool. It is not an AI chatbot. It is not a consulting engagement. It is a productised, repeatable deployment of agentic workflows into one specific business process.

### 3.2 Unique Advantages and Ease of Imitation

| Advantage | Description | Imitability |
|-----------|-------------|-------------|
| **Workflow-specific agents** | Agents are pre-built for onboarding patterns (doc chase, kickoff prep, risk flag), not generic AI | Medium — requires domain knowledge of onboarding failure modes |
| **Human-in-the-loop by design** | Every sensitive action requires approval; full audit trail | Low barrier — but most competitors skip this, creating a trust gap |
| **Deep integration layer** | Bi-directional connectors to 5+ tools the customer already uses | High barrier at scale — each integration is engineering work |
| **Operational telemetry** | Every workflow step is traced: timestamps, approvals, exceptions, overrides | Medium — but the data compounds and cannot be retroactively generated |
| **Productised deployment** | Repeatable rollout playbooks, not custom consulting | Low barrier to concept — high barrier to execution quality |

**Weekend Replication Test**: A competent developer could build a basic onboarding automation in 2 weeks. They could NOT build the integration depth, approval workflows, exception handling, telemetry, and deployment playbooks that make it production-grade and trustworthy. The product is the operational layer, not the AI.

### 3.3 Market and Competitors

#### General Market Description

Client onboarding is the process of taking a signed customer from contract to productive usage. For B2B SaaS, agencies, consultancies, and outsourced service providers, onboarding is the single largest determinant of time-to-value, first-year retention, and expansion revenue. Poor onboarding is the #1 cause of early churn.

The market is large and underserved by AI. Capterra lists 115 client onboarding software products (Capterra, 2026), but the vast majority are workflow/project management tools (Monday, Asana, Smartsheet) repurposed for onboarding rather than purpose-built agentic platforms.

#### Target Market Segment

**Primary ICP**: B2B SaaS companies, digital agencies, consultancies, and outsourced service providers with 20–300 employees, based in the UK and Europe, running 10+ new client onboardings per month, using at least 3 of: HubSpot/Salesforce, Slack, Asana/Jira/Monday, Google Workspace/Microsoft 365.

**Buyer**: COO, VP Operations, Head of Implementation, Head of Customer Success.

**User**: Onboarding managers, project coordinators, implementation leads, CSMs.

**Geographic scope**: UK first (London, Thames Valley, Manchester, Edinburgh tech corridors), then Northern Europe (Netherlands, Germany, Nordics), then US East Coast.

#### Segment Size and Growth

- There are approximately 30,000–50,000 B2B SaaS companies in the UK alone (Tech Nation / Dealroom, estimates)
- Of these, approximately 5,000–10,000 have 20–300 employees and run structured onboarding processes
- At an average contract value of £4,000/month, 1% penetration = £2.4M ARR; 5% = £12M ARR
- The broader European B2B SaaS market is 3–4x the UK market alone
- Growth is driven by: (a) increasing SaaS adoption, (b) rising customer expectations for time-to-value, (c) AI readiness in operations teams

#### Competitor Deep Dive

**Tier 1 — Direct Competitors (Purpose-Built Onboarding Platforms)**

| Competitor | Founded | Funding | Revenue Est. | Pricing | Platforms | Moat Type | Key Weakness |
|-----------|---------|---------|-------------|---------|-----------|-----------|-------------|
| **Rocketlane** | 2020 | $45M (Series B, 2023) | $10–20M ARR est. | $19–$109/user/month | HubSpot, Salesforce, Slack, Jira, Zapier, Workato, Snowflake | Switching costs (project data), brand | No agentic automation; workflow-based, not agent-based; requires manual configuration per project |
| **GUIDEcx** | 2017 | $25M+ | $5–15M ARR est. | Custom pricing (demo required) | Salesforce, HubSpot, Slack, Jira | Switching costs (project templates) | No AI agents; traditional project management approach; US-focused |
| **OnRamp** | 2021 | $5M+ | Early stage | Custom pricing | HubSpot, Salesforce | Early mover in dynamic onboarding | Small team; limited integrations; no agent automation |
| **Process Street** | 2014 | $12M (Series A) | ~$10M ARR est. | From $100/month (5 members) | Zapier, Slack, HubSpot, Salesforce | Brand, template library | Generic workflow tool; not onboarding-specific; AI features are bolted on |
| **Clustdoc** | 2016 | Bootstrapped | $1–3M ARR est. | From $100/month | Zapier | Document collection focus | Narrow scope; no project management; no AI |

**Tier 2 — Adjacent Competitors (General PM Tools Used for Onboarding)**

| Competitor | Founded | Funding | Revenue | Key Weakness for Onboarding |
|-----------|---------|---------|---------|---------------------------|
| **Asana** | 2008 | Public (NYSE: ASAN) | $652M ARR (FY2025) | Generic; no onboarding-specific workflows; no AI agents; no client portal |
| **Monday.com** | 2012 | Public (NASDAQ: MNDY) | $972M ARR (FY2025) | Same as Asana — too generic, no client-facing portal, no agent automation |
| **Kantata (Mavenlink)** | 2008 | $115M | ~$50M ARR est. | Enterprise-focused PSA; expensive; slow implementation; no agentic layer |
| **Certinia (FinancialForce)** | 2009 | Salesforce-backed | ~$150M ARR est. | Salesforce-native only; enterprise-only; zero AI agent capability |

#### On What Basis Do Rivals Compete?

1. **Templates and standardisation** — Rocketlane and Process Street compete on pre-built templates and repeatable workflows
2. **Integration breadth** — Rocketlane leads with HubSpot, Salesforce, Slack, Jira, Workato; others lag
3. **Client experience** — Branded client portals and self-serve collaboration (Rocketlane, LaunchBay)
4. **Reporting and visibility** — CSAT, project timelines, resource utilisation (Rocketlane, GUIDEcx)
5. **Price** — Ranges from $19/user/month (Rocketlane Essential) to enterprise pricing ($100+/user/month)

#### The Gap

**No competitor offers an agentic automation layer for onboarding.** Rocketlane has just launched "Nitro" AI agents (2026) for documentation and resourcing, but these are add-ons to a project management platform, not a purpose-built agentic onboarding OS. The gap is: agents that autonomously execute onboarding steps (doc chase, kickoff generation, task creation, follow-ups) with human approval checkpoints, full traceability, and cross-tool orchestration.

**Counter-positioning**: Rocketlane and GUIDEcx are project management tools with onboarding templates. They cannot reposition as "agent-first" without cannibalising their existing manual-workflow product and confusing their installed base. A new entrant can be agent-first from day one.

#### How Customers See the Competition

Buyers in this space currently use a combination of:
- A generic PM tool (Asana/Monday/Jira) + spreadsheets + email for onboarding
- Or a purpose-built tool like Rocketlane/GUIDEcx for structured onboarding

The dominant alternative is the **status quo**: manual coordination via email, Slack, and spreadsheets. Most mid-market companies do not have a dedicated onboarding platform at all. The primary competitor is not Rocketlane — it's "we'll just use Asana and email."

### 3.4 Revenue Model and Unit Economics

| Metric | Value | Source / Assumption |
|--------|-------|-------------------|
| Implementation fee | £8,000–£15,000 | Based on 2–4 weeks of setup, integration, and training |
| Monthly managed ops | £2,500–£5,000/month | Scales with number of active onboardings and integrations |
| Target gross margin | 75–85% | Post-setup, recurring revenue is high-margin; LLM API costs are <5% of revenue |
| Estimated CAC (founder-led) | £2,000–£4,000 | Outbound + content + referral; no paid ads at launch |
| Estimated LTV (18-month retention) | £50,000–£100,000 | Implementation + 18 months of recurring |
| LTV:CAC ratio | 12–25x | Strong; driven by low CAC from founder-led sales |
| Months to payback | 1–2 | Implementation fee covers CAC immediately |

**Design partner pricing** (months 0–3): £3,000–£5,000/month for 8 weeks, discounted in exchange for case study rights and feedback.

### 3.5 Technology Assessment

The technology stack is straightforward and low-risk:
- **Orchestration layer**: Python/TypeScript service that coordinates agent workflows, manages state, and enforces approval checkpoints
- **LLM layer**: Multi-model routing (OpenAI, Anthropic, Google) via abstraction — no single-vendor lock-in
- **Integration layer**: REST/webhook connectors to HubSpot, Salesforce, Slack, Asana, Jira, Google Drive, email
- **Tracing and telemetry**: OpenTelemetry-based logging of every agent action, approval, and exception
- **Deployment**: Cloud-hosted (Railway/Render/AWS), self-hosted option for enterprise

**Technology risk**: Low. The value is in workflow design, integration depth, and operational reliability — not in novel AI research.

### 3.6 Moat Score and Path

| Moat Dimension | Score (0–2) | Evidence / Path | Timeline |
|---------------|-------------|-----------------|----------|
| **Switching costs** | 2 | Deep integration with 5+ tools; historical workflow data; custom runbooks; team training | Months 3–6 |
| **Network effects** | 0 | None at launch; potential indirect effects from shared templates at scale | 18+ months |
| **Data advantage** | 1 | Operational telemetry on onboarding timelines, exceptions, overrides compounds over time | Months 6–12 |
| **Brand / trust** | 0 | None at launch; must be earned through case studies and community | 6–12 months |
| **Regulatory / compliance barrier** | 1 | SOC 2 compliance becomes a moat once achieved (6+ months to clear); GDPR compliance from day 1 | 6–12 months |
| **Counter-positioning** | 1 | Existing PM tools cannot become agent-first without cannibalising their manual-workflow product | Immediate |
| **Total** | **5/10** | Path to 7/10 within 12 months via data advantage + brand + SOC 2 | |

### 3.7 Mandate Compliance

| Objective / Constraint | Status | Evidence |
|-----------------------|--------|----------|
| Obj 1: Structural moat ≥ 6/10 | **CONDITIONAL** — 5/10 at launch, path to 7/10 by month 12 | Switching costs + counter-positioning are strong from day 1 |
| Obj 2: Platform independence | **PASS** — No single platform > 30% | Multi-model LLM, multi-tool integration, own orchestration layer |
| Obj 3: Stable retention | **PASS** — B2B recurring, high switching costs, daily usage | LTV:CAC > 12x; CAC payback < 2 months |
| Obj 4: Commercial defensibility | **PASS** — Integration depth + operational telemetry | Fails Weekend Replication Test (production-grade system takes months, not weekends) |
| Constraint 1: No single-point dependency | **PASS** | No dependency > 30% of revenue or functionality |
| Constraint 2: B2C churn ceiling | **N/A** — B2B model | |
| Constraint 3: Workflow integration | **PASS** | Integrates with tools customer already pays for (HubSpot, Slack, Asana, etc.) |

---

## 4. Idea 2 — Agentic Support Resolution Platform

### 4.1 Product and Service

**What it does**: A cross-stack AI agent platform for customer support that handles triage, knowledge retrieval, draft resolution, workflow actions (refunds, ticket updates, account changes), escalation routing, and QA review — across Zendesk, Intercom, Slack, email, and internal tools.

**Positioning**: Not "AI chatbot" (crowded). Instead: "cross-stack support resolution layer with human approval, traceability, and continuous QA." The differentiator is that it orchestrates actions across multiple backend systems, not just generates text responses.

### 4.2 Competitors

This space is **heavily funded and rapidly consolidating**.

**Tier 1 — Direct Competitors (AI-Native Support Platforms)**

| Competitor | Founded | Funding | Valuation | Pricing | Key Customers | Key Strength |
|-----------|---------|---------|-----------|---------|---------------|-------------|
| **Sierra AI** | 2023 | $175M+ | $4.5B | Outcome-based (pay per resolution) | Rocket Mortgage, SoFi, SiriusXM, Sonos, CLEAR, Brex, Ramp, WeightWatchers, Wayfair | Founded by ex-Salesforce CEO Bret Taylor + Clay Bavor; SOC 2, ISO 27001, HIPAA, GDPR; omnichannel (chat, SMS, WhatsApp, email, voice) |
| **Decagon AI** | 2023 | $100M+ | $1B+ | Custom enterprise | Hertz, Duolingo, Figma, Notion, Rippling, Eventbrite, Chime, Affirm, Dropbox | Natural language AOPs; 80% deflection (Duolingo); 3x CSAT increase (Oura); omnichannel |
| **Forethought** | 2018 | $92M | ~$500M | Per-resolution | Various enterprise | Triage AI + Solve AI; Salesforce/Zendesk/Intercom integration |
| **Ada** | 2016 | $190M | ~$1B | Platform fee | Meta, Verizon, AirAsia, Square | Multilingual; no-code builder; voice + chat |

**Tier 2 — Incumbent AI Features**

| Platform | AI Feature | Limitation |
|----------|-----------|------------|
| **Zendesk** | AI agents (Answer Bot → AI Agents) | Locked to Zendesk ecosystem; limited cross-tool orchestration |
| **Intercom** | Fin AI Agent | Locked to Intercom; cannot orchestrate across external systems |
| **Freshdesk** | Freddy AI | Same vendor lock-in problem |

#### Competitive Assessment

This market is **extremely well-funded**. Sierra alone has raised $175M+ at a $4.5B valuation, with Bret Taylor (ex-Salesforce CEO) as co-founder. Decagon has raised $100M+ and serves Duolingo, Figma, Notion, and Rippling. The barriers to entry for a new entrant are:

1. **Capital**: Incumbents have $100M+ in funding
2. **Enterprise trust**: Sierra and Decagon already serve Fortune 500 companies
3. **Technology**: Outcome-based pricing requires sophisticated resolution measurement
4. **Distribution**: Enterprise sales cycles of 3–6 months

### 4.3 Moat Score

| Moat Dimension | Score (0–2) | Notes |
|---------------|-------------|-------|
| Switching costs | 1 | Integration creates switching costs, but incumbents already have this |
| Network effects | 0 | None |
| Data advantage | 1 | Resolution data compounds, but Sierra/Decagon already have millions of conversations |
| Brand / trust | 0 | None at launch; incumbents have enterprise brand |
| Regulatory barrier | 0 | No unique compliance position |
| Counter-positioning | 0 | Cannot counter-position against Sierra/Decagon — they ARE the AI-native entrants |
| **Total** | **2/10** | **FAILS Objective 1 (≥ 6/10 required)** |

### 4.4 Mandate Compliance

| Objective / Constraint | Status | Evidence |
|-----------------------|--------|----------|
| Obj 1: Structural moat ≥ 6/10 | **FAIL** — 2/10 | Cannot achieve structural advantage against $4.5B-valued incumbents |
| Obj 2: Platform independence | PASS | |
| Obj 3: Stable retention | PASS (in theory) | |
| Obj 4: Commercial defensibility | **FAIL** — Weekend Replication Test is borderline; commercial defensibility against Sierra/Decagon is zero | |

**Verdict: KILL as standalone business. Too crowded, too well-funded. Do not enter this market directly.**

However: support resolution is a natural expansion wedge FROM Idea 1. Once you own the onboarding workflow, adding post-onboarding support resolution is a natural product expansion that leverages existing integrations and customer relationships.

---

## 5. Idea 3 — AgentOps Control Plane for Mid-Market

### 5.1 Product and Service

**What it does**: A monitoring, approval, evaluation, replay, routing, and governance layer for companies that already have 3–20 agentic workflows in production. Features include:

- Prompt and tool versioning
- Run traces and session replays
- Error detection and automated alerts
- Model routing and budget controls
- Human sign-off steps for sensitive actions
- KPI dashboards per agent workflow
- Compliance and audit logging

**What it is NOT**: It is not an agent framework (LangChain, CrewAI). It is not an LLM provider. It is the vendor-neutral operating layer above all of them.

### 5.2 Competitors

**Tier 1 — Direct Competitors (AI/LLM Observability Platforms)**

| Competitor | Founded | Funding | Revenue Est. | Pricing | Key Customers | Key Strength |
|-----------|---------|---------|-------------|---------|---------------|-------------|
| **LangSmith** (LangChain) | 2022 | $45M+ (Series A+) | Growing rapidly | Free tier + usage-based paid | Klarna, Vanta, Rippling, Lyft, Harvey, Cloudflare, Home Depot, LinkedIn, Coinbase, Bridgewater, Workday, Cisco | Framework-agnostic; OTEL support; tracing + monitoring + insights; self-hosted option; massive developer adoption through LangChain OSS |
| **Arize AI** | 2020 | $62M (Series B, 2024) | ~$15–30M ARR est. | Freemium + enterprise | DoorDash, Instacart, Reddit, Roblox, Uber, Booking.com, PepsiCo, Siemens, Priceline, Flipkart, Microsoft | 1T spans processed; 50M evals/month; 5M downloads/month; Phoenix OSS; OTEL-based; development + observability + evaluation in one platform |
| **Helicone** | 2023 | YC-backed | Early stage | Free tier + paid | Various startups | Lightweight; proxy-based integration; recently acquired by Mintlify |
| **Weights & Biases (Weave)** | 2017 | $250M+ | ~$100M+ ARR est. | Freemium + enterprise | Broad ML/AI teams | Established MLOps brand extending into LLM observability |
| **Braintrust** | 2023 | $36M (Series A) | Early stage | Free tier + enterprise | Various | Evals-focused; proxy for model routing; logging |
| **AgentOps** (the company) | 2023 | Seed stage | Minimal | Free tier | Early adopters | Purpose-built for agent monitoring; small team |

#### Competitive Assessment

This space is still early but moving fast. LangSmith and Arize are the clear leaders, with massive enterprise customer bases and tens of millions in ARR. However, critical observations:

1. **All existing players are developer tools**, not business-ops tools. They serve AI engineers, not COOs or Heads of Operations.
2. **No player offers a business-user-friendly approval/governance layer**. LangSmith's tracing is powerful but requires engineering expertise to interpret.
3. **The mid-market is underserved**. LangSmith and Arize target enterprises with AI teams. Companies with 3–20 agent workflows but no dedicated AI ops team have no good option.
4. **The compliance/governance angle is wide open**. With EU AI Act and UK AI Safety frameworks emerging, there's a regulatory tailwind for governance-first platforms.

#### The Gap

The gap is not "another observability tool for engineers." The gap is: **a business-user-friendly control plane that non-engineers can use to approve, monitor, and govern agentic workflows.**

Think of it as: LangSmith is for the AI engineer. The AgentOps Control Plane is for the COO who needs to sign off on what the AI engineer built.

### 5.3 Moat Score

| Moat Dimension | Score (0–2) | Evidence / Path | Timeline |
|---------------|-------------|-----------------|----------|
| Switching costs | 2 | Once all agent activity routes through the control plane, ripping it out is extremely painful | Months 3–6 |
| Network effects | 0 | None at launch; potential for shared governance templates at scale | 18+ months |
| Data advantage | 2 | All agent traces, approvals, exceptions, costs, and outcomes flow through the platform; this becomes the single source of truth | Months 3–6 |
| Brand / trust | 0 | None at launch | 6–12 months |
| Regulatory barrier | 1 | SOC 2 + GDPR + EU AI Act compliance logging requirement creates demand | 6–12 months |
| Counter-positioning | 1 | LangSmith/Arize are developer tools; repositioning for business users would alienate their core audience | Immediate |
| **Total** | **6/10** | **PASSES Objective 1** — path to 8/10 within 12 months via brand + regulatory | |

### 5.4 Revenue Model

| Metric | Value | Source / Assumption |
|--------|-------|-------------------|
| Monthly SaaS | £1,000–£5,000/month | Based on number of agent workflows monitored |
| Setup/advisory fee | £3,000–£10,000 | Initial configuration, integration, and governance design |
| Target gross margin | 80–90% | SaaS model; infrastructure costs are minimal relative to value |
| Estimated CAC | £3,000–£6,000 | Outbound + content + conference presence |
| Estimated LTV (24-month) | £36,000–£120,000 | 24 months × £1,500–£5,000/month |
| LTV:CAC ratio | 6–20x | Strong |
| Months to payback | 3–6 | Longer than Idea 1 because no upfront implementation fee |

### 5.5 Mandate Compliance

| Objective / Constraint | Status | Evidence |
|-----------------------|--------|----------|
| Obj 1: Structural moat ≥ 6/10 | **PASS** — 6/10 at launch | Switching costs + data advantage from day 1 |
| Obj 2: Platform independence | **PASS** — vendor-neutral by design | Multi-model, multi-framework, OTEL-based |
| Obj 3: Stable retention | **PASS** — B2B SaaS, high switching costs | |
| Obj 4: Commercial defensibility | **PASS** — data gravity + governance compliance | Cannot be replicated without equal deployment volume |
| Constraint 1: No single-point dependency | **PASS** | |
| Constraint 2: B2C churn ceiling | **N/A** — B2B | |
| Constraint 3: Workflow integration | **PASS** — integrates with customer's existing AI stack | |

### 5.6 Why Not Build This First?

Despite the stronger long-term moat score, Idea 3 has a harder first-sale problem:

1. **The buyer must already have 3+ agentic workflows in production**. In April 2026, most mid-market companies don't yet.
2. **The value proposition is monitoring/governance**, not revenue generation. Harder to sell than "we'll cut your onboarding time in half."
3. **The sales cycle is longer** because it requires buy-in from both engineering and operations.
4. **There's no implementation fee** to cover early CAC.

The recommended path is: build Idea 1 first, accumulate operational telemetry and deployment data, then extract the monitoring/governance layer into Idea 3 as a standalone product.

---

## 6. Recommended Strategy: Build Idea 1, Expand Into Idea 3

### Phase 1: Agentic Client Onboarding OS (Months 0–12)

**Months 0–2: Discovery and MVP**
- Interview 25–30 ops leaders at onboarding-heavy businesses in London and Thames Valley
- Validate narrow ICP: B2B SaaS companies with 20–100 employees, 10+ onboardings/month
- Confirm the KPI: time-to-live, onboarding cycle time, admin hours per client, or SLA misses
- Build narrow MVP: HubSpot + Slack + Asana + email + Google Drive
- Add approval checkpoints and OpenTelemetry trace logging from day 1

**Months 2–5: Design Partners**
- Land 3 design partners at £3,000–£5,000/month
- Do some work manually behind the scenes if needed (Wizard of Oz)
- Capture every exception, override, and edge case
- Measure before/after onboarding time and admin effort
- Produce 3 case studies with hard metrics

**Months 5–9: Productise and Scale**
- Codify deployment playbooks into repeatable configuration
- Add dashboards, rules engine, and template library
- Standardise pricing: £10k implementation + £2.5k–£5k/month
- Begin outbound to wider UK mid-market
- Target 10–15 paying customers by month 9

**Months 9–12: Expansion**
- Add Salesforce integration (opens enterprise segment)
- Add post-onboarding workflows: support handoff, renewal prep, QBR automation
- Begin SOC 2 certification process
- Build the internal monitoring layer that becomes Idea 3

### Phase 2: AgentOps Control Plane (Months 12–24)

**Months 12–15: Internal Extraction**
- Extract the monitoring, approval, and telemetry layer from Idea 1 into a standalone product
- Package it as a separate offering for companies that already have agentic workflows
- Launch to the developer-adjacent buyer: VP Engineering, Head of AI Ops

**Months 15–18: Market Entry**
- Position as the "business-user control plane for AI agents"
- Target companies in the Thames Valley tech corridor that are deploying AI but lack governance
- Price at £1,500–£5,000/month
- Leverage existing Idea 1 customer base for referrals

**Months 18–24: Platform Play**
- Multi-workflow customers from Idea 1 become natural Idea 3 customers
- Aggregate anonymised benchmark data across deployments
- The combination of "deploy agents" (Idea 1) + "govern agents" (Idea 3) creates an ecosystem moat

### Moat Evolution Over Time

| Timeframe | Primary Moat | How Built |
|-----------|-------------|-----------|
| Months 0–6 | **Process power** | Standardise one workflow; repeatable playbooks; productised deployment |
| Months 6–12 | **Switching costs** | Deep integrations; workflow history; customer-specific rules and templates |
| Months 12–18 | **Cornered resource** | Operational telemetry data that improves recommendations and cannot be replicated |
| Months 18–24 | **Counter-positioning** | "Deploy + Govern" platform that consultancies (too slow) and suite vendors (too locked-in) cannot match |

### What We Would NOT Do

- Do NOT start with a broad "AI transformation agency"
- Do NOT build our own model
- Do NOT target heavily regulated or cyber-heavy use cases first
- Do NOT promise full autonomy — sell "human-supervised agentic operations"
- Do NOT choose a wedge where the only differentiator is prompt quality
- Do NOT enter the AI support space directly (Idea 2) — Sierra and Decagon own it

---

## 7. Risk Assessment

### Risk 1: Market Timing — Companies Not Ready for Agentic Onboarding

**Probability**: Medium
**Impact**: High
**Mitigation**: Start with companies that already use 3+ SaaS tools for onboarding and are frustrated by manual coordination. These are "AI-ready" by behaviour even if they don't identify as such. The product's value (cut onboarding time, reduce admin hours) is measurable in weeks, not months.

### Risk 2: Sales Cycle Length

**Probability**: Medium
**Impact**: Medium
**Mitigation**: Founder-led sales with design partner pricing (£3–5k/month, no long-term commitment) keeps the cycle short. Target COOs and Heads of Ops, not IT procurement. The implementation fee covers CAC immediately.

### Risk 3: Integration Maintenance

**Probability**: High
**Impact**: Medium
**Mitigation**: Limit initial integrations to 5 tools (HubSpot, Slack, Asana, Google Drive, email). Use Zapier/Make as a bridge for non-core integrations. Each new integration is a strategic decision, not a support burden.

### Risk 4: LLM Provider Dependency

**Probability**: Low (by design)
**Impact**: High (if not mitigated)
**Mitigation**: Multi-model routing from day 1. Abstract LLM calls behind own orchestration layer. No single LLM vendor > 30% of product functionality. Test regularly across OpenAI, Anthropic, and Google models.

### Risk 5: Replication by Incumbents (Rocketlane, Monday, Asana)

**Probability**: Medium (12–18 month window)
**Impact**: Medium
**Mitigation**: Rocketlane is the closest threat — they've launched "Nitro" AI agents for documentation and resourcing. However, their architecture is fundamentally a project management platform with AI bolted on, not an agent-first orchestration layer. The counter-positioning advantage holds as long as we are agent-first and they are PM-first. Speed to market and customer lock-in via integrations are the primary defences.

### Risk 6: Founder Bandwidth (Two Graduate Students)

**Probability**: High
**Impact**: Medium
**Mitigation**: The product is a managed service initially, not a self-serve SaaS. This means fewer features needed at launch. Revenue from design partners covers early costs. Post-graduation (July 2026), both founders are full-time.

---

## 8. Financial Summary

### Year 1 (Months 0–12)

| Quarter | Customers | MRR (£) | ARR Run Rate (£) | Notes |
|---------|-----------|---------|-------------------|-------|
| Q1 (Jul–Sep 2026) | 3 design partners | £12,000 | £144,000 | Design partner pricing |
| Q2 (Oct–Dec 2026) | 8 paying | £28,000 | £336,000 | Standard pricing kicks in |
| Q3 (Jan–Mar 2027) | 15 paying | £52,500 | £630,000 | Outbound scaling |
| Q4 (Apr–Jun 2027) | 25 paying | £87,500 | £1,050,000 | Approaching £1M ARR |

**Implementation fees** (one-time): ~£150,000–£250,000 cumulative across 25 customers

### Year 2 Target
- 50–80 customers
- £2–3M ARR
- Begin Idea 3 (AgentOps Control Plane) contributing additional £200–400K ARR
- Total combined: £2.5–3.5M ARR

### Funding Requirement
- **Months 0–6**: Bootstrap / self-funded (design partner revenue covers costs)
- **Months 6–12**: Consider £250K–£500K pre-seed if growth rate warrants faster hiring
- **Months 12–18**: Seed round (£1–2M) to scale sales, engineering, and launch Idea 3

---

## 9. Exit Routes

Following the same framework as the Hedge Edge analysis:

**Most credible exit: Strategic trade sale (3–5 year horizon)**

Logical acquirers:
1. **Rocketlane / GUIDEcx** — acquire the agentic automation layer they can't easily build themselves
2. **HubSpot / Salesforce** — acquire an onboarding solution that deepens their ecosystem lock-in
3. **ServiceNow** — acquire an agentic operations platform for workflow automation
4. **Accenture / Deloitte Digital** — acquire productised AI deployment capability for their consulting practice

**Valuation framework**: Private SaaS companies at £2–3M ARR with strong growth and retention trade at 8–15x ARR, implying a potential exit value of £16–45M within 3–4 years.

---

## 10. Final Mandate Scorecard

| Criterion | Idea 1: Onboarding OS | Idea 2: Support Platform | Idea 3: AgentOps Control |
|-----------|----------------------|-------------------------|------------------------|
| Obj 1: Moat ≥ 6/10 | **5/10** (path to 7) | **2/10** ❌ | **6/10** ✓ |
| Obj 2: Platform independence | ✓ | ✓ | ✓ |
| Obj 3: Stable retention | ✓ | ✓ | ✓ |
| Obj 4: Commercial defensibility | ✓ | ❌ | ✓ |
| Constraint 1: No single dependency | ✓ | ✓ | ✓ |
| Constraint 2: B2C churn ceiling | N/A | N/A | N/A |
| Constraint 3: Workflow integration | ✓ | ✓ | ✓ |
| **Weekend Replication Test** | **PASS** | FAIL (Sierra exists) | **PASS** |
| **Overall** | **GO — Build first** | **KILL standalone** | **GO — Build second** |

---

## Reference List

Anthropic (2024) Building effective agents. Available at: https://www.anthropic.com/engineering/building-effective-agents (Accessed: 8 April 2026).

Arize AI (2026) Ship Agents that Work: AI & Agent Engineering Platform. Available at: https://arize.com (Accessed: 8 April 2026).

Bank for International Settlements (2022) Triennial Central Bank Survey: OTC foreign exchange turnover in April 2022. Basel: BIS. Available at: https://www.bis.org/statistics/rpfx22_fx.htm (Accessed: 8 April 2026).

Capterra (2026) Best Client Onboarding Software. Available at: https://www.capterra.com/client-onboarding-software/ (Accessed: 8 April 2026).

Decagon AI (2026) The AI concierge for every customer. Available at: https://decagon.ai (Accessed: 8 April 2026).

Grand View Research (2025) AI Agents Market Size, Share & Trends Analysis Report, 2025–2030. Cited by IBM (2026).

Helicone (2026) Build Reliable AI Apps. Available at: https://www.helicone.ai (Accessed: 8 April 2026).

IBM (2026) What is AgentOps? Available at: https://www.ibm.com/think/topics/agentops (Accessed: 8 April 2026).

LangChain (2026) LangSmith Observability: AI Agent Observability Platform. Available at: https://www.langchain.com/langsmith/observability (Accessed: 8 April 2026).

McKinsey & Company (2025) The state of AI in 2025: Agents, innovation, and transformation. Available at: https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai (Accessed: 8 April 2026).

Rocketlane (2026) Find the right plan for your needs. Available at: https://www.rocketlane.com/pricing (Accessed: 8 April 2026).

Rocketlane (2026) Deliver radical efficiency with an agentic, all-in-one PSA. Available at: https://rocketlane.com (Accessed: 8 April 2026).

Sierra AI (2026) Better customer experiences. Built on Sierra. Available at: https://sierra.ai (Accessed: 8 April 2026).
