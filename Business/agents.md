# AgentForge — Agentic Product Operating System

> This workspace IS the operating system for building AgentForge — a company that builds departmental AI agents for SMEs. Every department is a set of **skills** an AI agent can adopt — defined by Directives (what to do), Executions (how to do it), and Resources (reference material).

---

## What Is AgentForge?

AgentForge builds department-specific AI execution agents for small and mid-size businesses. Instead of selling a generic "AI platform," AgentForge starts with one department (Delivery / Client Onboarding), proves ROI with real business use cases built in public, then expands into adjacent departments until the product becomes a multi-department agentic operating system for SMEs.

**Core thesis**: Build departmental agents in public with real business use cases, starting with onboarding.

**Origin**: Spun out of the Hedge Edge strategy pipeline as idea-002 (Departmental Agents in Public for SMEs).

---

## DOE Framework — Directives, Executions, Resources

Every department follows the same **D·O·E** pattern:

| Layer | Folder | Purpose |
|-------|--------|---------|
| **Directives** | `directives/` | SOPs — what to do and why |
| **Executions** | `executions/` | Scripts and code — how to do it |
| **Resources** | `resources/` | Reference material, configs, templates |
| **SKILL.md** | Root of dept | Skill Command Sheet — ties DOE together as adoptable skills |

Each department's `SKILL.md` is the entry point. Read it to understand what skills you gain by adopting that department.

## Governance Model

- **Orchestrator owns structure**: Only Orchestrator may change cross-department DOE structure, move files between departments, or rewrite `SKILL.md` files.
- **Department agents own content**: Engineering, Product, Delivery, and Content can improve directives, executions, and resources inside their domain.
- **Structural source of truth**: When the workspace layout changes, update `Business/agents.md`, `Business/ORCHESTRATOR/SKILL.md`, and the affected department `SKILL.md` files through Orchestrator.

---

## Department Map

```
Business/
├── ENGINEERING/         Core tech — agent framework, integrations, approval engine, eval harness
│   └── SKILL.md         Skills: agent executor, tool integrations, approval flows, eval/observability, multi-agent orchestration
│
├── PRODUCT/             Product management — customer discovery, requirements, roadmap, feedback
│   └── SKILL.md         Skills: customer interviews, use case mapping, requirements, roadmap, feedback loops
│
├── DELIVERY/            DevOps & production — deployment, monitoring, observability, infrastructure
│   └── SKILL.md         Skills: deployment, monitoring, tracing, alerting, production ops
│
├── CONTENT/             Public building — blog posts, case studies, open source, social media
│   └── SKILL.md         Skills: case studies, technical posts, social content, open source releases
│
└── ORCHESTRATOR/        Central nervous system — sprint coordination, routing, cross-department workflows
    └── SKILL.md         Skills: sprint management, agent routing, task decomposition, status reporting
```

---

## Root-Level Folders (Outside Business/)

| Folder | Purpose |
|--------|---------|
| `shared/` | Shared Python/JS libraries used by all departments |
| `tmp/` | Temporary scratchpad — not persistent |
| `.github/agents/` | VS Code Copilot agent definitions (one per department) |
| `.env` | Master environment variables (all API keys) |

---

## How to Use This Workspace

1. **Pick a department** → Read its `SKILL.md`
2. **Pick a skill** → Follow the directive, run the execution, consult the resource
3. **Cross-department work** → Orchestrator routes multi-agent requests
4. **Shared code** → All departments import from root `shared/` package

---

## Key Infrastructure

| Service | Purpose | Config |
|---------|---------|--------|
| Supabase | Database, auth, telemetry | `.env` |
| Notion | CRM, dashboards, task logs | `.env` |
| Discord | Community, alerts | `.env` |
| Resend | Email delivery | `.env` |
| GitHub | Code, releases, CI/CD | `.env` |
| Vercel | Web hosting | `.env` |
| Railway | Always-on services | `.env` |
| HubSpot | CRM integration target | `ENGINEERING/resources/.env` |
| Slack | Communication integration target | `ENGINEERING/resources/.env` |
| Google Workspace | Gmail/Drive/Calendar integration target | `ENGINEERING/resources/.env` |
| Asana/Linear | Project management integration target | `ENGINEERING/resources/.env` |
| Stripe/Xero | Payment/invoicing integration target | `ENGINEERING/resources/.env` |

---

## Active Sprint

**14-Day Blitz** (see `ORCHESTRATOR/resources/sprint-plan.md`)

| Days | Focus | Lead Agent |
|------|-------|------------|
| 1–2 | Agent core + first 3 integrations | ENGINEERING |
| 3–4 | Remaining integrations + approval engine | ENGINEERING |
| 5–6 | Observability + evaluation harness | DELIVERY |
| 7–9 | Multi-agent orchestration | ENGINEERING + ORCHESTRATOR |
| 10–12 | First real deployment | DELIVERY + PRODUCT |
| 13–14 | Case study + public artefacts | CONTENT + PRODUCT |
