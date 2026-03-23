# STRATEGY — Skill Command Sheet

> **Adopt this department to gain**: Competitive intelligence, growth modelling, legal compliance, product management, market research, and investor-grade strategic analysis skills.

---

## Skills You Gain

STRATEGY is the brain of Hedge Edge. It houses three domains: **Business Strategy** (where to go), **Legal & Compliance** (can we legally go there), and **Product** (what to build to get there).

---

### BUSINESS STRATEGY SKILLS

#### Skill 1 — Business Context & Vision
- **Directive**: `directives/Business/What is Hede Edge.md` — company vision, product overview, ASE architecture
- **Resource**: `resources/hedge-edge-business-context.md` — comprehensive business context document

#### Skill 2 — Revenue Optimisation
- **Directive**: `directives/Business/revenue-optimization.md` — pricing strategy, monetisation models

#### Skill 3 — Powerhouse Research Engine
- **Executions**: `executions/deep_researcher.py` (multi-source deep research with research/brief/analyse modes), `executions/competitor_intel.py` (competitive intelligence: scan/deep-dive/matrix/moat), `executions/trend_scanner.py` (industry/fintech/regulatory/macro trends), `executions/swot_analyzer.py` (SWOT, PESTEL, Porter's 5 Forces, Blue Ocean), `executions/investor_wisdom.py` (channel 8 legendary investors: Buffett/Munger/Dalio/Soros/Marks/Thiel/Bezos/Grove), `executions/buffett_letters.py` (Berkshire shareholder letter analysis)

---

### LEGAL & COMPLIANCE SKILLS

#### Skill 4 — GDPR & Data Protection
- **Execution**: `executions/Legal/gdpr_compliance_checker.py` — audit processing activities against UK GDPR
- **Resources**: `resources/Legal/uk-gdpr-summary.md`, `resources/Legal/data-processing-register.md`, `resources/Legal/dsar-process.md`, `resources/Legal/privacy-policy-template.md`

#### Skill 5 — FCA Financial Promotions
- **Execution**: `executions/Legal/financial_promotions_auditor.py` — FCA COBS 4 compliance audit
- **Resources**: `resources/Legal/fca-financial-promotions.md`, `resources/Legal/risk-disclaimers.md`

#### Skill 6 — IB Agreement & Regulatory
- **Resources**: `resources/Legal/ib-agreement-checklist.md`, `resources/Legal/prop-firm-regulatory-landscape.md`, `resources/Legal/terms-of-service-template.md`

#### Skill 7 — Legal Knowledge Base
- **Executions**: `executions/Legal/legal_query_engine.py` (RAG-powered legal Q&A), `executions/Legal/enrich_legal_notebook.py` (feed docs into legal NotebookLM), `executions/Legal/setup_legal_notebook.py` (initialise NotebookLM)
- **Resource**: `resources/Legal/legal_compliance_guide.ipynb` — interactive legal compliance notebook

---

### PRODUCT SKILLS

#### Skill 8 — Feature Roadmap & Planning
- **Directive**: `directives/Product/feature-roadmap.md` — feature prioritisation, planning cycles

#### Skill 9 — Bug Triage
- **Directive**: `directives/Product/bug-triage.md` — severity matrix, response SLAs

#### Skill 10 — QA & Test Automation
- **Directive**: `directives/Product/qa-automation.md` — test strategy, CI/CD quality gates

#### Skill 11 — Release Management
- **Directive**: `directives/Product/release-management.md` — release process, versioning, rollback

#### Skill 12 — App Deployment
- **Directive**: `directives/Product/app-deploy.md` — Electron app deploy pipeline (bump, build, release, verify)
- **Execution**: `executions/Product/app_deployer.py` — deploy pipeline automation
- **Resources**: `resources/Product/app-deployment-reference.md`, `resources/Product/ea-installation-guide.md`, `resources/Product/hedging-explained.md`, `resources/Product/product-faq.md`

#### Skill 13 — Platform Integration
- **Directive**: `directives/Product/platform-integration.md` — MT4/MT5/cTrader platform expansion

---

## Dispatcher

`executions/run.py` — routes `--task` flags to execution scripts. Entry point for all Strategy tasks.

## Shared Dependencies

Imports from workspace-root `shared/`: `notion_client.py`, `supabase_client.py`, `llm_router.py`, `gemini_client.py`, `openrouter_client.py`.

## Cross-Department Links

| Department | Strategy Provides | Strategy Needs |
|------------|------------------|----------------|
| ALL | Strategic direction, compliance guardrails | Execution data |
| FINANCE | IB agreement terms, pricing models | MRR and commission data |
| GROWTH | Positioning, messaging, target segments | User feedback, campaign results |
| ANALYTICS | KPI targets, metric definitions | KPI actuals, trend data |
| ORCHESTRATOR | Release priorities, roadmap | Deploy capabilities |
