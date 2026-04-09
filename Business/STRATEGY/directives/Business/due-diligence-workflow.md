# Due Diligence Workflow — Idea-to-Validation Pipeline

> **Purpose**: A repeatable, gate-based process to evaluate business ideas with rigorous research before any capital or engineering time is committed. Born from the Hedge Edge lesson: structural competitive advantage must be validated before building.

> **Non-Negotiable Entry Criteria** — Every idea must clear these before it enters Gate 1:
> 1. Must have a credible path to **B2B or prosumer recurring revenue**
> 2. Must **not** depend on a single platform's terms of service for survival
> 3. Must have a plausible path to a **proprietary data moat, network effect, or regulatory barrier**
> 4. Must target a market where the **customer's cost of the problem exceeds $1,000/year**
> 5. Must be buildable to MVP with **≤3 months of solo/lean-team effort**

---

## Pipeline Overview

```
GATE 0          GATE 1           GATE 2            GATE 3             GATE 4
Idea Capture → Quick Kill    → Deep Research   → Full Business   → Contained
(30 min)       Screen (2 days)  (5 days)          Case (5 days)      Test (2-4 wks)
               ↓ KILL/GO        ↓ KILL/GO         ↓ KILL/GO          ↓ KILL/GO
               ~90% killed      ~70% killed       ~50% killed        Final verdict
```

**Target throughput**: 10 ideas per month enter Gate 0. 1-2 survive to Gate 4 per quarter.

---

## GATE 0 — Idea Capture (30 minutes)

**Action**: Fill out the first section of the Idea Evaluation Template (`resources/idea-evaluation-TEMPLATE.md`).

**What you write**:
- One-sentence problem statement
- Who has this problem (be specific: job title, industry, company size)
- How they currently solve it (the status quo)
- Why now — what changed (regulation, technology, market shift)
- Your unfair advantage to build this (domain knowledge, existing code, relationships)

**Output**: A new file in `resources/IdeaPipeline/` named `idea-{NNN}-{short-name}.md` copied from the template.

**Decision**: Does it pass the 5 Non-Negotiable Entry Criteria? If no → KILL. If yes → Gate 1.

---

## GATE 1 — Quick Kill Screen (2 working days max)

**Objective**: Rapidly disqualify ideas that fail basic market or structural tests before investing research time.

### Day 1: Market Existence Check
Research using these sources (in priority order):

| Source | What to Extract | URL / Access |
|--------|----------------|--------------|
| **Crunchbase** | Competitors, funding rounds, market validation | crunchbase.com |
| **Google Trends** | Search volume trajectory for core problem terms | trends.google.com |
| **Reddit / HackerNews** | Organic complaints about the problem (r/SaaS, r/startups, HN "Ask") | reddit.com, news.ycombinator.com |
| **G2 / Capterra** | Existing solutions, review sentiment, pricing benchmarks | g2.com, capterra.com |
| **LinkedIn Sales Navigator** | Target buyer persona count, company count in segment | linkedin.com |

### Day 2: Structural Moat Assessment
Answer these 5 questions (1 paragraph each):

1. **Winner-take-all dynamics?** Does this market reward a single dominant player (network effects) or can many coexist?
2. **Switching costs?** Once a customer is using the product, what would it cost them to leave? (Data migration, retraining, integration rewiring)
3. **Data advantage?** Does usage generate proprietary data that makes the product better over time?
4. **Regulatory barrier?** Are there licences, certifications, or compliance burdens that slow competitors?
5. **Distribution advantage?** Can you reach customers through a channel competitors cannot easily replicate?

**Scoring**: Each question scores 0 (none), 1 (weak), or 2 (strong). Total /10.
- Score ≤ 2 → **KILL** (no structural advantage possible)
- Score 3-4 → **CONDITIONAL** (proceed only if market size is very large)
- Score ≥ 5 → **GO** to Gate 2

**Output**: Update the idea file with Gate 1 results. Mark status as KILLED or GATE 2.

---

## GATE 2 — Deep Market Research (5 working days)

**Objective**: Build an evidence-based understanding of the market, customers, and competitive landscape before writing a business case.

### Day 1-2: Market Sizing (TAM → SAM → SOM)

**Reputable Sources for Market Data**:

