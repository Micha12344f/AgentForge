# Investor Vetting — RESEARCH Directive

## Purpose

Act as an investor vetting a business idea. Apply the screening standards derived from Warren Buffett's partnership letters (1957–1969) and Berkshire Hathaway shareholder letters (1977–2024) to evaluate whether a business idea qualifies as strong, marginal, or weak. The goal is honest, bias-free analysis — not promotion.

## Owner

RESEARCH

## Trigger

Use this skill when:
- A business idea, company, or product needs to be evaluated for investment quality
- An existing thesis PDF in the outputs folder needs a Buffett-grade second opinion
- The user asks to "vet", "screen", or "stress-test" a business idea
- A completed thesis needs its moat, economics, or durability claims challenged

## Execution Script

| Layer | Path |
|-------|------|
| Execution | `Business/RESEARCH/executions/vet_business_idea.py` |

Reads completed thesis PDFs from the outputs folder, extracts their text, and prints structured content that the Research agent can interpret. This allows the agent to review previously generated theses without manual copy-paste.

## Resources

| Resource | Path | Description |
|----------|------|-------------|
| Buffett Investor Corpus | `Business/RESEARCH/resources/buffett-investor-corpus.md` | Paraphrased chronological digest of Buffett's letters focused on business-idea evaluation criteria, moat signals, red flags, and valuation discipline |
| Existing thesis PDFs | `Business/RESEARCH/resources/outputs/` | Previously generated thesis documents that the execution script can read |

---

## How It Works — Step by Step

### Step 1 — Understand The Idea

Gather the business idea in plain language. At minimum you need:
- What the company does and how it makes money
- Who the customer is
- What advantage is claimed

If a thesis PDF already exists in `Business/RESEARCH/resources/outputs/`, run the execution script to extract and read it first.

### Step 2 — Classify The Thesis Type

Every business idea is one of these:
- **Durable compounder** — earns high returns on capital with a defensible position, reinvests productively
- **Mispricing / turnaround** — the market undervalues a real asset or earning stream
- **Control / governance unlock** — value is trapped by poor capital allocation or management inertia
- **Special situation / workout** — a specific catalyst (merger, spinoff, restructuring) creates a time-bound opportunity

State the type explicitly. If the idea does not fit cleanly, say so — an unclear thesis type is itself a warning.

### Step 3 — Apply The Screening Rubric

Score each dimension as PASS, MARGINAL, or FAIL with a one-sentence justification:

| Dimension | What good looks like | Fail signal |
| --- | --- | --- |
| Comprehensibility | The business model and edge can be explained in plain English | The thesis depends on jargon, narratives, or TAM inflation |
| Business quality | High returns on tangible capital with limited debt | Heavy capital needs, weak margins, or leverage doing the work |
| Moat | Evidence of cost advantage, habit, brand, switching friction, or distribution power | Differentiation is asserted but not visible in economics |
| Pricing power | The business can raise price or protect margin without damaging demand | It lives at the mercy of commodity pricing or constant discounting |
| Durability | The economics are likely to remain legible over a decade | Industry change makes long-range underwriting guesswork |
| Reinvestment runway | Incremental capital can still earn good returns | Growth consumes cash without raising intrinsic value |
| Management quality | Candor, owner mindset, and rational capital allocation | Promotional behavior, acquisition addiction, or evasive reporting |
| Incentives | Pay is linked to controllable value creation with downside exposure | Incentives reward activity, size, or short-term optics |
| Balance-sheet resilience | The business can survive a bad year without permanent damage | A mild shock creates refinancing or dilution risk |
| Valuation discipline | The expected return still works if the forecast is somewhat wrong | The price already assumes a best-case future |

### Step 4 — Check For Red Flags

Scan for the following patterns that Buffett warns about repeatedly across decades of letters:

- Bad industry economics dressed up as a management story
- High growth that requires constant capital just to stand still
- Leverage masking mediocre operating performance
- Promotional leadership and euphemistic accounting
- Acquisition-led growth with weak evidence of value creation
- Commodity pricing with no real customer captivity
- Theses that only work if several favorable assumptions all happen together
- Businesses outside the analyst's circle of competence

If the idea is an AI wrapper or MCP-tool product, also apply the mandatory stress tests from the Research SKILL.md (substitution, integration, data flywheel, model lock-in, MCP commoditisation).

### Step 5 — Apply The Buffett Questions

Answer each question with evidence, not assertion:

1. What exact kind of thesis is this?
2. What would make a rational competitor fail to dislodge this company?
3. What are owner earnings after the real costs of maintaining the business?
4. Does retained cash create more than one dollar of value for each dollar kept?
5. Can management explain capital allocation simply and defendably?
6. What happens to the thesis in a recession or financing squeeze?
7. Which facts would falsify the thesis within one to three years?
8. How much optimism is already embedded in the current price?

### Step 6 — Produce The Verdict

Summarize findings as:

**Verdict**: STRONG / MARGINAL / WEAK

**Basis**: 2–3 sentences connecting the rubric results to the verdict.

**Key risk**: The single most important thing that could break the thesis.

**Recommended action**: Pass, investigate further, or proceed to full thesis (Skill 1).

---

## Buffett-Era Context For Calibration

This directive draws on insights from across the Buffett corpus. The key evolutionary arc:

- **Partnership era (1957–1969)**: Best for downside protection logic, catalyst thinking, thesis-type discipline, and the willingness to pass when the opportunity set is poor.
- **Early Berkshire (1977–1989)**: Best for moat realism, owner-earnings framing, the shift from "cheap" to "wonderful business at a fair price", and the rejection of bad-industry-plus-good-management stories.
- **Mature Berkshire (1991–2001)**: Best for franchise vs. ordinary business distinction, pricing power, circle of competence, and anti-speculation valuation discipline.
- **Late Berkshire (2002–2024)**: Continuity of the same framework with broadened application. No major shifts, but useful for confirming the standard does not drift.

The full paraphrased corpus is in `Business/RESEARCH/resources/buffett-investor-corpus.md`. Read it when deeper calibration or era-specific context is needed.

---

## Default Stance

Scepticism first. A business idea is assumed weak until the evidence proves otherwise. If the analysis makes the idea look good, that should be because the economics and evidence support it — not because the analyst wanted a positive result.

Prefer Buffett's mature standard: durable compounders with honest management and conservative financing. Treat pricing power and low capital intensity as unusually strong tells. Pass quickly when the moat, incentives, or capital intensity do not hold up.
