#!/usr/bin/env python3
"""
financial_promotions_auditor.py — FCA Financial Promotions Compliance
=====================================================================
Scans Hedge Edge marketing copy for FCA financial promotions violations.
Checks landing page text, social media drafts, and email templates.

Usage:
    python financial_promotions_auditor.py --scan-url https://hedgeedge.info
    python financial_promotions_auditor.py --scan-file marketing_copy.md
    python financial_promotions_auditor.py --scan-text "Guaranteed profits with our hedging tool"
    python financial_promotions_auditor.py --generate-disclaimers
"""

import argparse
import json
import logging
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5].parent.parent.parent))
from shared.notion_client import log_task

_log = logging.getLogger("fca_promotions")
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ── Prohibited phrases / patterns ────────────────────────────────────

PROHIBITED_PATTERNS = [
    {
        "pattern": r"\bguaranteed?\s+(return|profit|income|yield)",
        "rule": "FCA COBS 4.5.2R",
        "severity": "CRITICAL",
        "reason": "Cannot guarantee returns on financial products",
        "fix": "Replace with 'potential' or 'historical' returns with disclaimer",
    },
    {
        "pattern": r"\brisk[\s-]*free\b",
        "rule": "FCA COBS 4.5.2R",
        "severity": "CRITICAL",
        "reason": "No financial product is risk-free",
        "fix": "Replace with 'risk-managed' or 'capital protection strategy'",
    },
    {
        "pattern": r"\bno[\s-]*loss\b",
        "rule": "FCA COBS 4.5.2R",
        "severity": "CRITICAL",
        "reason": "Implies zero downside which is misleading",
        "fix": "Replace with 'reduced risk' or 'hedged exposure'",
    },
    {
        "pattern": r"\b100%\s*(safe|secure|protection|guaranteed)",
        "rule": "FCA COBS 4.5.8R",
        "severity": "HIGH",
        "reason": "Absolute claims about safety are misleading",
        "fix": "Use qualified language: 'designed to help protect' or 'aims to reduce risk'",
    },
    {
        "pattern": r"\bmake\s+money\s+(fast|quick|easy|guaranteed)",
        "rule": "FCA COBS 4.5.2R",
        "severity": "CRITICAL",
        "reason": "Get-rich-quick language is prohibited",
        "fix": "Focus on the tool's functionality, not income promises",
    },
    {
        "pattern": r"\bpassive\s+income\b",
        "rule": "ASA CAP Code Rule 3.1",
        "severity": "MEDIUM",
        "reason": "Implies effortless returns; needs significant qualification",
        "fix": "Describe the active management required; add disclaimers",
    },
    {
        "pattern": r"\b28x\s*ROI\b",
        "rule": "FCA COBS 4.6",
        "severity": "MEDIUM",
        "reason": "ROI claims must include basis, time period, and disclaimers",
        "fix": "Add: 'Based on [specific scenario]. Past performance is not indicative of future results.'",
    },
    {
        "pattern": r"\balways\s+(win|profit|make money)",
        "rule": "FCA COBS 4.5.2R",
        "severity": "CRITICAL",
        "reason": "No strategy always wins",
        "fix": "Remove absolute claims; use 'designed to help' language",
    },
    {
        "pattern": r"\bfinancial\s+advice\b",
        "rule": "FSMA 2000 s.19",
        "severity": "HIGH",
        "reason": "Hedge Edge is not authorised to give financial advice",
        "fix": "Add disclaimer: 'This is not financial advice. Consult a qualified financial adviser.'",
    },
    {
        "pattern": r"\binvestment\s+(advice|recommendation)",
        "rule": "FSMA 2000 s.19",
        "severity": "HIGH",
        "reason": "Must not hold out as providing investment advice without FCA authorisation",
        "fix": "Clarify: 'Hedge Edge is a trade management tool, not an investment advisory service.'",
    },
]

# ── Required disclaimers ─────────────────────────────────────────────

