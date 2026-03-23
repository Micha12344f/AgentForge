#!/usr/bin/env python3
"""
SWOT Analyzer — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates comprehensive SWOT analyses using multiple frameworks.
Can run SWOT, PESTEL, Porter's 5 Forces, and Blue Ocean analysis.

Actions:
  --action swot       Full SWOT analysis of Hedge Edge
  --action pestel     PESTEL macro-environment analysis
  --action porter     Porter's Five Forces analysis
  --action blue-ocean Blue Ocean strategy canvas
  --action full       Run ALL frameworks in one shot

Usage:
  python swot_analyzer.py --action swot
  python swot_analyzer.py --action full
  python swot_analyzer.py --action porter
"""

import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import log_task

AGENT = "Strategy"
AGENT_KEY = "legal"

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')

CONTEXT = """Hedge Edge — Company Profile:
- UK-based SaaS startup (pre-revenue / early-revenue stage)
- Product: Desktop Electron app for prop-firm traders to hedge drawdown risk
- Revenue model: Subscriptions (Starter/Pro/Enterprise via Creem.io) + IB commissions from brokers
- Target market: Proprietary trading firm traders globally (~500k+ active funded traders)
- Platform integrations: MT4, MT5 (planned: cTrader)
- Team: Small, founder-led
- Infrastructure: Electron desktop app, Supabase backend, Node.js/TypeScript
- Distribution: Direct sales, broker partnerships (Vantage, BlackBull), community (Discord)
- Competitors: No direct competitor does drawdown hedging for prop-firm traders specifically
- Key differentiator: Only tool that actively hedges drawdown risk (not just monitors)"""


def _llm(system: str, prompt: str) -> str:
    return chat(AGENT_KEY, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ], temperature=0.3, max_tokens=4096)


