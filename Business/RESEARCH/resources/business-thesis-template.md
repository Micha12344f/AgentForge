# Business Thesis Template — Structured Analysis Framework

> **Skill**: Business Thesis Builder
> **Department**: RESEARCH
> **Directive**: `Business/RESEARCH/directives/business-thesis.md`

---

## Instructions for the Research Agent

This template is the canonical structure for producing an investor-grade business thesis document. Each section contains:
- **Guidance** (in blockquotes) — what the section must accomplish and how to think about it
- **Slot-in markers** (`{{PLACEHOLDER}}`) — where research findings are inserted
- The writing style must be **direct, honest, and free of promotional language**. If something is weak, say so. If a claim is unverified, flag it. The reader is assumed to be a sceptical, intelligent investor who will punish vagueness and reward candour.

**Output format**: The completed thesis is rendered to PDF via the execution script at `Business/RESEARCH/executions/build_thesis_pdf.py` and saved to `Business/RESEARCH/resources/outputs/`.

---

## Document Header

```
{{COMPANY_NAME}}                                                    {{MONTH}} {{YEAR}}
```

---

## 1. Summary

> **Guidance**: The summary is a self-contained overview of the entire thesis in ~4–6 paragraphs. It must cover: who the company targets, what it sells, how it delivers value, what stage it is at, what the financial requirement is, and what the principal risks are. Do not use superlatives. Do not claim uniqueness unless you can prove it. Write as though the reader will only read this section and nothing else.

> **AI Wrapper / MCP Tool Lens**: If the business is an AI wrapper or MCP-tool product, the summary must explicitly state: (a) what foundational model or API it wraps, (b) what the wrapper adds beyond calling the API directly, (c) whether the value is in the integration layer, the UX, the data flywheel, or the domain specialisation — and be honest about which of those is actually defensible.

**Paragraph 1 — Target customer and problem:**
{{SUMMARY_TARGET_CUSTOMER_AND_PROBLEM}}

**Paragraph 2 — Product and value proposition:**
{{SUMMARY_PRODUCT_AND_VALUE_PROPOSITION}}

**Paragraph 3 — Distinctive features and team credibility:**
{{SUMMARY_DISTINCTIVE_FEATURES_AND_TEAM}}

**Paragraph 4 — Current stage:**
{{SUMMARY_CURRENT_STAGE}}

**Paragraph 5 — Financial requirement:**
{{SUMMARY_FINANCIAL_REQUIREMENT}}

**Paragraph 6 — Principal risks and potential return:**
{{SUMMARY_RISKS_AND_RETURN}}

---

## 2. History

> **Guidance**: State the current stage of the business factually. Only claim what is evidenced. If something has not been independently verified, say so. Distinguish between "built" and "shipped to paying customers." Distinguish between "partnership signed" and "partnership generating revenue."

### Current stage and progress to date

{{HISTORY_CURRENT_STAGE}}

> Include: incorporation status, product development milestones actually completed, integrations live vs. planned, infrastructure in place, partnerships signed, revenue status (be precise: $0 MRR is fine — lying about traction is not), community or waitlist size if any, funding history if any.

{{HISTORY_PROGRESS_MILESTONES}}

> **Honesty checkpoint**: If there is no external funding, no trading history, no published audit, or no paying users — state that explicitly. Do not let absence of evidence be mistaken for presence of evidence.

---

## 3. Product and Service

> **Guidance**: This section must answer four distinct questions, each separated as a sub-section. The reader is assumed to be intelligent but not a domain expert. Avoid jargon infatuation — explain the technology simply but not simplistically.

### 3.1 — What is the product or service, and what will it be used for?

> Describe the product precisely. What does the user actually experience? What workflow does it replace or improve? If it is an AI wrapper: what does the user get that they cannot get by prompting the model directly?

{{PRODUCT_DESCRIPTION}}

### 3.2 — What are the product's unique or distinctive advantages, and how do they translate into customer benefits?

> Be specific. "Uses AI" is not an advantage. "Reduces manual data entry by 80% because the agent pre-fills from CRM data" is an advantage. Quantify where possible. If you cannot quantify, explain why.

> **AI Wrapper Stress Test**: Apply this three-part test:
> 1. **Substitution test** — Could the customer achieve the same outcome by using the underlying model/API directly with a well-crafted prompt? If yes, the wrapper's value is convenience, not capability.
> 2. **Integration test** — Does the product connect systems that the raw API cannot connect without custom engineering? If yes, the integration layer has genuine value.
> 3. **Data flywheel test** — Does usage generate proprietary data that improves the product over time in ways competitors cannot replicate without the same user base? If no, the product has no compounding advantage.

