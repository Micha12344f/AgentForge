#!/usr/bin/env python3
"""
Investor Wisdom Engine — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Channels the thinking of legendary investors and business strategists
to provide world-class strategic advice for Hedge Edge.

Actions:
  --action ask         Ask a specific question to a legendary investor
  --action playbook    Generate a strategic playbook from investor wisdom
  --action debate      Have two investors debate a Hedge Edge strategy question
  --action mental-models  Compile relevant mental models from great thinkers

Usage:
  python investor_wisdom.py --action ask --investor buffett --query "should we raise VC?"
  python investor_wisdom.py --action debate --query "grow fast or grow profitable"
  python investor_wisdom.py --action mental-models
"""

import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import log_task

AGENT = "Strategy"
AGENT_KEY = "legal"

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')

CONTEXT = """Hedge Edge: UK-based SaaS startup. Desktop Electron app that hedges drawdown
risk for prop-firm traders. Revenue from subscriptions + IB broker commissions.
Pre-revenue/early-revenue, founder-led, small team. Target: 500k+ active prop traders globally."""

INVESTORS = {
    "buffett": {
        "name": "Warren Buffett",
        "style": "Value investing, economic moats, long-term compounding, owner-operator mentality",
        "key_ideas": "Circle of competence, margin of safety, float, brand moats, owner earnings",
    },
    "munger": {
        "name": "Charlie Munger",
        "style": "Multi-disciplinary mental models, inversion thinking, avoiding stupidity",
        "key_ideas": "Latticework of mental models, inversion, incentive structures, psychology of misjudgment",
    },
    "dalio": {
        "name": "Ray Dalio",
        "style": "Principles-based, radical transparency, macro hedge fund, systems thinking",
        "key_ideas": "Principles, pain+reflection=progress, believability weighting, machine metaphor",
    },
    "soros": {
        "name": "George Soros",
        "style": "Reflexivity, macro bets, understanding market psychology, calculated aggression",
        "key_ideas": "Reflexivity theory, boom-bust cycles, going for the jugular when right",
    },
    "marks": {
        "name": "Howard Marks",
        "style": "Second-level thinking, risk awareness, market cycles, contrarianism",
        "key_ideas": "Second-level thinking, knowing what you don't know, cycle awareness, risk vs uncertainty",
    },
    "thiel": {
        "name": "Peter Thiel",
        "style": "Zero-to-one thinking, monopoly strategy, secrets, contrarian truth-seeking",
        "key_ideas": "Monopoly > competition, definite optimism, last mover advantage, secrets",
    },
    "bezos": {
        "name": "Jeff Bezos",
        "style": "Day 1 thinking, customer obsession, long-term orientation, two-pizza teams",
        "key_ideas": "Customer obsession, regret minimization, disagree and commit, flywheel effect",
    },
    "grove": {
        "name": "Andy Grove",
        "style": "Strategic inflection points, paranoid leadership, OKR framework",
        "key_ideas": "Only the paranoid survive, 10X forces, strategic inflection points, constructive confrontation",
    },
}


def _llm(system: str, prompt: str) -> str:
    return chat(AGENT_KEY, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ], temperature=0.4, max_tokens=4096)


def _save(content: str, label: str) -> str:
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"wisdom_{label}_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def action_ask(args):
    """Ask a specific question to a legendary investor."""
    investor_key = (args.investor or "buffett").lower()
    query = args.query
    if not query:
        print("  ❌ --query required")
        return

    inv = INVESTORS.get(investor_key)
    if not inv:
        print(f"  ❌ Unknown investor. Available: {', '.join(INVESTORS.keys())}")
        return

    print(f"\n{'=' * 60}")
    print(f"  🎩 ASKING {inv['name'].upper()}")
    print(f"{'=' * 60}\n")

    result = _llm(
        f"""You are {inv['name']}, the legendary investor/business leader.
Known for: {inv['style']}
Core ideas: {inv['key_ideas']}

Stay deeply in character. Quote your actual writings and speeches.
Apply your genuine frameworks and mental models. Be specific, not generic.
When giving advice, draw from actual historical parallels from your career.""",

        f"""{CONTEXT}

The founder of Hedge Edge asks you:
"{query}"

Respond as {inv['name']} would — with your characteristic directness,
wisdom, and specific references to your principles and past experiences.

Structure:
## My Answer
## Why (the reasoning from my framework)
## Historical Parallel (from my career/investments)
## Specific Advice for Hedge Edge
## What I'd Want to See in 12 Months
## The Mistake to Avoid"""
    )

    print(result)
    safe = investor_key + "_" + "".join(c if c.isalnum() else "_" for c in query)[:30]
    filepath = _save(f"# {inv['name']} on: {query}\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     safe)
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, f"{inv['name']}: {query[:50]}", "Complete", "P2",
             f"file={os.path.basename(filepath)}")


