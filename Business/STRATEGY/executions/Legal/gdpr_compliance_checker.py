#!/usr/bin/env python3
"""
gdpr_compliance_checker.py — UK GDPR Compliance Audit Tool
===========================================================
Checks Hedge Edge's data processing activities against UK GDPR requirements.
Produces a compliance scorecard with action items.

Usage:
    python gdpr_compliance_checker.py --audit full
    python gdpr_compliance_checker.py --audit data-transfers
    python gdpr_compliance_checker.py --audit consent
    python gdpr_compliance_checker.py --audit dsar --email user@example.com
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent.parent
_RESOURCES_DIR = _SKILL_DIR / "resources"
sys.path.insert(0, str(_SKILL_DIR.parents[4].parent.parent.parent))

from shared.notion_client import log_task

_log = logging.getLogger("gdpr_checker")
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ── Hedge Edge Data Processing Map ───────────────────────────────────

DATA_PROCESSORS = {
    "supabase": {
        "name": "Supabase Inc.",
        "location": "United States",
        "data_types": ["email", "password_hash", "subscription_status", "usage_logs", "phone_number"],
        "purpose": "Authentication, user management, subscription tracking",
        "lawful_basis": "Contract performance (Art 6(1)(b))",
        "transfer_mechanism": "Standard Contractual Clauses (SCCs)",
        "dpa_signed": False,
        "retention": "Until account deletion + 30 days",
    },
    "vercel": {
        "name": "Vercel Inc.",
        "location": "United States",
        "data_types": ["ip_address", "browser_info", "page_views"],
        "purpose": "Landing page hosting and edge delivery",
        "lawful_basis": "Legitimate interest (Art 6(1)(f))",
        "transfer_mechanism": "Standard Contractual Clauses (SCCs)",
        "dpa_signed": False,
        "retention": "30 days (access logs)",
    },
    "creem": {
        "name": "Creem.io",
        "location": "United States",
        "data_types": ["email", "payment_method", "billing_address", "transaction_history"],
        "purpose": "Payment processing for subscriptions",
        "lawful_basis": "Contract performance (Art 6(1)(b))",
        "transfer_mechanism": "Standard Contractual Clauses (SCCs)",
        "dpa_signed": False,
        "retention": "As required by financial regulations (6 years)",
    },
    "resend": {
        "name": "Resend Inc.",
        "location": "United States",
        "data_types": ["email", "name", "email_open_events"],
        "purpose": "Transactional and marketing email delivery",
        "lawful_basis": "Contract + Consent (marketing)",
        "transfer_mechanism": "Standard Contractual Clauses (SCCs)",
        "dpa_signed": False,
        "retention": "Until unsubscribe + 30 days",
    },
    "discord": {
        "name": "Discord Inc.",
        "location": "United States",
        "data_types": ["discord_username", "messages", "support_logs"],
        "purpose": "Community management and support",
        "lawful_basis": "Legitimate interest (Art 6(1)(f))",
        "transfer_mechanism": "Discord's own DPA and SCCs",
        "dpa_signed": False,
        "retention": "Indefinite (community content)",
    },
}

# ── GDPR Compliance Checks ──────────────────────────────────────────

COMPLIANCE_CHECKS = {
    "ico_registration": {
        "description": "ICO (Information Commissioner's Office) registration",
        "requirement": "All UK organisations processing personal data must register with the ICO",
        "status": "NOT_DONE",
        "action": "Register at https://ico.org.uk/registration/ — annual fee £40-£2,900 depending on size",
        "severity": "HIGH",
    },
    "privacy_policy": {
        "description": "Privacy policy published on hedgeedge.info",
        "requirement": "Articles 13-14: Must inform data subjects about processing",
        "status": "EXISTS",
        "action": "Review privacy policy covers all processors and data types listed above",
        "severity": "HIGH",
    },
    "cookie_consent": {
        "description": "Cookie consent mechanism on landing page",
        "requirement": "PECR + UK GDPR: Prior consent for non-essential cookies",
        "status": "NOT_DONE",
        "action": "Implement cookie consent banner (analytics cookies require opt-in)",
        "severity": "MEDIUM",
    },
    "data_processing_agreements": {
        "description": "DPAs with all sub-processors",
        "requirement": "Article 28: Written contract with each processor",
        "status": "PARTIAL",
        "action": "Execute DPAs with Supabase, Vercel, Creem, and Resend",
        "severity": "HIGH",
    },
    "transfer_safeguards": {
        "description": "International transfer safeguards (UK-to-US)",
        "requirement": "Chapter V: Adequate safeguards for international transfers",
        "status": "PARTIAL",
        "action": "Verify SCCs in place with each US-based processor; document TIA",
        "severity": "HIGH",
    },
    "ropa": {
        "description": "Record of Processing Activities (ROPA)",
        "requirement": "Article 30: Maintain records of processing activities",
        "status": "NOT_DONE",
        "action": "Create and maintain ROPA — see resources/data-processing-register.md",
        "severity": "MEDIUM",
    },
    "dsar_process": {
        "description": "Data Subject Access Request (DSAR) process",
        "requirement": "Articles 15-22: Must respond within 30 days",
        "status": "PARTIAL",
        "action": "Formalize DSAR response workflow — see resources/dsar-process.md",
        "severity": "MEDIUM",
    },
    "breach_procedure": {
        "description": "Data breach notification procedure",
        "requirement": "Articles 33-34: Notify ICO within 72 hours",
        "status": "NOT_DONE",
        "action": "Document breach response plan with escalation contacts",
        "severity": "HIGH",
    },
    "data_minimisation": {
        "description": "Only collecting data necessary for the purpose",
        "requirement": "Article 5(1)(c): Data minimisation principle",
        "status": "OK",
        "action": "Review data collected at signup — currently email + password (minimal)",
        "severity": "LOW",
    },
    "right_to_erasure": {
        "description": "Account deletion removes all personal data",
        "requirement": "Article 17: Right to erasure ('right to be forgotten')",
        "status": "EXISTS",
        "action": "Verify supabase-delete-account.sql purges all PII from all tables",
        "severity": "MEDIUM",
    },
}


def run_audit(audit_type: str = "full") -> dict:
    """Run a GDPR compliance audit and return structured results."""
    results = {
        "audit_type": audit_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company": "Hedge Edge Ltd",
        "jurisdiction": "UK (England & Wales)",
        "checks": {},
        "processors": {},
        "score": 0,
        "max_score": 0,
        "grade": "",
        "critical_actions": [],
    }

    # Filter checks by audit type
    if audit_type == "full":
        checks = COMPLIANCE_CHECKS
    elif audit_type == "data-transfers":
        checks = {k: v for k, v in COMPLIANCE_CHECKS.items()
                  if "transfer" in k or "dpa" in k or "processing" in k}
    elif audit_type == "consent":
        checks = {k: v for k, v in COMPLIANCE_CHECKS.items()
                  if "consent" in k or "privacy" in k or "cookie" in k}
    else:
        checks = COMPLIANCE_CHECKS

    # Score each check
    score_map = {"OK": 10, "EXISTS": 7, "PARTIAL": 4, "NOT_DONE": 0}
    total_score = 0
    max_score = len(checks) * 10

    for check_id, check in checks.items():
        score = score_map.get(check["status"], 0)
        total_score += score
        results["checks"][check_id] = {
            **check,
            "score": score,
        }
        if check["status"] in ("NOT_DONE", "PARTIAL") and check["severity"] in ("HIGH", "CRITICAL"):
            results["critical_actions"].append({
                "check": check_id,
                "action": check["action"],
                "severity": check["severity"],
            })

    results["score"] = total_score
    results["max_score"] = max_score
    pct = (total_score / max_score * 100) if max_score > 0 else 0

    if pct >= 80:
        results["grade"] = "A — Compliant"
    elif pct >= 60:
        results["grade"] = "B — Mostly Compliant"
    elif pct >= 40:
        results["grade"] = "C — Partially Compliant"
    else:
        results["grade"] = "D — Non-Compliant (urgent action needed)"

    results["processors"] = DATA_PROCESSORS
    return results


def print_audit(results: dict):
    """Pretty-print audit results."""
    print("\n" + "=" * 70)
    print(f"  UK GDPR COMPLIANCE AUDIT — {results['company']}")
    print(f"  {results['timestamp']}")
    print("=" * 70)

    score = results["score"]
    max_score = results["max_score"]
    pct = (score / max_score * 100) if max_score > 0 else 0
    print(f"\n  SCORE: {score}/{max_score} ({pct:.0f}%) — {results['grade']}")

    print(f"\n{'─' * 70}")
    print("  COMPLIANCE CHECKS")
    print(f"{'─' * 70}")

    status_icons = {"OK": "✅", "EXISTS": "🟡", "PARTIAL": "⚠️", "NOT_DONE": "❌"}
    for check_id, check in results["checks"].items():
        icon = status_icons.get(check["status"], "❓")
        print(f"\n  {icon} {check['description']}")
        print(f"     Status: {check['status']} | Severity: {check['severity']}")
        if check["status"] != "OK":
            print(f"     Action: {check['action']}")

    if results["critical_actions"]:
        print(f"\n{'─' * 70}")
        print("  🚨 CRITICAL ACTIONS REQUIRED")
        print(f"{'─' * 70}")
        for i, action in enumerate(results["critical_actions"], 1):
            print(f"\n  {i}. [{action['severity']}] {action['action']}")

    print(f"\n{'─' * 70}")
    print(f"  DATA PROCESSORS ({len(results['processors'])})")
    print(f"{'─' * 70}")
    for proc_id, proc in results["processors"].items():
        dpa_icon = "✅" if proc["dpa_signed"] else "❌"
        print(f"\n  {proc['name']} ({proc['location']})")
        print(f"     Purpose: {proc['purpose']}")
        print(f"     Data: {', '.join(proc['data_types'])}")
        print(f"     Lawful basis: {proc['lawful_basis']}")
        print(f"     DPA signed: {dpa_icon}")

    print()


def main():
    parser = argparse.ArgumentParser(description="UK GDPR Compliance Checker")
    parser.add_argument("--audit", default="full",
                        choices=["full", "data-transfers", "consent", "dsar"])
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = run_audit(args.audit)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_audit(results)

    log_task(
        agent="Legal Compliance",
        task=f"GDPR audit ({args.audit})",
        status="done",
        detail=f"Score: {results['score']}/{results['max_score']}, Grade: {results['grade']}",
    )


if __name__ == "__main__":
    main()
