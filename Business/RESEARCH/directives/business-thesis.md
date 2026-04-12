# Business Thesis Builder — RESEARCH Directive

## Purpose

Standard operating procedure for creating investor-grade business thesis documents. This directive governs the end-to-end process from initial business idea intake through research, analysis, writing, and PDF generation.

## Owner

RESEARCH

## Trigger

Use this skill when:
- A user provides a business idea and wants a structured thesis document
- A user asks for a business case, investment thesis, or competitive analysis document
- A user wants to vet an AI wrapper or MCP-tool business concept
- A user wants to evaluate whether a business idea has structural defensibility

## Execution Script

| Layer | Path |
|-------|------|
| Execution | `Business/RESEARCH/executions/build_thesis_pdf.py` |

Generates a professionally formatted PDF from completed thesis content. Outputs to `Business/RESEARCH/resources/outputs/`.

## Resources

| Resource | Path | Description |
|----------|------|-------------|
| Thesis Template | `Business/RESEARCH/resources/business-thesis-template.md` | Canonical template with all sections and slot-in markers |
| Research Sources | `Business/RESEARCH/resources/research-sources.md` | Authoritative source directory by domain |
| Outputs | `Business/RESEARCH/resources/outputs/` | Generated PDF thesis documents |

---

## How It Works — Step by Step

### Step 1 — Intake and Scoping

Collect the following from the user (use `vscode/askQuestions` if interactive):

| # | Question | Required |
|---|----------|----------|
| 1 | **Company name** (exact legal name and any trading names) | Yes |
| 2 | **One-paragraph description** — what the product does, who it serves | Yes |
| 3 | **Stage** — idea only / built but pre-launch / live with users / revenue generating | Yes |
| 4 | **Tech stack summary** — what it's built on, what APIs/models it uses | Yes |
| 5 | **Known competitors** — any the user is already aware of (can be "none") | Yes |
| 6 | **Jurisdiction** — where is the company registered, where are its customers? | Yes |
| 7 | **Existing materials** — any pitch decks, product docs, or financial projections available? | Optional |
| 8 | **Specific concerns** — any areas the user particularly wants stress-tested? | Optional |

### Step 2 — Read the Template

Read `Business/RESEARCH/resources/business-thesis-template.md` in full. This is the structural spine of every thesis. Do not deviate from its section order or omit sections.

### Step 3 — Research Phase

Execute research in the following order (each step may involve web scraping):

#### 3a — Product and Technology Research
- Understand the product architecture: what models/APIs it depends on, what the integration layer does, what the user experience is
- If it is an AI wrapper or MCP tool: immediately apply the five mandatory stress tests (substitution, integration, data flywheel, model lock-in, MCP commoditisation)
- Document all external dependencies

#### 3b — Market Research
- Identify the broadest relevant market and find institutional sizing data
- Use the source hierarchy in `Business/RESEARCH/resources/research-sources.md`
- Narrow to the target segment using bottom-up estimation where top-down data is unavailable
- Document buying patterns, customer profiles, and adoption friction

#### 3c — Competitor Research
- Follow the full competitor research directive at `Business/RESEARCH/directives/competitor-research.md`
- Scrape competitor websites for pricing, features, positioning, and traction metrics
- Classify competitors into Tier 1 (direct) and Tier 2 (adjacent)
- Build the structured comparison table
- Assess competitive response likelihood

#### 3d — Regulatory Research
- Follow the regulatory research directive at `Business/RESEARCH/directives/regulatory-research.md`
- Identify all regulatory bodies with jurisdiction over the business and its customers
- Fetch and interpret relevant guidance documents
- Assess terms-of-service risks for any platform dependencies
- Research legal precedent where relevant

### Step 4 — Analysis and Writing

Fill each section of the template in order. Follow these rules absolutely:

**Writing Rules**:
1. **No promotional language** — never use "revolutionary", "game-changing", "unique" (unless proven), "cutting-edge", or similar
2. **No unverified statistics** — every number must have a source citation. If you cannot find a source, say "no verifiable figure available" or "management estimate"
3. **Honest framing of weaknesses** — if the moat score is 2/18, say so. If the product is a thin wrapper, say so. If the market is too small, say so
4. **Distinguish between facts and assessments** — "The company has 500 users (Company X, 2026)" is a fact. "The market may reach $10B by 2030" is a projection — label it as such
5. **Harvard referencing** — every citation follows Harvard format with access date
6. **Investor-grade tone** — write as though the reader is a sceptical fund manager, not a cheerleader
7. **AI wrapper candour** — if the business is a thin wrapper with no structural defensibility, the thesis must say that plainly. The goal is truth, not encouragement

**Moat Scoring (mandatory for Section 3.3)**:

| Moat Type | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| Switching costs | None | Mild inconvenience | Meaningful workflow migration | Data/process lock-in |
| Network effects | None | Weak / indirect | Moderate direct effects | Strong multi-sided |
| Brand / trust | Unknown | Recognised | Trusted in segment | Industry authority |
| Proprietary data | None | Basic usage data | Differentiated dataset | Irreplaceable data asset |
| Regulatory / IP | None | Minor compliance hurdle | Licensed / certified | Patent or regulatory moat |
| Integration complexity | Trivial | Some API work | Multi-system orchestration | Deep enterprise integration |

**Score below 6** = race position (timing advantage only, no structural moat)
**Score 6–12** = emerging moat (some defensibility, needs strengthening)
**Score 12–18** = strong moat (structural advantages present)

### Step 5 — Draft Review

Before generating the PDF, present to the user:
1. **Executive findings** — 3–5 bullet points summarising the strongest and weakest aspects of the business
2. **Risk flags** — any material risks that an investor would want highlighted
3. **Moat score** — the quantified score with brief justification
4. **Recommendation** — a one-sentence honest assessment (e.g., "Timing play with execution risk" or "Thin wrapper with no structural defensibility" or "Genuine integration moat in an underserved niche")

Ask the user to confirm before generating the PDF.

### Step 6 — PDF Generation

Run the execution script:
```
python Business/RESEARCH/executions/build_thesis_pdf.py --company "<company-slug>" --month "<YYYY-MM>"
```

The script reads the completed thesis content (passed as a JSON file or via stdin) and generates a formatted PDF.

**Output path**: `Business/RESEARCH/resources/outputs/<company-slug>-thesis-<YYYY-MM>.pdf`

### Step 7 — Reference Verification

Before finalising, verify:
- [ ] Every in-text citation has a corresponding entry in the Reference List
- [ ] Every Reference List entry has been actually accessed (URL fetched during research)
- [ ] No fabricated citations
- [ ] No statistics without sources
- [ ] All "accessed" dates are accurate

---

## Anti-Patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Assume the business idea is good | Confirmation bias produces worthless analysis | Start from scepticism; let evidence build the case |
| Use superlatives ("best", "only", "revolutionary") | Destroys credibility with sophisticated readers | Use measurable claims ("reduces X by Y%") |
| Fabricate market sizes | Investors verify these | Use institutional sources or say "no verified figure available" |
| Skip competitor research | The most common failure in business plans | Scrape every competitor website; build the comparison table |
| Ignore regulatory risk | Regulators can kill a business overnight | Research the specific regulatory bodies and cite their guidance |
| Present a thin wrapper as defensible | AI-literate investors will see through it | Apply the five stress tests honestly |
| Skip the moat scoring | Investors need a clear signal on defensibility | Complete the full 6-dimension scoring grid |