def action_debate(args):
    """Have two investors debate a strategy question."""
    query = args.query
    if not query:
        print("  ❌ --query required")
        return

    print(f"\n{'=' * 60}")
    print(f"  ⚔️ INVESTOR DEBATE")
    print(f"{'=' * 60}")
    print(f"  Topic: {query}\n")

    inv_summary = "\n".join(f"- {v['name']}: {v['style']}" for v in INVESTORS.values())

    result = _llm(
        """You are a moderator facilitating a roundtable debate among legendary investors.
Each participant must stay in character with their genuine philosophy.""",

        f"""{CONTEXT}

The participants:
{inv_summary}

The debate question: "{query}"

Produce a structured debate:

## The Question
(Restate clearly)

## Opening Positions
(Each investor's initial stance — 2-3 sentences each, in their voice)

## The Debate
(Back-and-forth exchanges where investors challenge each other's views.
At least 3 rounds of exchange. Include disagreements and surprises.)

## Areas of Agreement
(Where do they converge?)

## Points of Irreconcilable Difference
(Where they'll never agree, and why)

## Synthesis for Hedge Edge
(What should Hedge Edge actually do, given all perspectives?)

## The Verdict
(If you had to pick one investor's advice for Hedge Edge on this topic, whose and why?)"""
    )

    print(result)
    safe = "debate_" + "".join(c if c.isalnum() else "_" for c in query)[:30]
    filepath = _save(f"# Investor Debate: {query}\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     safe)
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, f"Investor debate: {query[:50]}", "Complete", "P2",
             f"file={os.path.basename(filepath)}")


def action_mental_models(args):
    """Compile relevant mental models from great thinkers."""
    print(f"\n{'=' * 60}")
    print(f"  🧠 MENTAL MODELS FOR HEDGE EDGE")
    print(f"{'=' * 60}\n")

    result = _llm(
        """You are a polymath scholar who has mastered the mental models from
Buffett, Munger, Dalio, Thiel, Bezos, Grove, Marks, and Soros.""",

        f"""{CONTEXT}

Compile the 25 most relevant mental models for building Hedge Edge:

For each mental model:
1. **Model Name** — e.g. "Circle of Competence"
2. **Source** — who popularised it
3. **Core Principle** — 1-2 sentence explanation
4. **Applied to Hedge Edge** — specific application
5. **Anti-Pattern** — what violating this model looks like
6. **Decision It Helps With** — specific decisions it clarifies

Group by category:
- **Business Strategy Models** (moats, positioning, competition)
- **Decision Making Models** (inversion, second-level thinking)
- **Growth Models** (flywheels, network effects, scalability)
- **Risk Models** (margin of safety, tail risk, reflexivity)
- **Execution Models** (OKRs, two-pizza teams, disagree-and-commit)
- **Psychology Models** (incentives, loss aversion, social proof)

End with a **Top 5 "Must Internalise" Models for Hedge Edge's Current Stage**."""
    )

    print(result)
    filepath = _save(f"# Mental Models for Hedge Edge\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "mental_models")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Mental models compilation", "Complete", "P2",
             f"file={os.path.basename(filepath)}")


def action_playbook(args):
    """Generate a strategic playbook from investor wisdom."""
    print(f"\n{'=' * 60}")
    print(f"  📖 STRATEGIC PLAYBOOK (Investor Consensus)")
    print(f"{'=' * 60}\n")

    result = _llm(
        """You have studied the complete works of Buffett, Munger, Dalio, Thiel,
Bezos, Grove, Marks, and Soros. Synthesise their collective wisdom.""",

        f"""{CONTEXT}

Create "The Hedge Edge Strategic Playbook" — a synthesised guide drawing
from all legendary investors' wisdom:

## Chapter 1: The Opportunity (Thiel + Buffett)
- Is this a zero-to-one opportunity? What's the secret?
- What would Buffett's moat look like?

## Chapter 2: The Business Model (Bezos + Buffett)
- Subscription + IB commission — analysed through flywheel thinking
- Unit economics through Buffett's "owner earnings" lens

## Chapter 3: Growth Strategy (Bezos + Thiel)
- Customer obsession vs monopoly building
- When to be aggressive vs patient

## Chapter 4: Risk Management (Marks + Soros + Dalio)
- Second-level thinking about our own risks
- Reflexivity in the prop-firm market
- Principled approach to uncertainty

## Chapter 5: Competition (Grove + Porter)
- Strategic inflection points to watch for
- How to spot 10X forces early

## Chapter 6: Capital Allocation (Buffett + Munger)
- Bootstrap vs raise? The Buffett answer
- How to allocate limited resources

## Chapter 7: Culture & Team (Bezos + Dalio)
- Day 1 culture from the start
- Radical transparency for a small team

## Chapter 8: The 12-Month Plan
- Synthesised roadmap applying all frameworks
- Monthly milestones
- KPIs to track"""
    )

    print(result)
    filepath = _save(f"# Strategic Playbook — Investor Wisdom\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "playbook")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Strategic playbook generated", "Complete", "P1",
             f"file={os.path.basename(filepath)}")


ACTIONS = {
    "ask": action_ask,
    "debate": action_debate,
    "mental-models": action_mental_models,
    "playbook": action_playbook,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Investor Wisdom — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--investor", help="Investor to channel (buffett/munger/dalio/soros/marks/thiel/bezos/grove)")
    parser.add_argument("--query", help="Question or topic")
    args = parser.parse_args()
    ACTIONS[args.action](args)