{{PRODUCT_ADVANTAGES_AND_BENEFITS}}

### 3.3 — How easily can competitors imitate these advantages?

> This is the moat analysis. Be brutally honest. Apply the following framework:
>
> | Moat Type | Score (0–3) | Evidence |
> |-----------|-------------|----------|
> | Switching costs | | |
> | Network effects | | |
> | Brand / trust | | |
> | Proprietary data | | |
> | Regulatory / IP protection | | |
> | Integration complexity | | |
>
> **Overall moat score**: X/18
>
> A score below 6 means the business is in a race, not a moat position. Say that clearly.

{{COMPETITOR_IMITATION_ANALYSIS}}

### 3.4 — Technology analysis and associated risks

> **Guidance**: Write for someone who is smart but not technical. Explain what the technology does, not how it works at the implementation level. Focus on: what external dependencies exist, what happens if those dependencies change, and what the technical risks are.

> **AI Wrapper Specific Risks**:
> - Model provider risk: What happens if the underlying model's pricing doubles, quality degrades, or the provider adds competing features?
> - API dependency risk: Rate limits, deprecation, terms-of-service changes
> - Latency and reliability: Is the product's performance directly tied to a third-party API's uptime?
> - Data privacy: Does user data flow through third-party model APIs? If yes, what are the implications?

{{TECHNOLOGY_ANALYSIS}}

---

## 4. Market and Competitors

> **Guidance**: This is the most research-intensive section. It must be structured in three parts. Every claim about market size, growth, or competitor capability must cite a verifiable source. Do not invent statistics. If a number cannot be verified, say "unverified estimate" or "management projection" — never present it as fact.

### Part 1 — General Market Description

> Describe the overall market the business operates in. Include: market definition, market size (TAM), historical context, geographic scope, growth trajectory, and the primary customer type. Use institutional sources (BIS, Gartner, Grand View Research, Statista, government agencies) for market sizing. Use company disclosures for firm-specific data. Cite everything.

{{MARKET_GENERAL_DESCRIPTION}}

### Part 2 — Target Market Segment

> Narrow from the general market to the specific segment the business targets. Include:

#### Market segment definition
{{MARKET_SEGMENT_DEFINITION}}

#### Geographic scope
{{MARKET_GEOGRAPHIC_SCOPE}}

#### Segment size and growth
> Use bottom-up estimation if no published figure exists. Show your working. A transparent estimate is more credible than a fabricated precision.

{{MARKET_SEGMENT_SIZE_AND_GROWTH}}

#### Buying patterns and customer priorities
> How does the target customer currently buy solutions? What influences their decisions? What is their price sensitivity? What retention dynamics exist?

{{MARKET_BUYING_PATTERNS}}

#### Customer adjustments required
> What must the customer change about their current workflow to adopt this product? Every friction point is a conversion risk — name them.

{{MARKET_CUSTOMER_ADJUSTMENTS}}

### Part 3 — Competitor Analysis

> **Guidance**: This is the section investors scrutinise most. It must be structured, thorough, and honest. Categorise competitors into tiers:
>
> - **Tier 1 — Direct competitors**: Same value proposition, same target customer
> - **Tier 2 — Adjacent competitors**: Overlapping feature set but broader or different positioning
> - **The status quo**: The biggest competitor is always "doing nothing" or "doing it manually"
>
> For each Tier 1 and Tier 2 competitor, research and document:
> - Company name, URL, jurisdiction/registration
> - Product description and framing
> - Platform support / delivery model
> - Pricing (exact figures where available)
> - User base / traction metrics (verified where possible)
> - Funding and team size (if known)
> - Community and content strategy

#### Tier 1 — Direct Competitors

{{COMPETITORS_TIER_1}}

#### Tier 2 — Adjacent Competitors

{{COMPETITORS_TIER_2}}

#### On what basis do rivals compete?

> Identify the 4–6 dimensions on which competition actually operates in this market (e.g., price, platform breadth, framing, ease of onboarding, reputation, feature depth). Map each competitor's position on each dimension.

{{COMPETITORS_BASIS_OF_COMPETITION}}

#### Comparative table

