# Hedge Edge — Business Operating System

> This workspace IS the operating system for Hedge Edge. Every department is a set of **skills** an AI agent can adopt — defined by Directives (what to do), Executions (how to do it), and Resources (reference material).

---

## What Is Hedge Edge?

Hedge Edge is a UK-based SaaS platform for proprietary trading firm traders. The product is a Windows desktop application (Electron) that helps traders hedge their drawdown exposure. Revenue comes from subscriptions (Creem.io) and IB commission deals with brokers (Vantage Markets, BlackBull Markets).

---

## DOE Framework — Directives, Executions, Resources

Every department follows the same **D·O·E** pattern:

| Layer | Folder | Purpose |
|-------|--------|---------|
| **Directives** | `directives/` | SOPs — what to do and why |
| **Executions** | `executions/` | Python scripts — how to do it |
| **Resources** | `resources/` | Reference material, configs, and notebooks; when a department defines terminal-only execution, those notebooks are reference artifacts rather than the live operating path |
| **SKILL.md** | Root of dept | Skill Command Sheet — ties DOE together as adoptable skills |

Each department's `SKILL.md` is the entry point. Read it to understand what skills you gain by adopting that department.

If a department directive or `SKILL.md` defines a terminal-only execution rule, use the terminal workflow for live work and treat any linked notebooks as reference-only.

## Governance Model

- **Orchestrator owns structure**: Only Orchestrator may change cross-department DOE structure, move files between departments, or rewrite `SKILL.md` files to describe new folder ownership and what each folder now does.
- **Department agents own content**: Analytics, Finance, Growth, and Strategy can improve directives, executions, and resources inside their domain, but they do not own cross-department structural edits.
- **Structural source of truth**: When the workspace layout changes, update `Business/agents.md`, `Business/ORCHESTRATOR/SKILL.md`, and the affected department `SKILL.md` files through Orchestrator.

---

## Department Map

```
Business/
├── ANALYTICS/          Measurement engine — KPIs, attribution, funnels, reporting
│   └── SKILL.md        10 skills: KPI snapshots, attribution, email analytics, GA4, funnels, licensing, pipelines, A/B tests, reporting, platform activation
│
├── FINANCE/            Money flows — revenue tracking, IB commissions, expenses, invoicing
│   └── SKILL.md        5 skills: IB commissions, MRR tracking, expenses, financial reporting, invoicing
│
├── GROWTH/             Revenue engine — Marketing (awareness→lead) + Sales (lead→customer)
│   └── SKILL.md        14 skills: email marketing, beta keys, attribution, landing pages, Twitter/X, LinkedIn, Discord, content, feedback, metrics, onboarding, CRM, leads, calls
│
├── ORCHESTRATOR/       Central nervous system — routing, coordination, deployment, monitoring
│   └── SKILL.md        8 skills: agent routing, coordination, task decomposition, status, error handling, VPS, cron, app deployment
│
└── STRATEGY/           Brain — competitive intel, legal compliance, product management
    └── SKILL.md        13 skills: business context, revenue optimisation, research engine, GDPR, FCA, IB agreements, legal KB, roadmap, bug triage, QA, releases, app deploy, platforms
```

---

## Root-Level Folders (Outside Business/)

| Folder | Purpose |
|--------|---------|
| `shared/` | Python API clients used by all departments (Notion, Supabase, Discord, Resend, etc.) |
| `tmp/` | Temporary scratchpad scripts — not persistent |
| `.github/agents/` | VS Code Copilot agent definitions (one per department/role) |
| `.github/skills/` | Repo-local Copilot skills for reusable workflows |
| `.env` | Master environment variables (all API keys) |

---

## How to Use This Workspace

1. **Pick a department** → Read its `SKILL.md`
2. **Pick a skill** → Follow the directive, run the execution, consult the resource
3. **Cross-department work** → Orchestrator routes multi-agent requests
4. **Shared clients** → All departments import from root `shared/` package

### GROWTH Sub-Department Layout

- `Business/GROWTH/directives/Marketing` and `Business/GROWTH/directives/Sales` hold SOPs by funnel stage
- `Business/GROWTH/executions/Marketing` and `Business/GROWTH/executions/Sales` hold runnable workflows by sub-department
- `Business/GROWTH/resources/Marketing` and `Business/GROWTH/resources/Sales` hold human-facing references by sub-department
- `Business/GROWTH/resources/.env` remains the shared runtime override file for Growth workflows

---

## Key Infrastructure

| Service | Purpose | Config |
|---------|---------|--------|
| Supabase | Auth, database, beta keys | `.env` |
| Notion | CRM, dashboards, task logs | `.env` |
| Creem.io | Payment processing | `.env` |
| Discord | Community, alerts, support bot | `.env` |
| Resend | Email delivery | `.env` |
| Railway | Cron container, email service | `shared/Email-Send-Service/` |
| Vercel | Landing page hosting | `.env` |
| GitHub | Code, releases, CI/CD | `.env` |
| VPS (hedge-vps) | Always-on services, Twitter bots, mention bot | SSH via Cloudflare tunnel to Windows host + WSL Docker (NEVER Tailscale) |
