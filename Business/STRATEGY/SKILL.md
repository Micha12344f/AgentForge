# STRATEGY — Skill Command Sheet

> **Adopt this department to gain**: Competitive intelligence, growth modelling, legal compliance, product management, market research, and investor-grade strategic analysis skills.

> **Governance note**: Strategy owns strategy content. Orchestrator alone owns cross-department DOE restructuring and any `SKILL.md` rewrite that changes folder-role mapping or explains what folders now do.

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

#### Skill 14 — PropFirmMatch Exploration
- **Directive**: `directives/Business/propfirmmatch-exploration.md` — reconnaissance workflow for site mapping, filter validation, schema discovery, and custom-table inspection before scraper changes
- **Executions**: `executions/propmatch_site_explorer.py` (surface mapping + filter matrix capture), `executions/propmatch_deep_explorer.py` (deep discovery across pagination, firm pages, rules, and adjacent surfaces), `executions/propmatch_custom_table_explorer.py` (manual-login custom-table and hidden-column discovery)
- **Resources**: `resources/PropFirmMatchExploration/` — promoted site-map seed, exploration snapshots, screenshots, and schema artifacts

#### Skill 15 — Prop Firm Hedge Arbitrage (CFD/Forex)
- **Directive**: `directives/Business/prop-firm-hedge-arbitrage.md` — hedge arbitrage modelling SOP (EV, break-even, optimal hedge ratios)
- **Executions**: `executions/propmatch_scraper.py` (Playwright scraper for PropMatch challenge data), `executions/hedge_arbitrage_model.py` (EV model, break-even, comparison matrix, full pipeline)
- **Notebooks** (run in order or individually):
  - `resources/PropFirmData/type_a_challenge_insurance.ipynb` — Type A: challenge-only insurance, 8% funded target, static/trailing DD, top-30 EV rankings, capital efficiency, sensitivity sweep
  - `resources/PropFirmData/type_b_funded_recovery.ipynb` — Type B: extends Type A into 6 funded cycles (4% withdrawal, 80% survival, 1.5% drag); recovers full cost stack on failure
  - `resources/PropFirmData/type_c_funded_surplus.ipynb` — Type C: Type B + 2% surplus buffer; hedge covers stack + surplus, drag scales by (L+P)/L
- **Resources**: `resources/PropFirmData/` — scraped JSON/CSV (`propmatch_challenges_*.json`), model outputs

#### Skill 16 — Futures Hedge Model
- **Directive**: `directives/Business/futures-hedge-model.md` — futures-specific hedge model with trailing DD compounding, consistency rules, payout caps, and activation fees
- **Executions**: `executions/propmatch_scraper.py --action scrape-futures` — scrapes across all 8 account sizes ($25K–$300K) with discounts disabled
- **Notebooks** (run in order or individually):
  - `resources/PropFirmData/type_a_futures_insurance.ipynb` — Type A: futures challenge insurance; $-based targets/DD, per-contract spread, payout cap mechanics, cycles-to-recover
  - `resources/PropFirmData/type_b_futures_recovery.ipynb` — Type B: futures funded recovery; payout-cap-aware withdrawals, 6-cycle survival model
  - `resources/PropFirmData/type_c_futures_surplus.ipynb` — Type C: futures surplus hedge; unified B/C model with surplus_target_pct parameter
- **Resources**: `resources/PropFirmData/futures_hedge_model.ipynb` — general reference notebook; `resources/PropFirmData/propmatch_futures_*.json` — scraped futures challenge data (76 challenges, 8 account sizes)

#### Skill 17 — Instant Funded Hedge Model
- **Directive**: `directives/Business/instant-funded-hedge-model.md` — instant-funded account model for upfront-fee economics, static vs trailing funded drawdown, and optional consistency-rule stress testing
- **Resources**: `resources/PropFirmData/instant_funded_hedge_model.ipynb` — interactive notebook ingesting scraped FX challenges filtered to `steps_label = Instant` and ranking first-payout EV (63 offers, 5% payout target, 100x leverage capital model)

#### Skill 18 — Consolidated Cross-Asset Hedge Analysis
- **Directive**: `directives/Business/propfirm-consolidated-analysis.md` — SOP for running all 7 models (FX Type A/B/C + Futures Type A/B/C + Instant-Funded) in a single pipeline and generating a PDF report
- **Execution**: `resources/PropFirmData/consolidated_report.py` — runs all 7 models from latest scraped JSON files, generates 12 charts, and exports a 27+ page PDF with executive summary, per-asset deep dives, statistical analysis, and ranked recommendations
- **Output**: `resources/PropFirmData/HedgeEdge_Consolidated_Report_{date}.pdf` — latest consolidated PDF (1MB+; includes EV distributions, Top 25 opportunities, firm heatmap, fee-vs-EV, capital efficiency scatter, drawdown-type impact, profit-split analysis)
- **Charts**: `resources/PropFirmData/_charts/` — 12 exported PNG charts (boxplot, bar, heatmap, scatter, histogram, grouped-bar)
- **Run command**: `python Business/STRATEGY/resources/PropFirmData/consolidated_report.py`
- **When to use**: After any scraper refresh; for board-level reporting; when comparing opportunities across asset classes; before deploying capital into new prop-firm challenges

#### Skill 19 — Budget-Constrained Prop Firm Selection (Hedge-Adjusted)

