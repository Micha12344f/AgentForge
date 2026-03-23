#!/usr/bin/env python3
"""
Competitor Intelligence Engine — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deep competitive analysis against prop-firm hedging/risk tools.

Actions:
  --action scan        Quick competitive landscape scan
  --action deep-dive   Full analysis of a specific competitor
  --action matrix      Feature comparison matrix vs Hedge Edge
  --action moat        Analyse Hedge Edge's competitive moat

Usage:
  python competitor_intel.py --action scan
  python competitor_intel.py --action deep-dive --target "FTMO"
  python competitor_intel.py --action matrix
  python competitor_intel.py --action moat
"""

import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import add_row, log_task

AGENT = "Strategy"
AGENT_KEY = "legal"

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')
PROFILES_PATH = os.path.join(RESOURCES_DIR, "competitor-profiles.json")

# ──────────────────────────────────────────────
# Known competitors and their profiles
# ──────────────────────────────────────────────

KNOWN_COMPETITORS = {
    "FTMO": {
        "url": "https://ftmo.com",
        "type": "Prop Firm (Challenge)",
        "features": ["Challenge model", "Scaling plan", "No hedging tool", "MT4/MT5"],
        "pricing": "Challenge fees (€155-€1,080)",
        "hq": "Czech Republic",
        "weakness": "No built-in risk hedging for traders",
    },
    "MyForexFunds": {
        "url": "https://myforexfunds.com",
        "type": "Prop Firm (Challenge)",
        "features": ["Rapid/Evaluation/Accelerated", "Low cost", "MT4/MT5"],
        "pricing": "Challenge fees ($49-$499)",
        "hq": "Canada",
        "weakness": "Regulatory scrutiny, shut down by CFTC in 2023",
    },
    "The5ers": {
        "url": "https://the5ers.com",
        "type": "Prop Firm (Instant Funding)",
        "features": ["Instant funding", "Growth plan", "MT5/cTrader"],
        "pricing": "$95-$875",
        "hq": "Israel",
        "weakness": "No hedging analytics",
    },
    "FundedNext": {
        "url": "https://fundednext.com",
        "type": "Prop Firm (Challenge)",
        "features": ["Stellar/Evaluation/Express", "15% profit share from challenge phase"],
        "pricing": "$32-$999",
        "hq": "UAE",
        "weakness": "No hedging integration",
    },
    "TopStep": {
        "url": "https://topstep.com",
        "type": "Prop Firm (Futures)",
        "features": ["Futures trading", "Trading Combine", "Real funded accounts"],
        "pricing": "$165-$375/mo",
        "hq": "USA",
        "weakness": "Futures only, no FX hedging",
    },
    "Darwinex": {
        "url": "https://darwinex.com",
        "type": "Asset Manager / Prop",
        "features": ["DARWIN index", "Investor allocation", "FCA regulated"],
        "pricing": "Performance fees",
        "hq": "UK",
        "weakness": "Complex model, high barrier to entry",
    },
    "cTrader": {
        "url": "https://ctrader.com",
        "type": "Trading Platform",
        "features": ["Advanced charting", "cBots", "Copy trading"],
        "pricing": "Broker-integrated",
        "hq": "Cyprus",
        "weakness": "Platform not risk management tool",
    },
}


def _load_profiles() -> dict:
    """Load existing competitor profiles."""
    if os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_profiles(profiles: dict) -> None:
    """Save competitor profiles."""
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, default=str)


def _llm(system: str, prompt: str, max_tokens: int = 4096) -> str:
    return chat(AGENT_KEY, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ], temperature=0.3, max_tokens=max_tokens)


# ──────────────────────────────────────────────
# Actions
# ──────────────────────────────────────────────

def action_scan(args):
    """Quick competitive landscape scan."""
    print(f"\n{'=' * 60}")
    print(f"  🔍 COMPETITIVE LANDSCAPE SCAN")
    print(f"{'=' * 60}\n")

    competitor_data = json.dumps(KNOWN_COMPETITORS, indent=2)
    result = _llm(
        """You are a competitive intelligence analyst for Hedge Edge, a UK-based
prop-firm hedging SaaS. Hedge Edge sells a desktop Electron app that helps
proprietary trading firm traders hedge their drawdown risk.

Analyse the competitive landscape and produce a structured assessment.""",

        f"""Here are the known competitors and their profiles:

{competitor_data}

Produce:
1. **Competitive Landscape Overview** — who plays where, market segments
2. **Threat Assessment** — rank competitors by threat level (Critical/High/Medium/Low)
3. **Gap Analysis** — what nobody does that Hedge Edge could
4. **Strategic Positioning** — where Hedge Edge sits vs everyone else
5. **Immediate Actions** — top 3 things Hedge Edge should do this quarter

Use Markdown tables where appropriate. Be specific and quantitative."""
    )

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"competitive_scan_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Competitive Landscape Scan\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Competitive landscape scan", "Complete", "P1",
             f"file={os.path.basename(filepath)}")