def _save(content: str, label: str) -> str:
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"framework_{label}_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def action_swot(args):
    """Full SWOT analysis."""
    print(f"\n{'=' * 60}")
    print(f"  🎯 SWOT ANALYSIS — HEDGE EDGE")
    print(f"{'=' * 60}\n")

    result = _llm(
        "You are a McKinsey strategy partner conducting a SWOT analysis.",
        f"""{CONTEXT}

Produce a board-ready SWOT analysis:

## Strengths (Internal Positives)
- List 8-10 strengths with evidence/reasoning
- Rate each: Critical / Important / Nice-to-have
- Identify which strengths are sustainable vs temporary

## Weaknesses (Internal Negatives)
- List 8-10 weaknesses honestly
- Rate severity: Critical / Significant / Minor
- For each, suggest a mitigation strategy

## Opportunities (External Positives)
- List 8-10 market opportunities
- Rate each by: Size (S/M/L) × Feasibility (Easy/Medium/Hard) × Urgency (Now/Soon/Later)
- Prioritise top 3 to pursue first

## Threats (External Negatives)
- List 8-10 threats
- Rate likelihood (High/Medium/Low) × Impact (Critical/Significant/Minor)
- For each, identify an early warning signal

## SWOT Cross-Analysis (The Real Value)
- **SO strategies**: Use Strengths to capture Opportunities
- **WO strategies**: Address Weaknesses to enable Opportunities
- **ST strategies**: Use Strengths to defend against Threats
- **WT strategies**: Minimise Weaknesses to avoid Threats

## Priority Actions (Next 90 Days)
Top 5 actions with owner, deadline, and expected impact."""
    )

    print(result)
    filepath = _save(f"# SWOT Analysis — Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "swot")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "SWOT analysis", "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_pestel(args):
    """PESTEL macro-environment analysis."""
    print(f"\n{'=' * 60}")
    print(f"  🌐 PESTEL ANALYSIS — HEDGE EDGE")
    print(f"{'=' * 60}\n")

    result = _llm(
        "You are a macro-strategy analyst using the PESTEL framework.",
        f"""{CONTEXT}

Produce a comprehensive PESTEL analysis for Hedge Edge:

## Political
- UK post-Brexit fintech policy, government support for fintech
- Global political attitudes to retail/prop trading
- Impact rating: HIGH/MEDIUM/LOW

## Economic
- Interest rates, FX volatility, recession risk
- Retail trader income trends, willingness to pay
- Impact rating: HIGH/MEDIUM/LOW

## Social
- Gig economy/side-hustle culture driving prop trading interest
- Trust in fintech, financial literacy trends
- Impact rating: HIGH/MEDIUM/LOW

## Technological
- Desktop vs web vs mobile trends
- AI/ML in trading, platform evolution (MT4→MT5→cTrader)
- Impact rating: HIGH/MEDIUM/LOW

## Environmental
- ESG considerations for fintech
- Carbon footprint of trading infrastructure
- Impact rating: HIGH/MEDIUM/LOW

## Legal
- FCA regulations, GDPR, consumer duty
- Prop-firm regulatory classification uncertainty
- Impact rating: HIGH/MEDIUM/LOW

For each factor: Current State → Trend Direction → Impact on Hedge Edge → Required Response

End with an overall **Macro Readiness Score** (1-100) and priority actions."""
    )

    print(result)
    filepath = _save(f"# PESTEL Analysis — Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "pestel")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "PESTEL analysis", "Complete", "P2", f"file={os.path.basename(filepath)}")


def action_porter(args):
    """Porter's Five Forces analysis."""
    print(f"\n{'=' * 60}")
    print(f"  ⚔️ PORTER'S FIVE FORCES — PROP-FIRM HEDGING")
    print(f"{'=' * 60}\n")

    result = _llm(
        "You are Michael Porter applying your Five Forces framework to a specific market.",
        f"""{CONTEXT}

Apply Porter's Five Forces to the prop-firm hedging/risk-management software market:

## 1. Threat of New Entrants
- Barriers to entry (technology, regulation, trust, distribution)
- Capital requirements
- Switching costs for customers
- **Force Strength**: WEAK/MODERATE/STRONG
- **Hedge Edge Defence**: What moats protect us

## 2. Bargaining Power of Buyers (Prop-Firm Traders)
- Number of alternatives available
- Price sensitivity of prop traders
- Importance of hedging to their success
- **Force Strength**: WEAK/MODERATE/STRONG
- **Hedge Edge Strategy**: How to reduce buyer power

## 3. Bargaining Power of Suppliers
- Key suppliers (brokers, data feeds, platforms, cloud infra)
- Switching costs for changing suppliers
- Supplier concentration
- **Force Strength**: WEAK/MODERATE/STRONG
- **Hedge Edge Strategy**: How to manage supplier relationships

## 4. Threat of Substitutes
- Manual hedging (traders doing it themselves)
- Risk management features built into prop firms
- General trading tools that could add hedging
- **Force Strength**: WEAK/MODERATE/STRONG
- **Hedge Edge Defence**: Why substitutes are inferior

## 5. Industry Rivalry
- Who are the direct competitors (if any)
- Market growth rate (growing market = less rivalry)
- Product differentiation
- **Force Strength**: WEAK/MODERATE/STRONG
- **Hedge Edge Position**: Our competitive advantage

## Overall Industry Attractiveness Score (1-10)
## Strategic Recommendations Based on Forces Analysis"""
    )

    print(result)
    filepath = _save(f"# Porter's Five Forces — Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "porter")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Porter's Five Forces", "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_blue_ocean(args):
    """Blue Ocean strategy canvas."""
    print(f"\n{'=' * 60}")
    print(f"  🌊 BLUE OCEAN STRATEGY — HEDGE EDGE")
    print(f"{'=' * 60}\n")

    result = _llm(
        "You are a Blue Ocean Strategy consultant (Kim & Mauborgne framework).",
        f"""{CONTEXT}

Apply Blue Ocean Strategy to Hedge Edge:

## Current Red Ocean (Where Everyone Competes)
- What are the competitive factors in prop-firm tools today?
- Where do most competitors invest and compete?
- What does the typical value curve look like?

## Strategy Canvas
Create a comparison table showing competitive factors rated 1-5 for:
- Typical Prop Firm Platform
- Risk Management Tools
- Hedge Edge (current)
- Hedge Edge (blue ocean target)

Factors to evaluate:
Price, Features, Ease of Use, Platform Coverage, Risk Analytics,
Active Hedging, Community, Support, Brand Trust, Customisation,
Integration Depth, Educational Content, Real-time Alerts

## Four Actions Framework (ERRC Grid)
| Eliminate | Reduce |
|-----------|--------|
| (factors to eliminate) | (factors to reduce below industry) |

| Raise | Create |
|-------|--------|
| (factors to raise above industry) | (entirely new factors) |

## New Value Curve
- What does Hedge Edge's differentiated offering look like?
- What's the "blue ocean" — the uncontested market space?

## Three Tiers of Non-Customers
1. Soon-to-be non-customers (prop traders almost churning from firms)
2. Refusing non-customers (traders who avoid prop firms due to risk)
3. Unexplored non-customers (traders in adjacent markets)

## Strategic Move Sequence
Test: Buyer Utility → Price → Cost → Adoption hurdles

## Implementation Roadmap (6 months)"""
    )

    print(result)
    filepath = _save(f"# Blue Ocean Strategy — Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "blue_ocean")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Blue Ocean strategy", "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_full(args):
    """Run ALL strategic frameworks."""
    print(f"\n{'=' * 60}")
    print(f"  🧠 FULL STRATEGIC FRAMEWORK SUITE")
    print(f"{'=' * 60}\n")

    for name, fn in [("SWOT", action_swot), ("PESTEL", action_pestel),
                     ("Porter's 5 Forces", action_porter), ("Blue Ocean", action_blue_ocean)]:
        print(f"\n  Running {name}...")
        fn(args)


ACTIONS = {
    "swot": action_swot,
    "pestel": action_pestel,
    "porter": action_porter,
    "blue-ocean": action_blue_ocean,
    "full": action_full,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SWOT Analyzer — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    args = parser.parse_args()
    ACTIONS[args.action](args)
