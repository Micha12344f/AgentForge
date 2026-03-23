#!/usr/bin/env python3
"""
Trend Scanner — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scans for industry trends, emerging threats, and market shifts
relevant to the prop-firm/hedging/fintech space.

Actions:
  --action industry    Prop-firm industry trend analysis
  --action fintech     Broader fintech/trading tech trends
  --action regulatory  Regulatory trend scan (FCA, ESMA, global)
  --action macro       Macro-economic trends affecting prop trading

Usage:
  python trend_scanner.py --action industry
  python trend_scanner.py --action regulatory
  python trend_scanner.py --action macro
"""

import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from shared.llm_router import chat
from shared.notion_client import log_task

AGENT = "Strategy"
AGENT_KEY = "legal"

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')


def _llm(system: str, prompt: str) -> str:
    return chat(AGENT_KEY, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ], temperature=0.3, max_tokens=4096)


def _save(content: str, label: str) -> str:
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESOURCES_DIR, f"trends_{label}_{ts}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


SYSTEM = """You are a fintech industry analyst specialising in prop trading,
hedging technology, and retail trading infrastructure. You monitor regulatory
bodies (FCA, ESMA, CFTC, ASIC), trading platforms (MT4/MT5/cTrader),
prop firms, and the broader fintech ecosystem.

Hedge Edge context: UK-based SaaS that hedges drawdown risk for prop-firm traders.
Desktop Electron app, subscription + IB commission model.

Always structure your analysis with:
- Clear trend identification with supporting evidence
- Timeline assessment (emerging/growing/mature/declining)
- Impact rating for Hedge Edge (Critical/High/Medium/Low)
- Recommended response (act now, monitor, ignore)
- Confidence level for each trend (HIGH/MEDIUM/LOW)

Use UK English. Be specific with dates, numbers, and sources."""


def action_industry(args):
    """Prop-firm industry trend analysis."""
    print(f"\n{'=' * 60}")
    print(f"  📡 PROP-FIRM INDUSTRY TRENDS")
    print(f"{'=' * 60}\n")

    result = _llm(SYSTEM, """Analyse current trends in the proprietary trading firm industry:

1. **Market Structure Trends** — consolidation, new entrants, business model evolution
2. **Technology Trends** — platform shifts, API-first, mobile, AI/ML in trading
3. **Customer Behaviour Trends** — trader demographics, expectations, pain points
4. **Business Model Trends** — challenge fee models, profit splits, subscription shifts
5. **Risk Management Trends** — how firms handle drawdown, hedging approaches
6. **Emerging Opportunities** — gaps in the market Hedge Edge should exploit
7. **Existential Threats** — things that could kill the prop-firm model entirely

For each trend provide: Description → Evidence → Timeline → Impact on Hedge Edge → Recommended Action

End with a **Trend Heatmap** — rank all trends by urgency × impact.""")

    print(result)
    filepath = _save(f"# Prop-Firm Industry Trends\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "industry")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Industry trend scan", "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_fintech(args):
    """Broader fintech/trading tech trends."""
    print(f"\n{'=' * 60}")
    print(f"  🚀 FINTECH & TRADING TECH TRENDS")
    print(f"{'=' * 60}\n")

    result = _llm(SYSTEM, """Analyse broader fintech and trading technology trends:

1. **AI in Trading** — LLMs, ML models, automated strategies, sentiment analysis
2. **Platform Evolution** — MT4/MT5 sunset timelines, cTrader growth, FIX protocol
3. **Embedded Finance** — APIs, Banking-as-a-Service for trading firms
4. **Regulatory Technology** — compliance automation, KYC/AML, trade reporting
5. **Desktop vs Cloud vs Mobile** — where is trading software heading
6. **Data & Analytics** — real-time analytics, alternative data, risk dashboards
7. **Payments & Settlement** — crypto settlement, instant payouts, multi-currency
8. **Open Banking** — PSD2/open banking implications for trading platforms

For each: Trend → Relevance to Hedge Edge → Adoption Timeline → Action Required""")

    print(result)
    filepath = _save(f"# Fintech & Trading Tech Trends\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "fintech")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Fintech trend scan", "Complete", "P2", f"file={os.path.basename(filepath)}")


def action_regulatory(args):
    """Regulatory trend scan."""
    print(f"\n{'=' * 60}")
    print(f"  ⚖️ REGULATORY TRENDS")
    print(f"{'=' * 60}\n")

    result = _llm(SYSTEM, """Analyse regulatory trends affecting prop firms and hedging software:

1. **FCA (UK)** — financial promotions, consumer duty, fintech supervision
2. **ESMA (EU)** — MiFID III, retail trading restrictions, CFD regulations
3. **CFTC/SEC (US)** — prop firm scrutiny (MyForexFunds shutdown), DeFi regs
4. **ASIC (Australia)** — CFD restrictions, platform licensing
5. **Global KYC/AML** — travel rule, beneficial ownership, sanctions screening
6. **GDPR/Data** — UK GDPR evolution, data localisation, AI Act implications
7. **Prop Firm Specific** — are regulators treating prop firms as investment firms?

For each jurisdiction:
- Current regulatory posture
- Upcoming changes with dates
- Specific impact on Hedge Edge
- Compliance actions needed
- Risk level (RED/AMBER/GREEN)

End with a **Regulatory Risk Matrix** and **Compliance Roadmap**.""")

    print(result)
    filepath = _save(f"# Regulatory Trends\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "regulatory")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Regulatory trend scan", "Complete", "P1", f"file={os.path.basename(filepath)}")


def action_macro(args):
    """Macro-economic trends affecting prop trading."""
    print(f"\n{'=' * 60}")
    print(f"  🌍 MACRO-ECONOMIC TRENDS")
    print(f"{'=' * 60}\n")

    result = _llm(SYSTEM, """Analyse macro-economic trends and their impact on prop trading:

1. **Interest Rates** — Fed/BoE/ECB paths, impact on FX volatility and trading volumes
2. **Market Volatility** — VIX trends, geopolitical risk, event-driven vol
3. **Retail Trading Boom** — is retail trading still growing or plateauing
4. **Employment/Gig Economy** — more people seeking prop trading as career
5. **Currency Markets** — major FX trends, emerging market opportunities
6. **Inflation** — impact on subscription willingness to pay
7. **Geopolitical** — trade wars, conflicts, sanctions → trading opportunities
8. **Technology Adoption** — fintech penetration rates by region

For each: Current State → 6-Month Outlook → 12-Month Outlook → Impact on Hedge Edge

End with a **Scenario Analysis**:
- Bull case for Hedge Edge
- Base case
- Bear case
With probability weightings.""")

    print(result)
    filepath = _save(f"# Macro-Economic Trends\n> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n{result}",
                     "macro")
    print(f"\n  📄 Saved: {os.path.basename(filepath)}")
    log_task(AGENT, "Macro trend scan", "Complete", "P2", f"file={os.path.basename(filepath)}")


ACTIONS = {
    "industry": action_industry,
    "fintech": action_fintech,
    "regulatory": action_regulatory,
    "macro": action_macro,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trend Scanner — Strategy Agent")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    args = parser.parse_args()
    ACTIONS[args.action](args)