REQUIRED_DISCLAIMERS = {
    "capital_risk": {
        "text": "Trading involves risk. You may lose some or all of your invested capital. "
                "Only trade with money you can afford to lose.",
        "where": "Landing page footer, pricing page, all marketing materials",
        "rule": "FCA COBS 4.5.2R",
    },
    "not_financial_advice": {
        "text": "Hedge Edge is a trade management tool. It does not constitute financial advice. "
                "Please consult a qualified financial adviser before making trading decisions.",
        "where": "Landing page, Terms of Service, marketing emails",
        "rule": "FSMA 2000 s.19",
    },
    "past_performance": {
        "text": "Past performance is not indicative of future results. "
                "Hypothetical examples are for illustration only.",
        "where": "Any page showing ROI calculations, testimonials, or performance data",
        "rule": "FCA COBS 4.6.2R",
    },
    "ib_disclosure": {
        "text": "Hedge Edge may receive commission from partner brokers when you open an account "
                "through our referral links. This does not affect the service you receive.",
        "where": "Broker recommendation pages, IB links, pricing page",
        "rule": "FCA COBS 6.1B",
    },
    "prop_firm_disclaimer": {
        "text": "Hedge Edge is an independent tool. We are not affiliated with, endorsed by, "
                "or sponsored by any prop firm. Always check your prop firm's terms before hedging.",
        "where": "Landing page, product descriptions",
        "rule": "General fair trading",
    },
}


def scan_text(text: str) -> list[dict]:
    """Scan text for FCA financial promotions violations."""
    violations = []
    for check in PROHIBITED_PATTERNS:
        matches = list(re.finditer(check["pattern"], text, re.IGNORECASE))
        for match in matches:
            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].replace("\n", " ").strip()

            violations.append({
                "matched_text": match.group(),
                "context": f"...{context}...",
                "rule": check["rule"],
                "severity": check["severity"],
                "reason": check["reason"],
                "fix": check["fix"],
                "position": match.start(),
            })

    return sorted(violations, key=lambda v: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[v["severity"]])


def print_scan_results(violations: list, source: str):
    """Pretty-print scan results."""
    print("\n" + "=" * 70)
    print(f"  FCA FINANCIAL PROMOTIONS AUDIT")
    print(f"  Source: {source}")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    if not violations:
        print("\n  ✅ No violations detected.")
    else:
        severity_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"\n  ⚠️  {len(violations)} violation(s) found:\n")
        for i, v in enumerate(violations, 1):
            icon = severity_icons.get(v["severity"], "❓")
            print(f"  {icon} [{v['severity']}] Violation #{i}")
            print(f"     Matched: \"{v['matched_text']}\"")
            print(f"     Context: {v['context']}")
            print(f"     Rule:    {v['rule']}")
            print(f"     Reason:  {v['reason']}")
            print(f"     Fix:     {v['fix']}")
            print()

    print(f"{'─' * 70}")
    print("  REQUIRED DISCLAIMERS")
    print(f"{'─' * 70}")
    for key, disc in REQUIRED_DISCLAIMERS.items():
        print(f"\n  📋 {key.upper()}")
        print(f"     \"{disc['text']}\"")
        print(f"     Where: {disc['where']}")
        print(f"     Rule:  {disc['rule']}")

    print()


def main():
    parser = argparse.ArgumentParser(description="FCA Financial Promotions Auditor")
    parser.add_argument("--scan-text", "-t", help="Text to scan")
    parser.add_argument("--scan-file", "-f", help="File to scan")
    parser.add_argument("--generate-disclaimers", action="store_true", help="Output required disclaimers")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.generate_disclaimers:
        if args.json:
            print(json.dumps(REQUIRED_DISCLAIMERS, indent=2))
        else:
            print("\n  APPROVED DISCLAIMERS FOR HEDGE EDGE\n")
            for key, disc in REQUIRED_DISCLAIMERS.items():
                print(f"  [{key.upper()}]")
                print(f"  {disc['text']}\n")
        return

    text = ""
    source = ""

    if args.scan_text:
        text = args.scan_text
        source = "CLI input"
    elif args.scan_file:
        path = Path(args.scan_file)
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        source = str(path)
    else:
        parser.print_help()
        return

    violations = scan_text(text)

    if args.json:
        print(json.dumps({"source": source, "violations": violations}, indent=2))
    else:
        print_scan_results(violations, source)

    log_task(
        agent="Legal Compliance",
        task=f"FCA promotions audit: {source[:60]}",
        status="done",
        detail=f"{len(violations)} violations found",
    )


if __name__ == "__main__":
    main()
