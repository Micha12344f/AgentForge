# Agentic Capability Plan — Learn by Building, Execute by Learning

> **Status**: ACTIVE
> **Date**: 2026-04-09
> **Author**: Ryan + Orchestrator
> **Companion files**: `idea-mandate-memo.md`, `idea-002-departmental-agentic-os.md`
> **Core thesis**: The selected idea is to build departmental agents in public with real business use cases, starting with onboarding. Every hour spent learning agentic AI must also produce a reusable asset or proof point for that thesis.

---

## The Strategic Frame

The idea is chosen. What matters now is building capability and evidence faster than the market. You need:
1. **Deep technical fluency** in how agentic systems actually work in production
2. **A portfolio of real builds** that prove capability to yourself and to future customers
3. **Pattern recognition** for where agentic automation creates genuine ROI vs where it is theatre
4. **Speed** — when the right opportunity crystallises, you can ship in weeks, not months

The plan below is not a course. It is the execution plan for validating the onboarding-first wedge while building reusable capability for later departmental expansion.

---

## Principle: No Dead Learning

Every activity must produce at least one of:
- A working tool or system you keep using
- A reusable component in the shared/ library
- A case study or demo you can show a potential customer
- A published artefact (blog post, open-source repo, video, template)
- A customer conversation or paid engagement

If an activity produces none of these, it is passive consumption and should be cut.

---

## Skill Domains to Master

| # | Domain | Why It Matters | Current Level | Target Level |
|---|--------|---------------|---------------|-------------|
| 1 | Agent Orchestration | Core of every agentic product — routing, state, handoff, retry, fallback | Medium (internal orchestrator exists) | High |
| 2 | Tool-Use & Integration | Agents are only useful if they can act on real systems (CRM, PM, email, docs) | Medium (shared clients exist) | High |
| 3 | Human-in-the-Loop / Approval Flows | Trust is the product — every production agent needs approval checkpoints | Low-Medium (conceptual, not shipped) | High |
| 4 | Evaluation & Observability | You cannot improve what you cannot measure — traces, evals, failure analysis | Low (basic alerting exists) | High |
| 5 | Prompt Engineering & Reliability | Reducing hallucination, improving instruction-following, structured output | Medium | High |
| 6 | Multi-Agent Coordination | Multiple agents working together with clear ownership and conflict resolution | Medium (internal department model) | High |
| 7 | Deployment & Productionisation | Shipping agents that run 24/7, handle edge cases, and recover from failure | Medium (Railway, VPS, cron) | High |
| 8 | Security & Compliance | GDPR, data handling, prompt injection defence, audit trails | Low-Medium | Medium-High |
| 9 | Sales & Positioning | Explaining agentic value to non-technical buyers without hype | Medium | High |
| 10 | Workflow Decomposition | Breaking real business processes into agent-suitable steps | High (strategy work) | Very High |

---

## The Plan: 14-Day Blitz

Same deliverables as a 12-week plan, compressed to match the team's actual execution speed. Phases overlap where dependencies allow. The pace is aggressive but realistic given existing infrastructure in shared/ and the internal orchestrator.

---

### Day 1–2: Agent Core + First Integrations (parallel)

**Morning track — Agent executor**:
- [ ] Single-agent executor: takes a task, decomposes into steps, calls tools, returns structured output
- [ ] Trace log format (JSON): every decision, tool call, result, latency, cost
- [ ] Error recovery: retry, fallback, escalate

**Afternoon track — Integrations (start 3 of 5)**:
- [ ] HubSpot CRM client: contacts, deals, lifecycle events, webhooks
- [ ] Slack client: messages, channels, slash commands, interactive messages
- [ ] Google Workspace client: Gmail send/read, Drive file ops, Calendar CRUD

**End of Day 2 checkpoint**:
- Agent can execute a 3-step task using real tools and produce a trace
- 3 integrations have working CRUD + auth + rate-limit handling

**Skill domains**: 1, 2, 5, 7

---

### Day 3–4: Remaining Integrations + Approval Engine

