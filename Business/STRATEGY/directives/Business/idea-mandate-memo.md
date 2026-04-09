# IDEA MANDATE MEMO

> **Status**: ACTIVE — Binding filter for all future business idea evaluation  
> **Author**: Ryan + Strategy Agent  
> **Date**: April 2026  
> **Supersedes**: Ad-hoc idea selection  
> **Companion files**: `due-diligence-workflow.md`, `resources/idea-evaluation-TEMPLATE.md`

---

## Preamble

Six months of operating Hedge Edge proved one iron law: **a competitive advantage is not a nice-to-have — it is the entire game.** Hedge Edge scored 2/10 on structural defensibility. Platform dependency (prop firm TOS), B2C churn, and zero switching costs made the product trivially replicable and commercially fragile. This memo converts those failures into binding objectives, hard constraints, and a targeted research plan so that the next venture is chosen with evidence, not enthusiasm.

Every idea entering the Due Diligence Pipeline (Skill 20, Gate 0+) must pass through this memo's filter **before** any code is written or capital deployed.

---

## I. Objectives

Each objective inverts a specific Hedge Edge failure.

### Objective 1 — Structural Moat (≥ 6/10 on Moat Scorecard)

**Hedge Edge failure**: Moat score 2/10. No network effects, no proprietary data, no switching costs. Any developer could replicate the copier in a weekend.

**Mandate**: The next idea must possess **at least two** of the following structural advantages from Hamilton Helmer's 7 Powers framework:

| Power | Definition | Applicability Test |
|-------|-----------|-------------------|
| **Scale Economies** | Unit costs decline with volume; a smaller rival cannot match pricing at the same margin | Does doubling users halve per-unit cost? |
| **Network Economies** | Each additional user increases value for all existing users (direct or indirect) | Would the 1,000th customer make the product materially better for customer #1? |
| **Counter-Positioning** | Newcomer adopts a business model that an incumbent cannot copy without cannibalising its core | Would a legacy player have to sacrifice existing revenue to match you? |
| **Switching Costs** | The expected loss from switching (data migration, retraining, integration rewiring, workflow disruption) exceeds the expected gain | If a competitor offered a free trial, would customers still stay because switching is too painful? |
| **Branding** | Brand equity permits premium pricing; customers buy partly on trust and reputation | N/A for a day-one startup — deprioritise |
| **Cornered Resource** | Exclusive access to a valuable asset: proprietary dataset, patent, regulatory licence, key talent | Do you own or control something rivals genuinely cannot obtain? |
| **Process Power** | Embedded organisational processes that enable lower costs or superior product quality and are opaque to competitors | Only relevant at scale — deprioritise for Gate 0-2 |

**Priority powers for early-stage SaaS**: Network Economies, Switching Costs, Counter-Positioning, Cornered Resource.

**Minimum bar**: Score ≥ 6/10 on the moat scorecard by Gate 2. Any idea scoring ≤ 4 is killed.

---

### Objective 2 — Platform Independence

**Hedge Edge failure**: 100% dependent on prop firm platforms whose Terms of Service can (and do) change unilaterally. One TOS update could evaporate the entire business overnight.

**Mandate**: No single third-party platform may control more than **30%** of the product's distribution, data access, or core functionality.

**Proxy company evidence:**

- **Zynga → Facebook**: Zynga made up 19% of Facebook's revenue (2011) through a five-year exclusivity deal. When Facebook terminated the special agreement in November 2012, Zynga lost nearly half its user base within a year. Valuation was docked $400M. Stock fell from $14.50 to ~$4. The lesson: building *on* a platform is fine; building exclusively *within* a platform is existential exposure.
- **Apollo → Reddit**: In April 2023, Reddit introduced API pricing ($12,000 per 50M requests). Apollo developer Christian Selig faced $20M/year in API costs. Apollo, Sync, BaconReader, and RIF all shut down on June 30, 2023. There was no negotiation, no transition period, no recourse. 7,000+ subreddit blackout followed, but all third-party apps still died.
- **Third-party Twitter clients → X (2023)**: Twitter replaced its free API with a paid tier in February 2023. Tweetbot, Twitterrific, and dozens of third-party clients were killed instantly — some after 10+ years of development.

**Structural test (Gate 1)**: Map every external dependency. If removing any single dependency kills the product, the idea fails.

---

### Objective 3 — Stabilise Retention and Revenue

**Hedge Edge failure**: B2C model with no switching costs. Customers could churn freely because the product didn't embed into their workflow. No data lock-in, no integrations, no multi-user collaboration.