| Source | Best For | Access |
|--------|----------|--------|
| **Statista** | Market size estimates, industry statistics | statista.com (paid, but previews are useful) |
| **IBISWorld** | Industry reports with revenue, growth rates, competitive landscape | ibisworld.com |
| **Grand View Research / Mordor Intelligence** | TAM projections by vertical | grandviewresearch.com, mordorintelligence.com |
| **SEC EDGAR / Companies House** | Competitor financials (public companies or UK filings) | sec.gov, find-and-update.company-information.service.gov.uk |
| **S-1 Filings** | IPO prospectuses with granular market data | sec.gov/cgi-bin/browse-edgar |
| **PitchBook / CB Insights** | VC deal flow, market maps, emerging categories | pitchbook.com, cbinsights.com |
| **SaaS Capital Index** | SaaS valuation multiples and benchmarks | saas-capital.com |
| **BIS / World Bank / OECD** | Macro-level financial and economic data | bis.org, worldbank.org, oecd.org |

**Deliverable**: TAM/SAM/SOM table with sources cited. Conservative, base, and optimistic cases.

### Day 3-4: Competitive Landscape

Use the **Powerhouse Research Engine** (Skill 3):
- `competitor_intel.py --action matrix` — build comparison matrix
- `competitor_intel.py --action moat` — assess each competitor's defensibility
- `deep_researcher.py --mode analyse` — synthesise findings

**Build a Competitor Matrix** with these columns:

| Competitor | Founded | Funding | Revenue Est. | Customers | Pricing | Platform | Moat Type | Weakness |
|-----------|---------|---------|-------------|-----------|---------|----------|-----------|----------|

**Deliverable**: Completed competitor matrix. Identify the gap — what are all competitors bad at?

### Day 5: Customer Discovery Interviews

- Reach out to **5 potential customers** minimum (LinkedIn, Reddit, industry Discord/Slack)
- Use the Mom Test framework: ask about their *past behaviour*, not whether they'd *hypothetically* buy
- Key questions:
  1. "What's the most time-consuming part of [problem area] for you?"
  2. "How much do you currently spend solving this?"
  3. "What have you tried that didn't work?"
  4. "If this problem disappeared tomorrow, what would change for your business?"

**Deliverable**: Interview summaries. Pattern analysis across responses.

**Gate 2 Decision**:
- Market too small (SOM < $10M) → **KILL**
- No clear gap in competitor landscape → **KILL**
- Customers don't confirm the pain → **KILL**
- Otherwise → **GO** to Gate 3

---

## GATE 3 — Full Business Case (5 working days)

**Objective**: Produce a comprehensive business plan document identical in rigour to `What is Hede Edge.md`.

**Use the template**: Copy `resources/idea-evaluation-TEMPLATE.md` sections into a full write-up. The required sections mirror the Hedge Edge document:

### Required Sections (1 day each):

| Day | Section | Content |
|-----|---------|---------|
| 1 | **Product & Service** | What it is, unique advantages, ease of imitation, technology risks |
| 2 | **Market & Competitors** | General market, target segment, geographic scope, segment size, buying patterns, competitor analysis (Tier 1 & 2), competitive dimensions, comparison table |
| 3 | **Business Model** | Revenue streams, pricing, unit economics, CAC/LTV projections |
| 4 | **Risk, Return, Exit** | Market risk, regulatory risk, replication risk, dependency risk, return case, exit routes |
| 5 | **Moat Strategy** | Honest moat assessment (score /10), path to defensibility, timeline to moat |

### Quality Standard
The finished document must meet the same standard as the Hedge Edge write-up:
- Every factual claim has a cited source
- Risks are stated honestly, not minimised
- Competitor analysis is evidence-based, not dismissive
- The moat assessment is brutally honest (remember: Hedge Edge scored 2/10)

**Gate 3 Decision**:
- Moat score ≤ 2 with no credible path to improve → **KILL**
- Unit economics don't work (CAC > LTV) → **KILL**
- Risk profile unacceptable (single point of failure, legal exposure) → **KILL**
- Otherwise → **GO** to Gate 4

---

## GATE 4 — Contained Test (2-4 weeks)

**Objective**: Validate demand with real market signals before building the product.

### Test Options (pick one):