**Morning track — Integrations (finish)**:
- [ ] Asana or Linear client: tasks, projects, status updates, webhooks
- [ ] Stripe or Xero client: invoices, payments, reconciliation events
- [ ] Integration test suite: mock + live sandbox for all 5
- [ ] Auth flow docs: OAuth2, API key, service account per integration

**Afternoon track — Human-in-the-loop**:
- [ ] Approval queue service: API + Slack-based approval UI
- [ ] Agent SDK function: `await_approval(action, context, urgency)`
- [ ] Audit log: timestamps, approver identity, decision, rationale
- [ ] Timeout + escalation: no response in X minutes → escalate to next approver

**End of Day 4 checkpoint**:
- 5 production-grade integrations ready
- Approval engine working: agent pauses → human approves in Slack → agent resumes → trace logged

**Skill domains**: 2, 3, 7, 8

---

### Day 5–6: Observability + Evaluation

**Build**:
- [ ] Tracing service: every agent action logged (input, output, latency, cost, outcome, approval status)
- [ ] Evaluation harness: define expected outcomes per task, run agent, compare, score pass/fail
- [ ] At least 30 test cases across 3+ workflow types
- [ ] Summary report: pass rate, failure categories, cost per task, latency distribution
- [ ] Regression alerting: pass rate drops below threshold → Discord/Slack alert

**End of Day 6 checkpoint**:
- Can run any agent workflow and get a scored trace with cost and failure analysis
- First batch of eval results showing where agents succeed and where they break

**Skill domains**: 4, 7

---

### Day 7–9: Multi-Agent Orchestration

**Build**: A multi-agent system where 3+ agents coordinate on a real end-to-end workflow using the integrations and approval engine from previous days.

**Target workflow**: New client signed →
1. Agent A reads deal from HubSpot, creates project in Asana
2. Agent B drafts welcome email in Gmail, pauses for approval
3. Agent C schedules kickoff in Google Calendar
4. Agent D posts internal summary in Slack
5. Orchestrator tracks DAG completion, handles failures at any node

**Deliverables**:
- [ ] DAG-based multi-agent orchestrator with shared state object
- [ ] Failure handling: node failure preserves completed work, retries or escalates
- [ ] End-to-end demo running on real sandbox accounts (not mocks)
- [ ] All runs traced and scored through the eval harness

**End of Day 9 checkpoint**:
- Full pipeline runs: HubSpot → Asana → Gmail (with approval) → Calendar → Slack
- Every step traced, scored, and auditable

**Skill domains**: 6, 1, 2, 3

---

### Day 10–12: First Real Deployment

**Deploy** one complete agentic workflow for a real use case:
- Option A: Automate a piece of Hedge Edge's own operations (e.g., new-subscriber welcome, alert triage, report generation)
- Option B: Deploy for a friend's or contact's business (client onboarding, invoice chase, weekly reporting)
- Option C: Public demo that runs live and anyone can trigger

**Deliverables**:
- [ ] Live system running on real data with real users or real triggers
- [ ] Monitoring: know when it fails before the user does (Discord + email alerts)
- [ ] Usage dashboard: runs per day, cost per run, success rate, avg latency
- [ ] First round of user feedback collected
- [ ] Idea pipeline check: log any pain points or opportunities discovered during deployment

**End of Day 12 checkpoint**:
- One agentic system running in production with monitoring
- At least 1 real user besides yourself

**Skill domains**: 7, 9, 3, 4

---

### Day 13–14: Case Study, Public Artefacts, Pipeline Review

**Ship the story**:
- [ ] Case study document: problem → solution → architecture → results → learnings
- [ ] 2–3 short-form posts (LinkedIn / X) showing what was built and what was learned
- [ ] 1 technical blog post or demo video walking through the full stack
- [ ] Open-source at least one non-proprietary component (integration client, eval harness, or approval engine)

**Pipeline review**:
- [ ] Log all observations and pain points discovered during the 14 days
- [ ] Run Gate 0 entry check on any ideas that emerged
- [ ] Re-evaluate idea-002 (Departmental Agentic OS): still valid? Better wedge discovered?
- [ ] Decide: push idea-002 to Gate 1, pivot to a new idea, or run a second 14-day cycle on a harder problem

**End of Day 14 checkpoint**:
- Public proof that you built and shipped a real agentic system
- Clear view of what to build next