> **MANDATORY WORKFLOW** — Apply this skill whenever a user asks: "I have $X budget, what challenge should I get?", "what can I afford?", "I need money fast — what should I buy?", or any variant where a budget ceiling is given and a prop firm challenge is being selected.

**The core rule**: A stated budget of $X is **never interpreted as fee only**. It must be applied against the **full hedge cost stack** — the total capital consumed across all phases including challenge fees, activation fees (futures), and accumulated hedge losses. Only challenges where `total_hedge_cost ≤ $X` qualify.

##### Step 1 — Identify All Data Sources

Load the latest scraped files for **all three asset classes**:
- FX/Forex challenges: `resources/PropFirmData/propmatch_challenges_*.json` (Skills 15, 17)
- Futures challenges: `resources/PropFirmData/propmatch_futures_*.json` (Skill 16)
- Filter Instant-funded rows (`steps_label = "Instant"`) from the FX file for Skill 17 treatment

Compare **across all account size variants** for every firm — do not pre-filter by account size. A $50K variant of a firm may fit the budget when the $100K variant does not.

##### Step 2 — Compute Full Hedge Cost Stack Per Challenge

For each candidate challenge, compute `total_hedge_cost` using the deterministic phase model:

**FX Multi-Phase (Skill 15):**
```
L_1 = fee
For each phase n (eval → funded):
    S_n = L_n / max_drawdown_pct          # hedge size
    hedge_loss_n = S_n × profit_target_n + friction_n
    L_{n+1} = L_n + hedge_loss_n          # cost stack compounds
total_hedge_cost = L_final
```

**Futures (Skill 16) — add activation fee + trailing DD compounding:**
```
L_1 = fee + activation_fee
Walk N daily increments (target / N per step):
    hedge_size = L / max_loss
    daily_loss = hedge_size × (daily_target / account_size)
    spread_loss = max_contracts_minis × cost_per_contract
    L = L + daily_loss + spread_loss
total_hedge_cost = L_final
```

**Instant-Funded (Skill 17) — no eval phase, single funded leg:**
```
L = fee
S = L / max_drawdown_pct
hedge_loss = S × first_payout_target_pct + friction
total_hedge_cost = L + hedge_loss
```

Default assumptions when live model is not run:
- FX funded target: 8% of account
- Futures funded target: 6% of account
- Instant funded first-payout target: 5% of account
- FX spread friction: 0.03% per phase
- Futures spread friction: $5/contract round-trip

##### Step 2b — Drawdown Type Pre-Filter (MANDATORY)

Before computing any costs, classify each challenge's `drawdown_type` and exclude non-hedgeable products:

| `drawdown_type` | Hedgeable | Action |
|---|---|---|
| `Balance - EOD` | Yes | Include — full model |
| `Balance/Equity - Highest at EOD` | Mostly yes | Include — EOD-close assumption |
| `Equity - Intraday` / real-time equity trailing | **No** | **Exclude entirely** |

**Why intraday equity trailing is excluded:** The breach distance — which determines hedge notional — is a stochastic process driven by intraday volatility, not net P&L toward target. It can only decrease intraday (floors ratchet on every equity high, never recover). No static or dynamic position strategy produces a deterministic recovery on breach. The true hedge cost is path-dependent and unquantifiable. These are a structurally incompatible product category — do not model or recommend them.

Flagging rule: if `drawdown_type` is absent from the data, default to include but note the assumption. If a firm is known to use intraday equity trailing (e.g. FundingPips Instant Standard), exclude explicitly.

##### Step 3 — Filter, Rank, and Compare

Filter: keep only challenges where `total_hedge_cost ≤ budget`.

Rank by:
1. **EV** = `profit_split_pct × account_size × funded_target_pct − total_hedge_cost` (primary)
2. **Break-even payout %** = `total_hedge_cost / (profit_split_pct × account_size)` (lower = safer)
3. **Payout speed** — score fast payout cadences: daily > on-demand > bi-weekly > 5-day > 7-day > 14-day > 30-day
4. **Capital efficiency** = `EV / total_hedge_cost`

##### Step 4 — Output Format

Always produce a table with these columns:

| Rank | Firm | Account | Asset | Steps | Fee | Hedge Cost | Total Cost | Budget Used | EV | Break-Even% | Split | Payout Speed | Rating |

Then provide:
- **Top pick** with full hedge cost breakdown (fee + per-phase hedge losses)
- **Budget scenarios**: show what the user can afford at `fee only` vs `fee + hedge costs` — explicitly call out if the naive fee-only interpretation would leave the user undercapitalised
- **Cross-asset comparison**: always show at least one FX, one Futures, and one Instant-Funded option if they fit the budget
- **Sensitivity note**: if a challenge is marginal (total_hedge_cost close to budget), flag it as requiring a buffer

##### Example Application

If budget = $500:
- Do NOT just filter `fee ≤ $500`
- Compute total_hedge_cost for each challenge across all variants
- A $399 2-step FX challenge with 8% funded target, 5% max DD, 80% split on $100K has:
  - Phase 1 hedge loss ≈ $399 × (8%/5%) = ~$638 total stack after phase 1
  - Exceeds $500 budget on total cost basis → disqualified unless user has separate trading capital buffer
- Flag which challenges genuinely fit within $500 **including hedge costs**, not just fee

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
