# Network Intelligence — RESEARCH Directive

## Purpose

Turn people discovered during research into durable network intelligence. The research agent should not repeatedly rediscover useful humans. It should persist them, enrich them, and connect them to active opportunities.

## Owner

RESEARCH

## Trigger

Use this directive whenever:
- a research task uncovers a relevant person
- a user asks who to talk to, who can buy, who can introduce, or who matters in a market
- a thesis, discovery run, or competitor scan identifies operators, founders, investors, or ecosystem connectors
- the agent needs to build a reusable relationship map around an opportunity

## Execution

| Layer | Path |
|-------|------|
| Execution | `Business/RESEARCH/executions/network_capture.py` |
| Database helper | `Business/RESEARCH/resources/Network/network_db.py` |
| Database | `Business/RESEARCH/resources/Network/network.db` |

## Core Rule

If a person is likely to matter again, store them now.

Do not wait for the user to ask twice.

## What Counts As A Relevant Person

Capture people who are one or more of the following:
- direct buyer
- workflow operator with first-hand pain
- domain expert
- partner or referral source
- ecosystem connector
- investor or acquirer candidate
- competitor founder or key executive

Do not capture people with no plausible strategic use.

## Minimum Data To Store

For each captured person, store at least:
- full name
- current role or strongest known affiliation
- source URL or concrete source note
- short profile summary
- relationship type
- tags

If an active opportunity exists, also store:
- opportunity name
- match score
- match type
- rationale
- suggested next step

## Research Flow

### Step 1 — Find the person

Use public sources: company sites, LinkedIn, Substack, X, interviews, bios, podcasts, press coverage, conference pages, investor pages, community sites, and company registries where relevant.

### Step 2 — Verify the profile

Confirm at least one concrete role, affiliation, or reason the person matters. If the role is stale or ambiguous, say so in the summary instead of pretending certainty.

### Step 3 — Write a decision-useful summary

The summary should answer:
- who they are
- why they matter
- how they connect to the opportunity

Avoid vague summaries like "marketing leader" or "interesting contact." Be specific.

### Step 4 — Persist to the database

Use `network_capture.py` to upsert:
- the person
- any source metadata
- the active opportunity if needed
- the person-opportunity match

### Step 5 — Keep the network clean

Update existing records instead of creating duplicates. Prefer a single durable record per person with richer metadata over multiple thin records.

## Match Logic

Score people against an opportunity using the strongest fit:

| Match type | Meaning |
|------------|---------|
| `buyer` | Could purchase directly |
| `operator` | Feels the workflow pain directly |
| `partner` | Could distribute, sponsor, or integrate |
| `introducer` | Can open doors to likely buyers or operators |
| `investor` | Could fund or validate the business |
| `competitor` | Useful for category mapping or response analysis |
| `expert` | Can sharpen understanding of the market or problem |

Score guidance:
- `80–100`: strong immediate relevance
- `60–79`: useful but indirect
- `40–59`: speculative relevance
- `<40`: probably not worth storing unless strategically unusual

## Anti-Patterns

| Don't | Why |
|------|-----|
| Keep people only in temporary notes | The knowledge is lost and must be rediscovered |
| Store names without a why | The record is not decision-useful |
| Add every person mentioned online | Noise kills the value of the network |
| Treat connectors as buyers | Outreach strategy becomes confused |
| Pretend certainty on incomplete bios | False precision degrades trust in the dataset |

## Output Standard

At the end of a meaningful research run, the network should be stronger than it was at the start:
- more relevant people stored
- better sources attached
- clearer opportunity matches recorded
- cleaner next steps for outreach or validation