**Skill domains**: 9, 10

---

## After the 14 Days: What You Have

1. A working single-agent framework with tool-use and error recovery
2. Five production-grade integrations with real business tools
3. A human-in-the-loop approval engine
4. An evaluation and observability system
5. A multi-agent orchestrator
6. At least one real deployment with real users
7. Public artefacts proving capability
8. A sharper idea pipeline grounded in building, not theory

That is the operational core of any agentic business. And after 14 days of building at this intensity, the pattern recognition you gain is worth more than months of research.

---

## Ongoing: The Idea Pipeline Runs in Parallel

While building, keep the idea pipeline active:

| Day | Pipeline Activity |
|-----|-------------------|
| Every day | Log at least 1 observation: "I noticed X is painful / broken / manual in Y context" |
| Day 6 | Review observations. Do any pass the 5 entry criteria? If yes, create Gate 0 entries. |
| Day 12 | Review all Gate 0 entries. Run Gate 1 quick-kill on the best 2–3. |
| Day 14 | Pick the strongest idea and decide: Gate 2 deep research or second build cycle. |

The key insight: **building gives you better ideas than thinking**. The best business ideas will come from pain you discover while building real systems, not from brainstorming sessions.

In this case, the build is not abstract exploration. It is direct validation of the onboarding-first wedge inside idea-002.

---

## Ongoing: Public Learning Compounds

Everything you build should be documented publicly where possible:

| Format | When | Purpose |
|--------|------|--------|
| Short-form posts (LinkedIn / X) | Daily or every other day | Build audience, attract inbound interest, signal expertise |
| Technical blog post or demo video | Day 13–14 | Deep dive on what you built and what you learned |
| Open-source component | Day 14 | Release at least one non-proprietary tool |

This is not marketing for a product. This is building a reputation as someone who ships real agentic systems. That reputation becomes distribution when you do have a product to sell.

---

## Anti-Patterns to Avoid

| Trap | Why It Feels Productive | Why It Is Not |
|------|------------------------|---------------|
| Watching AI YouTube all day | Feels like learning | You absorb opinions, not skills. Cap at 30 min/day. |
| Building a framework before building a product | Feels like infrastructure | Premature abstraction. Build the thing, extract the pattern later. |
| Chasing every new model release | Feels like staying current | Model upgrades rarely change what you should build. Check monthly, not daily. |
| Perfecting Sprint 1 before moving to Sprint 2 | Feels like quality | 80% working is enough. Move forward, come back later. |
| Selling before you have a demo | Feels like validation | You need proof, not promises. Build first, sell from evidence. |
| Building in private | Feels safe | Nobody knows you exist. Ship publicly from day one. |

---

## Success Metrics at Day 14

| Metric | Minimum | Strong |
|--------|---------|--------|
| Working integrations | 5 | 7+ |
| Agent runs logged with traces | 100 | 500+ |
| Real users of at least one deployed system | 1 | 3+ |
| Public posts / artefacts | 3 | 8+ |
| Gate 0 ideas generated from building | 2 | 5+ |
| Gate 1 survivors | 1 | 2+ |
| Inbound conversations from public content | 1 | 5+ |

---

## Daily Rhythm

| Time | Activity |
|------|--------|
| First 15 min | Review: what shipped yesterday, what is blocked, what is the single most important thing today |
| Morning block | Build. The hardest or most uncertain task of the day goes here. |
| Afternoon block | Build. Integrations, tests, or deployment work. |
| Last 30 min | Log: 1 observation for the idea pipeline + 1 short-form post or note about what you built today |
| Evening (optional) | Explore: 1 high-quality source, video, or competitor teardown. Cap at 30 min. |

---

## How This Connects to the Business

The department-by-department SME thesis (idea-002) is now the selected business direction. This plan is the execution layer for validating it.

After 14 days:
- If the onboarding-first wedge still holds, you have the full stack to build V1 immediately
- If a better idea emerged from building, you pivot with full capability and proven components
- If someone approaches you with a problem, you can say "I built exactly this last week" instead of "I could build that"

The business follows the capability. The capability comes from building real things, not from finding the perfect idea first.
