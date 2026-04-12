# Regulatory & Legal Research — RESEARCH Directive

## Purpose

Standard operating procedure for identifying, fetching, interpreting, and citing regulatory documentation relevant to a business thesis. This directive ensures that regulatory and legal risk assessment is grounded in primary sources rather than secondary commentary.

## Owner

RESEARCH

## Trigger

Use this skill when:
- Building Section 5 (Risk, Return, Exit) of a business thesis — specifically regulatory/legal risk
- Building Section 3.4 (Technology analysis) — where platform ToS or compliance matters apply
- A user explicitly asks about the regulatory landscape for a business idea
- The business operates in or adjacent to a regulated industry

## Resources

| Resource | Path | Description |
|----------|------|-------------|
| Research Sources | `Business/RESEARCH/resources/research-sources.md` | Authoritative source directory with regulatory portals by jurisdiction |

---

## How It Works — Step by Step

### Step 1 — Identify the Regulatory Surface

For any given business, determine:

| Question | Why it matters |
|----------|---------------|
| **What industry does the business operate in?** | Determines primary regulatory bodies |
| **Where is the company registered?** | Determines primary jurisdiction |
| **Where are the customers?** | May trigger additional jurisdictions (GDPR if EU customers, CFTC if US futures, etc.) |
| **Does the product touch financial data, personal data, health data, or minors' data?** | Triggers specific regulatory frameworks |
| **Does the product interact with regulated platforms (brokers, exchanges, banks)?** | May trigger platform-specific compliance |
| **Does the product facilitate, advise on, or arrange regulated activities?** | Determines whether licensing/authorisation is required |

### Step 2 — Identify Relevant Regulatory Bodies

Common regulatory bodies by domain:

**Financial services**:
| Jurisdiction | Body | Portal |
|-------------|------|--------|
| UK | Financial Conduct Authority (FCA) | handbook.fca.org.uk |
| US | Securities and Exchange Commission (SEC) | sec.gov |
| US | Commodity Futures Trading Commission (CFTC) | cftc.gov |
| EU | European Securities and Markets Authority (ESMA) | esma.europa.eu |
| Australia | ASIC | asic.gov.au |
| Cyprus | CySEC | cysec.gov.cy |

**Data protection**:
| Jurisdiction | Framework | Portal |
|-------------|-----------|--------|
| UK | UK GDPR / Data Protection Act 2018 | ico.org.uk |
| EU | GDPR | edpb.europa.eu |
| US (California) | CCPA/CPRA | oag.ca.gov |

**AI-specific regulation**:
| Jurisdiction | Framework | Status |
|-------------|-----------|--------|
| EU | AI Act | In force (phased implementation 2024–2027) |
| UK | Pro-innovation approach (no single AI Act) | Principles-based, sector regulators adapt |
| US | Executive Order on AI Safety (Oct 2023) | Guidance-level, not legislation |

**Platform terms of service** (not regulation, but functionally equivalent for dependency risk):
- OpenAI usage policies
- Anthropic acceptable use policy
- Google Cloud AI terms
- MetaTrader / MetaQuotes terms
- Any platform the business depends on

### Step 3 — Fetch Primary Regulatory Documents

For each identified regulatory body:

1. **Fetch the most relevant guidance document** — use the regulatory body's handbook, guidance portal, or FAQ section
2. **Fetch any enforcement actions** relevant to the business domain — these reveal how regulation is actually applied, not just what the law says
3. **Fetch relevant terms of service** — for any third-party platform the business depends on

**What to extract from each document**:
- The specific sections/paragraphs that apply to the business
- The regulatory perimeter — is this business inside or outside the regulated boundary?
- The consequences of non-compliance (fines, prohibition, reputational damage)
- Any exemptions or safe harbours that may apply
- Recent enforcement actions that signal regulatory direction

### Step 4 — Interpret the Regulatory Position

For each regulatory dimension, assess:

| Dimension | Assessment |
|-----------|-----------|
| **Is the business within the regulatory perimeter?** | Clearly inside / borderline / clearly outside |
| **If borderline, what determines which side?** | Specific activities, wording, or business model choices |
| **What authorisation or licensing is required?** | None / notification only / registration / full licence |
| **What are the compliance obligations?** | Data handling, disclosure, record-keeping, reporting |
| **What is the enforcement risk?** | Low (no active enforcement in space) / Medium / High (recent actions) |
| **What is the reputational risk?** | How would regulatory scrutiny be perceived by customers and partners? |

### Step 5 — Legal Precedent Research

Where relevant (especially for novel business models or grey-area activities):

1. **Search for case law** — UK: BAILII (bailii.org), US: federal court databases, SEC/CFTC enforcement databases
2. **Identify the closest legal precedent** — what happened when a similar business faced regulatory or legal challenge?
3. **Cite properly** — case name [year] court reference (e.g., OBG Ltd v Allan [2007] UKHL 21)

### Step 6 — Terms of Service Risk Analysis

For AI wrapper and platform-dependent businesses:

1. **Fetch the ToS/acceptable use policy** of every platform the business depends on
2. **Identify clauses that the business model may conflict with**
3. **Assess the risk**: what happens if the platform enforces against the business?
4. **Document workarounds or compliance strategies** if they exist

### Step 7 — Write the Regulatory Risk Section

Structure the output as:

```
**Risk X: [Regulatory/Legal Risk Title]**

The business [description of regulatory exposure]. [Regulatory body] governs this
through [specific framework/guidance] (citation). The relevant guidance states
[quoted or paraphrased passage with precise citation].

[Assessment of where the business falls relative to the regulatory perimeter]

[Enforcement precedent if any — cite cases]

[Probability and impact assessment]

[Mitigation: what the business can do to reduce this risk]
```

---

## Citation Standards for Regulatory Sources

**UK regulatory guidance**:
```
FCA (year) Document title. Financial Conduct Authority Handbook. Available at: URL (Accessed: date).
```

**US regulatory guidance**:
```
SEC (year) Document title. Washington, D.C.: U.S. Securities and Exchange Commission.
Available at: URL (Accessed: date).
```

**Case law (UK)**:
```
Case Name [Year] Court Reference.
```

**Case law (US)**:
```
Case Name, Volume Reporter Page (Court Year).
```

**Terms of service**:
```
Company Name (year) Document title. Available at: URL (Accessed: date).
```

---

## Anti-Patterns

| Don't | Why | Instead |
|-------|-----|---------|
| State "no regulation applies" without checking | Almost every business has some regulatory surface | Research the specific bodies and cite your finding |
| Use secondary commentary as the primary source | Blog posts about regulation are often wrong | Fetch the actual regulatory guidance document |
| Ignore terms-of-service risk | Platform ToS can be more immediately lethal than regulation | Fetch and analyse every dependent platform's ToS |
| Provide legal advice | You are an analyst, not a lawyer | Frame findings as risk analysis, recommend professional legal review where appropriate |
| Assume US regulation applies everywhere | Regulatory frameworks are jurisdictional | Research the specific jurisdictions relevant to the business |
| Skip enforcement actions | Regulation on paper vs. regulation in practice are different things | Search for recent enforcement actions in the relevant space |