**Mandate**: The next venture must demonstrate a credible path to:

| Metric | Minimum Threshold | Top-Quartile Target | Source |
|--------|------------------|--------------------|----|
| **Net Revenue Retention (NRR)** | ≥ 100% | ≥ 120% | Bessemer Cloud Index, KeyBanc SaaS Survey |
| **Gross Revenue Retention (GRR)** | ≥ 85% | ≥ 95% | SaaS Capital Index |
| **LTV:CAC Ratio** | ≥ 3:1 | ≥ 5:1 | Industry standard (Bessemer) |
| **CAC Payback Period** | ≤ 18 months (B2B) | ≤ 12 months | KeyBanc, Stripe Atlas |
| **Monthly Logo Churn** | ≤ 3% (B2B) | ≤ 1% | Benchmark: B2C churn is typically 5-8%/month |

**B2C churn ceiling**: If the idea targets consumers (B2C), CAC must be recoverable within **3 months** of subscription revenue. If the model cannot meet this, pivot to B2B/prosumer or kill.

**Counter-example — HubSpot's switching-cost moat**: HubSpot started as a marketing tool but deliberately expanded into Sales Hub (2014), Service Hub (2018), CMS/Content Hub, and CRM — creating an all-in-one platform with enormous switching costs. Once a company uses 3+ HubSpot hubs, the data, workflows, automations, and team training make switching practically impossible. Result: $3.13B revenue (FY2025), 288,706 customers, and Google offered ~$32B to acquire them. The moat isn't any single product — it's the **integration gravity** of the ecosystem.

**Design principle**: Build a product that becomes **more valuable and harder to leave** with each month of usage. Embed into the customer's daily workflow and data stack.

---

### Objective 4 — Commercial Defensibility

**Hedge Edge failure**: The product was functionally identical to competitors (Prop Firm Armour, PropEA, Heron Copier). No IP, no unique data, no regulatory barrier. Pricing was the only differentiator, which is a race to zero.

**Mandate**: By Gate 3, the business case must demonstrate at least one of:

1. **Proprietary data asset**: Usage generates unique data that improves the product in a way competitors cannot replicate without equal user volume
2. **Regulatory or compliance barrier**: Certification, licence, or compliance burden that takes 6+ months to clear (e.g., SOC 2, HIPAA, PCI-DSS, ISO 27001)
3. **Integration depth**: Bi-directional integrations with 3+ tools the customer already pays for, creating workflow dependency (cf. HubSpot's ecosystem strategy)
4. **Community or content moat**: User-generated content, templates, workflows, or community contributions that compound in value

**Disqualification**: If a competent developer can replicate the entire product in < 2 weeks, the idea fails Objective 4 regardless of scoring.

---

## II. Constraints

These are hard guardrails — violations are automatic kills, not factors to be weighed.

### Constraint 1 — No Single-Point Dependency

No single third-party platform, API, partnership, or regulation may constitute more than **30%** of either:
- Revenue generation
- Product distribution / customer acquisition
- Core functionality delivery

**Test**: For each external dependency, ask "If this partner/platform disappeared tomorrow, does the business survive?" If the answer is no, the architecture must be redesigned or the idea killed.

**Implementation**: At Gate 1, build a **Dependency Map** listing every external service with an estimated revenue/functionality share percentage. Flag any item ≥ 30%.

---

### Constraint 2 — B2C Churn Ceiling

If the idea targets consumers (B2C), **CAC must be recoverable within 3 months** of the customer's expected subscription revenue. B2C monthly logo churn rates typically range 5-8%, making long payback periods fatal.

**Rationale**: Hedge Edge targeted individual retail traders (B2C). Acquisition cost was difficult to recoup against rapid churn. B2B customers have structurally lower churn (1-3% monthly) because:
- Multiple stakeholders use the product (social lock-in)
- IT approval processes create activation friction that also prevents casual departure
- Enterprise procurement cycles create switching costs (security reviews, vendor audits)

**Preferred model**: B2B or prosumer with team/workspace plans. If B2C is pursued, the unit economics must clear this ceiling.

---

### Constraint 3 — Workflow Integration Requirement

The product must **integrate with at least one tool the customer already pays for** and uses daily (e.g., Slack, HubSpot, Salesforce, Notion, Jira, QuickBooks, Xero, Shopify).

**Rationale**: Integration creates three forms of defensibility simultaneously:
1. **Switching cost** — Migrating integrations and automations is painful
2. **Activation depth** — Product is encountered in the user's existing workflow rather than requiring a separate session
3. **Distribution** — Marketplace listings (Salesforce AppExchange, HubSpot Marketplace, Shopify App Store) provide organic discovery

**Test (Gate 2)**: List the 3 most used tools by the target customer. Design at least one deep bi-directional integration. If the product is useful only as a standalone app with no integration surface, it likely fails Constraint 3.

---

## III. Targeted Action Plan

These are the four research sprints to execute before any idea enters Gate 0. They build the contextual knowledge needed to generate ideas that pass the objectives and constraints above.

### Sprint 1 — Proxy Company Teardowns (3 days)

**Objective**: Study companies that failed due to structural weaknesses we're guarding against, and companies that succeeded by building the moats we require.

#### Teardown A: Zynga vs. Epic Games — Platform Dependency

| Dimension | Zynga (cautionary) | Epic Games (counter-example) |
|-----------|-------------------|------------------------------|
| **Platform** | 100% Facebook-dependent (2007-2012) | Built Unreal Engine (owned distribution) |
| **Revenue share** | Facebook took 30% of revenue via Facebook Credits | Epic Games Store charges 12% vs. Steam's 30% |
| **TOS risk** | Facebook unilaterally ended special deal (Nov 2012) | Epic owns the platform; sets its own terms |
| **User base** | Lost ~50% of users within a year of Facebook changes | 400M+ registered Epic accounts across owned properties |
| **Outcome** | Stock fell from $14.50 to ~$4; forced to pivot to mobile | $32B+ valuation; forked away from platform rent-seeking |

**Key lesson**: Own your distribution. If you build on someone else's platform, the margins are theirs to set and the terms are theirs to change. Epic's moat is that it *is* the platform — Unreal Engine gives it counter-positioning power against Unity, and Epic Games Store lets it compete on economics (12% vs. 30%).

#### Teardown B: HubSpot — From Tool to Ecosystem

| Phase | What Happened | Moat Mechanism |
|-------|--------------|----------------|
| **2006-2010** | Marketing-only tool; revenue grew from $255K to $15.6M | None — functionally replicable |
| **2010-2014** | Launched CRM Free (2014), moved upmarket to mid-market | Switching costs: data + workflow lock-in |
| **2014-2020** | Added Sales Hub, Service Hub, Operations Hub | Integration gravity: 3+ hubs = near-permanent customer |
| **2020-2026** | AI layer (Breeze), Clearbit acquisition, $3.13B revenue | Cornered resource (Clearbit data) + network effects (ecosystem marketplace) |

**Key lesson**: Start narrow, but design for stacking. HubSpot's *individual* products were never best-in-class ("more breadth than depth" — CRM Search, 2012). The moat isn't product quality — it's the **cost of leaving an interconnected ecosystem**. Once you use HubSpot CRM + Marketing Hub + Sales Hub, migrating all three simultaneously is a 3-month project that no VP of Sales will authorise unless the building is on fire.

**Application**: Design the next product with an expansion roadmap from day one. V1 solves one problem well. V2-V3 add adjacent capabilities that share the same data model and workflow. Each addition makes leaving harder.

---

### Sprint 2 — Map the 7 Powers Framework to Idea Generation (2 days)

**Objective**: Internalise Hamilton Helmer's 7 Powers as a lens for generating and filtering ideas. For each power type, identify 2-3 existing SaaS/B2B companies that embody it.

| Power | Definition | Example Companies | How They Built It |
|-------|-----------|-------------------|-------------------|
| **Scale Economies** | Per-unit cost falls as volume grows; smaller rivals can't match | AWS, Cloudflare | Massive infrastructure investment creates cost advantage at scale |
| **Network Economies** | Value of product increases with each additional user | Slack (within orgs), Figma (design files shared), LinkedIn | Direct: more users = more value. Indirect: more users attract more integrations |
| **Counter-Positioning** | Incumbent can't adopt your model without self-harm | Notion vs. Atlassian, GitHub Copilot vs. traditional IDEs | Bundling/simplification cannibalises incumbent's per-seat premium products |
| **Switching Costs** | Expected loss of switching exceeds expected gain | Salesforce, HubSpot, Workday | Data gravity, workflow automation, user training, integrations |
| **Branding** | Premium pricing power from perceived quality/trust | Apple, Stripe | Requires years of consistent quality — not available at inception |
| **Cornered Resource** | Exclusive access to a key asset | Clearbit (contact data), ZoomInfo, Bloomberg Terminal | Proprietary datasets, regulatory licences, exclusive partnerships |
| **Process Power** | Opaque organisational excellence | Toyota (TPS), TSMC (chip fabrication) | Builds over years — not applicable at founding |

**Actionable filter for idea generation**: Focus on ideas where **Network Economies, Switching Costs, Counter-Positioning, or Cornered Resource** are plausible at launch or within 12 months of product-market fit.

**Question to ask for every idea**: *"Which of the 7 Powers will this business possess at $1M ARR? At $10M ARR? If the answer is 'none,' kill it."*

---

### Sprint 3 — Benchmark Defensible Unit Economics (2 days)

**Objective**: Establish evidence-backed thresholds for retention, LTV:CAC, and payback so that Gate 2-3 evaluations have hard benchmarks, not gut feel.

#### 3A. Net Revenue Retention (NRR) Benchmarks

| Segment | Median NRR | Top Quartile | Best in Class | Source |
|---------|-----------|-------------|--------------|--------|
| **Enterprise SaaS** (>$50K ACV) | 110-115% | 125%+ | 140%+ (Snowflake, Twilio at peak) | Bessemer Cloud Index, KeyBanc |
| **Mid-Market SaaS** ($10-50K ACV) | 105-110% | 115-120% | 130%+ | SaaS Capital, KeyBanc |
| **SMB SaaS** (<$10K ACV) | 90-100% | 105-110% | 115%+ | OpenView, ProfitWell |
| **B2C Subscription** | 60-80% | 85-90% | 95%+ (rare) | ProfitWell, Recurly |

**Takeaway**: B2C subscription NRR is structurally 20-40 percentage points below B2B. This is why Constraint 2 exists — B2C churn is a physics problem, not an execution problem.

#### 3B. LTV:CAC & Payback Benchmarks

| Metric | Acceptable | Good | Excellent |
|--------|-----------|------|-----------|
| LTV:CAC | 3:1 | 5:1 | 8:1+ |
| CAC Payback (B2B) | ≤ 18 months | ≤ 12 months | ≤ 6 months |
| CAC Payback (B2C) | ≤ 3 months | ≤ 2 months | ≤ 1 month |
| Gross Margin | ≥ 65% | ≥ 75% | ≥ 85% |

**Rule of thumb**: If the idea targets B2C and the projected monthly subscription is < $30/month, the unit economics almost certainly fail unless viral/organic acquisition delivers CAC < $10.

#### 3C. What "Good" Looks Like at Different Stages

| Stage | Revenue | NRR Target | Churn Target | LTV:CAC |
|-------|---------|-----------|-------------|---------|
| Pre-PMF | $0-100K ARR | N/A (too few customers) | Focus on qualitative retention signals | N/A |
| Early PMF | $100K-1M ARR | ≥ 100% | ≤ 5% monthly logo churn | ≥ 2:1 |
| Growth | $1M-10M ARR | ≥ 110% | ≤ 3% monthly logo churn | ≥ 3:1 |
| Scale | $10M+ ARR | ≥ 120% | ≤ 1.5% monthly logo churn | ≥ 5:1 |

---

### Sprint 4 — Audit API & Platform Risk (1 day)

**Objective**: Build a permanent reference card of platform dependency disasters to use as a gut-check at Gate 1.

#### Case Study Reference Card

| Year | Platform | What Happened | Who Died | Lesson |
|------|----------|--------------|----------|--------|
| 2012 | Facebook | Ended exclusive Zynga agreement; modified app notification policies | Zynga (lost ~50% users, $400M valuation hit) | Distribution dependency = existential dependency |
| 2018 | Facebook | Cambridge Analytica scandal → API lockdown; reduced organic reach to ~2% | Hundreds of social media tools, media publishers | Policy changes cascade to all dependents simultaneously |
| 2023 (Feb) | Twitter / X | Replaced free API with paid tiers; killed third-party client access | Tweetbot, Twitterrific, dozens of clients (10+ year businesses) | Overnight, unilateral, no negotiation |
| 2023 (Apr) | Reddit | Introduced API pricing ($12K/50M requests); $20M/year for major clients | Apollo, Sync, BaconReader, RIF (all shut down June 30) | Even community outrage (7,000+ subreddit blackout) didn't reverse the decision |
| 2020+ | Apple App Store | 30% revenue share; arbitrary review rejections; policy changes | Countless indie developers, Epic (Fortnite removed) | "App Store lottery" — approval is never guaranteed |
| 2024+ | Google Search | Algorithm updates can wipe 60-90% of organic traffic overnight | Content sites, affiliate businesses, niche publishers | SEO-dependent distribution is a single-point-of-failure |

#### Dependency Audit Checklist (use at Gate 1)

For every external service the product relies on, answer:

| Question | Answer |
|----------|--------|
| What % of revenue flows through this platform? | ___ % |
| What % of users come from this channel? | ___ % |
| What % of core functionality depends on this API? | ___ % |
| Does this platform have a history of API/TOS changes? | Y/N |
| Can the product function (degraded) if this platform disappears? | Y/N |
| Is there a viable alternative you could migrate to within 30 days? | Y/N |

**Red flags**: Any single dependency ≥ 30% | No viable alternative | Platform has a history of unilateral changes

---

## IV. Refinements & Additions

These are additions beyond the original outline, informed by the research above.

### Addition 1 — The "Weekend Replication Test"

Before any idea passes Gate 1, answer honestly: **"Can a competent developer replicate the core value proposition in a weekend hackathon?"**

If yes, the idea has no technical moat. Hedge Edge failed this test — the copier was commodity software wrapped in a UI. Look for ideas where the *data*, the *integrations*, or the *user-generated content* compound over time and cannot be cloned by copying the code.

### Addition 2 — Expansion Wedge Design

Inspired by HubSpot's playbook: every V1 product must ship with a **documented expansion roadmap** showing how V2 and V3 add adjacent capabilities that share data and workflows with V1.

- **V1**: Solve one core problem exceptionally well (earn trust)
- **V2**: Add one adjacent capability that reuses V1 data (create switching cost)
- **V3**: Add collaboration/team features (create social lock-in)

This should be sketched at Gate 2 and detailed at Gate 3.

### Addition 3 — "Anti-Portfolio" Review

Maintain a running log of killed ideas with *why* they were killed. Review quarterly. Sometimes a killed idea becomes viable because:
- A new regulation created a barrier (Cornered Resource)
- A platform opened an API that didn't exist before
- A competitor validated the market with a flawed execution you can counter-position against

This log lives in `resources/IdeaPipeline/anti-portfolio.md` (to be created).

### Addition 4 — Mandatory Scenario Planning at Gate 3

Before any idea advances to Gate 4 (Contained Test), model three scenarios:

1. **Platform Risk Scenario**: Your largest external dependency changes terms. What happens? Can you survive?
2. **Clone Scenario**: A well-funded competitor copies your product. What keeps customers? What's your defensible wedge?
3. **Churn Scenario**: Monthly churn doubles from your base case. At what churn rate do unit economics break? How far above that line are you?

If any scenario produces a "business dies" outcome with no recovery path, the idea does not advance.

---

## V. How This Memo Connects to the Pipeline

```
IDEA MANDATE MEMO (this file)
       │
       ▼
  [Filter: Idea must satisfy all 4 Objectives + 3 Constraints]
       │
       ▼
  due-diligence-workflow.md → Gate 0 → Gate 1 → Gate 2 → Gate 3 → Gate 4
       │
       ▼
  idea-evaluation-TEMPLATE.md (copied per idea)
       │
       ▼
  pipeline-tracker.md (status tracking)
```

**Usage rule**: Before an idea enters Gate 0, cross-reference it against this memo's Objectives and Constraints. If it obviously violates any constraint, it doesn't even get a template file. Save the time.

---

## Appendix: Hedge Edge Failures → Mandate Mapping

| Hedge Edge Failure | Objective/Constraint | What We Require Now |
|-------------------|---------------------|-------------------|
| Moat score 2/10 | Objective 1 | ≥ 6/10 with 2+ structural powers |
| 100% prop firm TOS dependency | Objective 2, Constraint 1 | No dependency > 30% |
| B2C retail traders with zero switching costs | Objective 3, Constraint 2 | NRR ≥ 100%, CAC payback ≤ 3mo (B2C) or ≤ 18mo (B2B) |
| Functionally identical to competitors | Objective 4 | Must fail Weekend Replication Test |
| No integrations with existing tools | Constraint 3 | Must integrate with tool customer already uses |
| No expansion path (product was feature-complete at launch) | Addition 2 | V1/V2/V3 expansion roadmap at Gate 2 |

---

*This memo is a living document. Update it as new case studies, framework improvements, or post-mortems emerge. It is not a guarantee of success — it is a filter to prevent repeating known patterns of failure.*
