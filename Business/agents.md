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
| **Resources** | `resources/` | Reference material, configs, notebooks |
| **SKILL.md** | Root of dept | Skill Command Sheet — ties DOE together as adoptable skills |

Each department's `SKILL.md` is the entry point. Read it to understand what skills you gain by adopting that department.

---

## Department Map

```
Business/
├── ANALYTICS/          Measurement engine — KPIs, attribution, funnels, reporting
│   └── SKILL.md        9 skills: KPI snapshots, attribution, email analytics, GA4, funnels, licensing, pipelines, A/B tests, reporting
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
| `.env` | Master environment variables (all API keys) |

---

## How to Use This Workspace

1. **Pick a department** → Read its `SKILL.md`
2. **Pick a skill** → Follow the directive, run the execution, consult the resource
3. **Cross-department work** → Orchestrator routes multi-agent requests
4. **Shared clients** → All departments import from root `shared/` package

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
| VPS (hedge-vps) | Always-on services | SSH via Cloudflare tunnel (NEVER Tailscale) |