| Test Type | Effort | Signal Quality | Method |
|-----------|--------|---------------|--------|
| **Landing Page + Waitlist** | 2-3 days build | Medium | Drive traffic via ads ($200-500 budget), measure signup rate |
| **Concierge MVP** | 1-2 weeks | High | Deliver the service manually to 5-10 customers, charge real money |
| **Wizard of Oz** | 1-2 weeks | High | Build the UI, but fulfil requests manually behind the scenes |
| **Pre-sale** | 1 week | Very High | Sell annual subscriptions before building; refund if you don't build |
| **Cold Outreach** | 3-5 days | Medium-High | Email/LinkedIn 100 prospects with a specific offer, measure response rate |

### Success Metrics (define before testing):

| Metric | Minimum Threshold | Strong Signal |
|--------|------------------|--------------|
| Landing page conversion (visitor → signup) | ≥ 5% | ≥ 15% |
| Concierge willingness to pay | ≥ 3/10 customers pay | ≥ 6/10 pay |
| Pre-sale conversion | ≥ 2% of outreach | ≥ 5% of outreach |
| Cold outreach response rate | ≥ 10% reply | ≥ 25% reply |

### Spend Caps
- **Maximum test budget**: $500 (ads, tools, domain)
- **Maximum time**: 4 weeks
- **Maximum code written**: Landing page + basic API only. No product engineering.

**Gate 4 Decision**:
- Below minimum thresholds → **KILL**
- Meets minimum but not strong → **CONDITIONAL** (run a second test variant)
- Hits strong signal → **GO TO BUILD** (begin product engineering)

---

## Sources Reference Card

### Tier 1 — High Authority (always use)
| Source | Domain | Notes |
|--------|--------|-------|
| SEC EDGAR / Companies House | Financials | Verified filings, not estimates |
| BIS / World Bank / OECD | Macro data | Central bank grade |
| Government statistical offices | Demographics, industry data | ONS (UK), BLS (US), Eurostat (EU) |
| Academic databases (SSRN, Google Scholar) | Research papers | Peer-reviewed or working papers |

### Tier 2 — Industry Standard (use with cross-reference)
| Source | Domain | Notes |
|--------|--------|-------|
| Crunchbase, PitchBook, CB Insights | Startup/VC data | Self-reported; verify key claims |
| Statista, IBISWorld | Market sizing | Methodology varies; cite the methodology |
| SaaS Capital, OpenView, Bessemer | SaaS benchmarks | Reputable but US-centric |
| G2, Capterra, Trustpilot | Product reviews | Sample bias; useful for sentiment, not sizing |

### Tier 3 — Signal Sources (directional only)
| Source | Domain | Notes |
|--------|--------|-------|
| Reddit, HN, Discord, Twitter/X | Customer pain signals | Anecdotal; never cite as market data |
| YouTube, podcasts, blogs | Trend spotting | Filter for substance vs hype |
| Google Trends, SimilarWeb | Traffic/interest proxy | Relative, not absolute |

**Rule**: Every factual claim in a Gate 3 document must cite at least one Tier 1 or Tier 2 source. Tier 3 sources support narrative only.

---

## File Naming & Storage

```
resources/IdeaPipeline/
  idea-001-{short-name}.md        ← Gate 0-2 evaluation (from template)
  idea-002-{short-name}.md
  ...
  pipeline-tracker.md             ← Master status tracker

directives/Business/
  due-diligence-workflow.md       ← This file (the process)
  {short-name}-business-case.md   ← Gate 3 output (full write-up, same standard as "What is Hede Edge.md")
```

---

## Lessons from Hedge Edge

These are codified learnings that must be checked against every new idea:

1. **"No moat" is not "no business" — but it is "no defensible business."** Hedge Edge scored 2/10 on moat. The product worked; the competitive position did not.
2. **Platform dependency is existential risk.** If a third party (prop firms, app stores, APIs) can ban your use case overnight, your business is a tenant, not an owner.
3. **B2C in niche markets is a grind.** Retail traders churn fast, are price-sensitive, and are expensive to acquire. B2B customers have budgets and contracts.
4. **Timing advantage ≠ moat.** Being first only matters if you can convert that lead into switching costs, data advantages, or network effects before competitors arrive.
5. **The research would have caught it.** A rigorous Gate 2-3 process applied to Hedge Edge in mid-2025 would have identified the 2/10 moat score, the prop-firm TOS risk, and the replication risk before engineering began.
