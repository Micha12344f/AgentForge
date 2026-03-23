#!/usr/bin/env python3
"""
Deep Researcher — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-source research engine that synthesizes intelligence from the web,
LLM reasoning, and internal data into structured strategic briefs.

Actions:
  --action research   Free-form deep research on any business topic
  --action brief      Generate a strategic briefing document
  --action analyse    Analyse a specific company, market, or trend

Usage:
  python deep_researcher.py --action research --query "prop firm market size 2026"
  python deep_researcher.py --action brief --query "hedging SaaS competitive landscape"
  python deep_researcher.py --action analyse --query "FTMO strengths weaknesses threats"
"""

import sys, os, json, argparse, textwrap
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import add_row, log_task

AGENT = "Strategy"
AGENT_KEY = "legal"  # Strategy uses the legal LLM config (Trinity Large)

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')


# ──────────────────────────────────────────────
# Research Prompts
# ──────────────────────────────────────────────

RESEARCH_SYSTEM = """You are an elite business strategist and research analyst for Hedge Edge,
a UK-based prop-firm hedging SaaS platform. You produce investment-grade research.

Your expertise spans:
- Proprietary trading firm industry (prop firms, funded traders, challenges)
- Hedging and risk management for retail/prop trading
- SaaS business models, unit economics, growth strategy
- Competitive intelligence and market analysis
- Financial analysis frameworks (Porter's 5 Forces, SWOT, PESTEL, BCG Matrix)
- Wisdom from legendary investors (Buffett, Munger, Marks, Dalio, Soros)

When researching, always:
1. Structure findings with clear headers and bullet points
2. Cite specific numbers, dates, and sources where possible
3. Distinguish between facts, estimates, and speculation
4. End with actionable recommendations for Hedge Edge
5. Consider UK regulatory context (FCA, GDPR)

Output in structured Markdown."""

BRIEF_SYSTEM = """You are a McKinsey-tier strategy consultant producing a board-ready briefing
for Hedge Edge (UK prop-firm hedging SaaS). Structure every brief as:

## Executive Summary
(2-3 sentences — the "so what")

## Key Findings
(Numbered list of 5-8 critical insights)

## Analysis
(Deep analysis with data points, frameworks applied)

## Competitive Implications
(What this means for Hedge Edge specifically)

## Recommendations
(Prioritised action items: P0/P1/P2 with owner and timeline)

## Risks & Mitigants
(What could go wrong, how to hedge)

Be precise, analytical, and actionable. Use UK English."""

ANALYSE_SYSTEM = """You are a competitive intelligence analyst. Produce a comprehensive
analysis using multiple strategic frameworks. Structure as:

## Company/Topic Overview
(What it is, key metrics, positioning)

## SWOT Analysis
| Strengths | Weaknesses |
|-----------|------------|
| ... | ... |

| Opportunities | Threats |
|---------------|---------|
| ... | ... |

## Porter's Five Forces Assessment
(Buyer power, supplier power, threat of substitutes, threat of new entrants, rivalry)

## Key Financial/Business Metrics
(Revenue estimates, growth rate, market share, funding, team size)

## Strategic Implications for Hedge Edge
(How does this affect our positioning, what can we learn, what should we do)

## Sources & Confidence Level
(Rate confidence: HIGH/MEDIUM/LOW for each major claim)

Use UK English. Be quantitative wherever possible."""


def _research(query: str, system: str, max_tokens: int = 4096) -> str:
    """Run a research query through the LLM."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    return chat(AGENT_KEY, messages, temperature=0.3, max_tokens=max_tokens)


def _save_output(title: str, content: str, action: str) -> str:
    """Save research output to resources and Notion."""
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:60].strip().replace(" ", "_")
    filename = f"research_{action}_{safe_title}_{ts}.md"
    filepath = os.path.join(RESOURCES_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n")
        f.write(f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"> Action: {action}\n\n")
        f.write(content)

    return filepath


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_research(args):
    """Free-form deep research on any topic."""
    query = args.query
    print(f"\n{'=' * 60}")
    print(f"  🔬 DEEP RESEARCH")
    print(f"{'=' * 60}")
    print(f"\n  Query: {query}")
    print(f"  Researching...\n")

    result = _research(query, RESEARCH_SYSTEM)

    filepath = _save_output(query, result, "research")
    print(result)
    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    print(f"{'─' * 60}")

    log_task(AGENT, f"Deep research: {query[:80]}",
             "Complete", "P2", f"file={os.path.basename(filepath)}")


def action_brief(args):
    """Generate a strategic briefing document."""
    query = args.query
    print(f"\n{'=' * 60}")
    print(f"  📋 STRATEGIC BRIEF")
    print(f"{'=' * 60}")
    print(f"\n  Topic: {query}")
    print(f"  Generating brief...\n")

    result = _research(query, BRIEF_SYSTEM, max_tokens=4096)

    filepath = _save_output(query, result, "brief")
    print(result)
    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    print(f"{'─' * 60}")

    log_task(AGENT, f"Strategic brief: {query[:80]}",
             "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_analyse(args):
    """Analyse a specific company, market, or trend."""
    query = args.query
    print(f"\n{'=' * 60}")
    print(f"  🎯 STRATEGIC ANALYSIS")
    print(f"{'=' * 60}")
    print(f"\n  Target: {query}")
    print(f"  Analysing...\n")

    result = _research(query, ANALYSE_SYSTEM, max_tokens=4096)

    filepath = _save_output(query, result, "analysis")
    print(result)
    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    print(f"{'─' * 60}")

    log_task(AGENT, f"Strategic analysis: {query[:80]}",
             "Complete", "P1", f"file={os.path.basename(filepath)}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

ACTIONS = {
    "research": action_research,
    "brief": action_brief,
    "analyse": action_analyse,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep Researcher — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--query", required=True, help="Research query or topic")
    args = parser.parse_args()
    ACTIONS[args.action](args)
