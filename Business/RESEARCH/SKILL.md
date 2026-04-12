---
name: research
description: "Research Agent — produces investor-grade business thesis documents. Vets AI wrapper and MCP-tool business ideas with zero bias. Researches competitors, scrapes websites, interprets regulatory documents, and generates PDF deliverables from structured templates."
---

# RESEARCH — Skill Command Sheet

> **Adopt this department to gain**: Business thesis creation, competitor research and comparable analysis, regulatory document interpretation, web scraping for market intelligence, statistical research from reputable sources, and automated PDF document generation.

> **Governance**: Research owns thesis content and competitive analysis. Orchestrator alone owns cross-department DOE restructuring and `agents.md` / `SKILL.md` registration.

---

## Core Philosophy

**Zero bias. Zero promotional language. Zero unverified claims.**

This department exists to produce honest, investor-grade analysis of business ideas — particularly those in the AI wrapper and MCP tooling space. The default assumption is scepticism: every claimed advantage must be stress-tested, every market figure must be sourced, and every weakness must be stated plainly. If the analysis flatters the subject, it should be because the evidence supports it, not because the analyst wanted it to.

---

## Skills

### Skill 1 — Business Thesis Builder
| Layer | Path |
|-------|------|
| Directive | `directives/business-thesis.md` |
| Executions | `executions/build_thesis_pdf.py` |
| Resources | `resources/business-thesis-template.md` |
| Use for | Creating complete investor-grade business thesis documents from structured research |

**What this covers**:
- Structured thesis creation following the canonical 5-section template (Summary, History, Product & Service, Market & Competitors, Risk/Return/Exit)
- AI wrapper and MCP-tool specific stress tests (substitution test, integration test, data flywheel test)
- Moat analysis with quantified scoring (0–18 scale)
- Automated PDF generation with professional formatting
- Harvard-style referencing with verified sources only
- Output saved to `resources/outputs/` as PDF

### Skill 2 — Competitor Research & Comparables
| Layer | Path |
|-------|------|
| Directive | `directives/competitor-research.md` |
| Resources | `resources/research-sources.md` |
| Use for | Systematic competitor identification, profiling, and structured comparison |

**What this covers**:
- Tiered competitor classification (Tier 1 direct, Tier 2 adjacent, status quo)
- Website scraping for pricing, features, user metrics, and positioning
- Structured comparison tables across all relevant attributes
- Basis-of-competition analysis (identifying the 4–6 actual competitive dimensions)
- Barrier and competitive response assessment
- Customer perception analysis from forums, Discord, Reddit, Trustpilot, YouTube

### Skill 3 — Regulatory & Legal Research
| Layer | Path |
|-------|------|
| Directive | `directives/regulatory-research.md` |
| Resources | `resources/research-sources.md` |
| Use for | Finding, interpreting, and citing regulatory documentation relevant to a business thesis |

**What this covers**:
- Identifying the relevant regulatory bodies for a given business domain and jurisdiction
- Fetching and interpreting regulatory guidance documents (FCA, SEC, CFTC, GDPR, etc.)
- Legal precedent research for contract, liability, and compliance risk assessment
- Terms-of-service analysis for platform dependency risks
- Regulatory risk scoring and classification
- Proper legal citation format for British and US legal sources

### Skill 4 — Statistical & Market Research
| Layer | Path |
|-------|------|
| Directive | `directives/business-thesis.md` (Section: Market and Competitors guidance) |
| Resources | `resources/research-sources.md` |
| Use for | Sourcing verifiable market data from reputable institutional and academic sources |

**What this covers**:
- Market sizing (TAM/SAM/SOM) from institutional sources only
- Growth rate estimation with transparent methodology
- Bottom-up segment estimation when top-down data is unavailable (show working)
- Source hierarchy: government/central bank data > peer-reviewed > industry analyst reports > company disclosures > management estimates
- Mandatory source verification: if a statistic cannot be traced to a reputable origin, it is flagged as unverified

### Skill 5 — Web Scraping & Intelligence Gathering
| Layer | Path |
|-------|------|
| Directive | `directives/competitor-research.md` (Section: Research Execution) |
| Use for | Scraping competitor websites, regulatory portals, and market data sources |

**What this covers**:
- Fetching competitor homepages, pricing pages, feature pages, and about pages
- Extracting structured data: pricing tiers, platform support, user metrics, team size
- Scraping regulatory portals for guidance documents and enforcement actions
- Forum and community analysis: Discord, Reddit, Trustpilot, MQL5, YouTube
- Respecting robots.txt and rate limits — never brute-force scrape

---

## AI Wrapper & MCP Tool Specialisation

This department has a particular expertise in evaluating businesses that are:
1. **AI wrappers** — products that sit on top of foundational model APIs (OpenAI, Anthropic, Google, etc.) and add a UX, integration, or domain layer
2. **MCP tool products** — products built around the Model Context Protocol for connecting AI agents to external systems

For these products, the following stress tests are **mandatory** in every thesis:

| Test | Question | Failure = |
|------|----------|-----------|
| **Substitution test** | Can the customer achieve the same outcome by using the underlying model/API directly? | Value is convenience only — highly replicable |
| **Integration test** | Does the product connect systems the raw API cannot connect without custom engineering? | If no, the product is a thin wrapper |
| **Data flywheel test** | Does usage generate proprietary data that compounds product quality? | If no, no compounding advantage exists |
| **Model lock-in test** | What happens if the underlying model doubles in price, degrades in quality, or adds competing features? | Business viability collapses if answer is fatal |
| **MCP commoditisation test** | Is the MCP integration available as a pre-built server on glama.ai, smithery.ai, or modelcontextprotocol/servers? | If yes, integration is not a moat |

---

## Workflow

1. **Receive business idea** — user provides company name, product description, and any existing materials
2. **Read the directive** — `Business/RESEARCH/directives/business-thesis.md`
3. **Read the template** — `Business/RESEARCH/resources/business-thesis-template.md`
4. **Research phase** — web scraping, competitor research, regulatory research, statistical research
5. **Analysis phase** — fill template sections with researched findings, apply stress tests, score moats
6. **Draft review** — present key findings and risk flags before PDF generation
7. **PDF generation** — run `Business/RESEARCH/executions/build_thesis_pdf.py` to produce the final PDF
8. **Output** — PDF saved to `Business/RESEARCH/resources/outputs/<company-slug>-thesis-<YYYY-MM>.pdf`