> Build a structured comparison table covering all competitors and the subject company across every relevant attribute. Example attributes: primary framing, delivery model, platforms supported, execution model, analytics, entry pricing, free tier, community, scale/users.

{{COMPETITORS_COMPARISON_TABLE}}

#### What makes the product superior or different, and how can unique features be protected?

> List each claimed differentiator. For each one, assess: (a) is it real? (b) is it defensible? (c) for how long?

{{PRODUCT_DIFFERENTIATION_ANALYSIS}}

#### What barriers does a new entrant face, and how is competition likely to react?

> **Barriers facing the subject company as entrant**: trust, platform coverage, distribution, content authority, existing competitor scale.
> **Likely competitive response**: non-response (most probable at zero scale), messaging adaptation, price retaliation, feature imitation.

{{BARRIERS_AND_COMPETITIVE_RESPONSE}}

#### How do potential customers see the competition?

> What do forums, Discord servers, Reddit threads, YouTube comments, Trustpilot reviews, and community discussions say about existing tools? What is the default alternative (doing nothing)? What would it take for this product to displace the status quo?

{{CUSTOMER_PERCEPTION_OF_COMPETITION}}

---

## 5. Risk, Return, Exit

> **Guidance**: This is the investor's decision section. Frame risks honestly — an investor who discovers a risk you hid will never trust you again. Frame returns with academic backing, not hype. Frame exits with precedent, not fantasy.

### The Risks

> Enumerate all material risks. For each risk: state it, explain the mechanism, assess probability and impact, and note any mitigation. Standard risk categories to consider:

> 1. **Market adoption and long-term feasibility risk** — Will the target market actually buy this? Is there a structural paradox (e.g., your success threatens the ecosystem you depend on)?
> 2. **Regulatory and reputational risk** — What regulations apply? What happens if perception shifts?
> 3. **Partner dependency risk** — Which third parties can unilaterally damage the business?
> 4. **Regulatory/legal risk** — Are there specific laws, terms of service, or contractual obligations that the product may conflict with? Cite specific regulatory bodies and legal precedent where relevant.
> 5. **Replication risk** — How quickly can a well-resourced competitor reproduce the visible feature set? Reference AI-assisted development speed (Kalliamvakou, 2022) where relevant.
> 6. **Model/API provider risk** (AI wrapper specific) — What happens if the foundational model changes pricing, quality, ToS, or adds competing features?
> 7. **Execution risk** — Pre-revenue, pre-launch, lean team: what are the specific failure modes?

{{RISK_ANALYSIS}}

### Expected Return

> Frame as asymmetric capital appreciation. Reference venture failure rates (~75% fail to return capital — Hayes, 2026) and top-performing fund returns (30%+ annualised). For SaaS businesses, use ARR-based valuation frameworks (SaaS Capital / Lucas, 2022):
>
> $Valuation\ Multiple = -3.2 + (0.32 \times SCI) + (8.26 \times ARR\ Growth\ Rate) + (2.62 \times NRR\ Rate)$
>
> Reference public SaaS trading multiples (4.8x–9.9x TTM revenue) with private discount (~2x).
> Identify the specific milestones that reduce investment risk: first paid conversions, retention evidence, platform expansion, sustained MRR growth.

{{EXPECTED_RETURN_ANALYSIS}}

### Exit Routes

> Identify the most credible exit routes for the specific business. Standard options:
> - **Trade sale / M&A** — who are logical acquirers and why?
> - **IPO** — realistic only at significant scale
> - **MBO** — management buyout
> - **Secondary sale** — selling equity to another investor
> - **Liquidation** — last resort, lowest returns
>
> Reference typical venture exit timelines (4–6 years, predominantly M&A — Hayes, 2026).

{{EXIT_ROUTES_ANALYSIS}}

### Investor Objections and Responses

> Pre-empt the most likely investor objections. For each: state the objection, acknowledge its validity, and map it to a specific milestone that demonstrably reduces the risk.

{{INVESTOR_OBJECTIONS}}

---

## Reference List

> **Guidance**: Harvard referencing style. Every source cited in the document must appear here. Separate into: academic/institutional sources, company disclosures, and internal documents. Do not fabricate citations. If a URL was fetched during research, include the access date.

{{REFERENCE_LIST}}

---

## Appendices (Optional)

> Include supplementary material that supports the thesis but would interrupt the flow of the main document: detailed financial projections, technical architecture diagrams, survey data, extended competitor profiles, regulatory extracts.

{{APPENDICES}}