def action_deep_dive(args):
    """Full analysis of a specific competitor."""
    target = args.target
    if not target:
        print("  ❌ --target required for deep-dive (e.g. --target FTMO)")
        return

    print(f"\n{'=' * 60}")
    print(f"  🎯 DEEP DIVE: {target}")
    print(f"{'=' * 60}\n")

    known_data = KNOWN_COMPETITORS.get(target, {})
    ctx = f"Known data on {target}: {json.dumps(known_data, indent=2)}" if known_data else f"No existing data on {target}."

    result = _llm(
        """You are a competitive intelligence analyst for Hedge Edge (UK prop-firm hedging SaaS).
Produce a comprehensive competitive deep-dive.""",

        f"""Deep-dive analysis on: {target}

{ctx}

Cover:
1. **Company Overview** — founding, HQ, funding, team size, revenue estimates
2. **Product Analysis** — core features, UX, pricing tiers, technology stack
3. **Market Position** — target customers, market share, brand perception
4. **SWOT Analysis** — detailed strengths, weaknesses, opportunities, threats
5. **Business Model** — how they make money, unit economics if estimable
6. **Growth Trajectory** — growth signals, recent launches, hiring patterns
7. **Threat to Hedge Edge** — specific ways they could threaten our position
8. **How Hedge Edge Can Win** — our advantages and counter-strategies
9. **Confidence Assessment** — rate each section HIGH/MEDIUM/LOW confidence

Be analytical and quantitative. Separate facts from estimates."""
    )

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = target.replace(" ", "_")[:30]
    filepath = os.path.join(RESOURCES_DIR, f"deep_dive_{safe}_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Deep Dive: {target}\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, f"Competitor deep-dive: {target}", "Complete", "P1",
             f"file={os.path.basename(filepath)}")


def action_matrix(args):
    """Feature comparison matrix vs Hedge Edge."""
    print(f"\n{'=' * 60}")
    print(f"  📊 FEATURE COMPARISON MATRIX")
    print(f"{'=' * 60}\n")

    competitor_data = json.dumps(KNOWN_COMPETITORS, indent=2)
    result = _llm(
        """You are a product strategist for Hedge Edge, a UK desktop app that hedges
drawdown risk for prop-firm traders.""",

        f"""Create a comprehensive feature comparison matrix.

Known competitors:
{competitor_data}

Hedge Edge features:
- Desktop Electron app (Windows)
- Real-time drawdown hedging
- Multi-account monitoring
- Risk analytics dashboard
- Automated hedge execution
- MT4/MT5 integration
- Subscription model (Starter/Pro/Enterprise)
- UK-based, targeting global prop firm traders

Produce:
1. A **Markdown comparison table** with features as rows and companies as columns
   Use ✅/❌/🔶 (partial) for each cell
2. **Feature Gap Priorities** — what Hedge Edge needs most urgently
3. **Unique Value Propositions** — what Hedge Edge has that nobody else does
4. **Areas of Parity** — where we match competitors
5. **Biggest Differentiators by competitor** — what each does better than us"""
    )

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"feature_matrix_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Feature Comparison Matrix\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Feature comparison matrix", "Complete", "P1",
             f"file={os.path.basename(filepath)}")


def action_moat(args):
    """Analyse Hedge Edge's competitive moat."""
    print(f"\n{'=' * 60}")
    print(f"  🏰 COMPETITIVE MOAT ANALYSIS")
    print(f"{'=' * 60}\n")

    result = _llm(
        """You are Warren Buffett's strategic advisor, applying his moat analysis
framework to a UK fintech SaaS startup.""",

        """Analyse Hedge Edge's competitive moat using Buffett's framework.

Hedge Edge: UK-based prop-firm hedging SaaS platform.
- Desktop Electron app that hedges drawdown risk for prop-firm traders
- Revenue: subscriptions + IB commission deals with brokers
- Target: proprietary trading firm traders globally
- Stage: pre-revenue / early revenue
- Team: small, founder-led

Apply these moat dimensions:
1. **Brand Moat** — brand recognition, trust, reputation
2. **Switching Costs** — how locked-in are customers
3. **Network Effects** — does the product get better with more users
4. **Cost Advantages** — can we deliver cheaper than competitors
5. **Intangible Assets** — IP, patents, regulatory licenses, data advantages
6. **Efficient Scale** — is the market too small for multiple players

For each dimension:
- Rate current moat strength: NONE / WEAK / MODERATE / STRONG
- Identify specific actions to strengthen it
- Estimate time and investment needed

Then provide an **Overall Moat Score** and **3-Year Moat Building Roadmap**.

Channel Buffett: "In business, I look for economic castles protected by
unbreachable moats." — What would Buffett say about Hedge Edge?"""
    )

    print(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"moat_analysis_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Competitive Moat Analysis\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}")

    print(f"\n{'─' * 60}")
    print(f"  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Competitive moat analysis", "Complete", "P1",
             f"file={os.path.basename(filepath)}")


ACTIONS = {
    "scan": action_scan,
    "deep-dive": action_deep_dive,
    "matrix": action_matrix,
    "moat": action_moat,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Competitor Intelligence — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--target", help="Competitor name for deep-dive")
    args = parser.parse_args()
    ACTIONS[args.action](args)
