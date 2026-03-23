#!/usr/bin/env python3
"""
ticket_manager.py — Community Manager Agent Support Triage

Create, resolve, and report on support tickets from community channels.

Usage:
    python ticket_manager.py --action create-ticket --title "Can't connect MetaTrader to Hedge Edge" --channel Discord --priority P1
    python ticket_manager.py --action resolve-ticket --title "Can't connect..." --resolution "Updated MT5 bridge docs"
    python ticket_manager.py --action ticket-report
    python ticket_manager.py --action overdue --days 3
"""

import sys, os, argparse
from datetime import datetime, timedelta

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if os.path.isfile(os.path.join(d, "shared", "notion_client.py")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

from shared.notion_client import add_row, query_db, update_row, log_task

# ── Support bot import (for auto-resolve via FAQ deflection) ──
try:
    from shared.support_bot import answer as support_answer
    from shared.notebooklm_client import budget_remaining
    _BOT_AVAILABLE = True
except ImportError:
    _BOT_AVAILABLE = False


def create_ticket(args):
    row = {
        "Ticket":     args.title,
        "Status":     "Open",
        "Priority":   args.priority or "P2",
        "Channel":    args.channel or "Discord",
        "Created":    datetime.now().strftime("%Y-%m-%d"),
        "User":       args.user or "",
        "Category":   args.category or "Support",
        "Resolution": "",
    }
    add_row("support_tickets", row)
    print(f"🎫 Ticket created: {args.title}")
    print(f"   Priority: {row['Priority']} | Channel: {row['Channel']}")
    log_task("Community", f"Ticket: {args.title}", "Complete", "P1")


def resolve_ticket(args):
    items = query_db("support_tickets", filter={
        "property": "Ticket", "title": {"equals": args.title}
    })
    if not items:
        print(f"❌ Ticket not found: {args.title}"); return
    item = items[0]
    updates = {
        "Status":     "Resolved",
        "Resolution": args.resolution or "Resolved",
        "Resolved":   datetime.now().strftime("%Y-%m-%d"),
    }
    update_row(item["_id"], "support_tickets", updates)
    print(f"✅ Resolved: {args.title}")
    if args.resolution: print(f"   Resolution: {args.resolution}")
    # Calculate resolution time
    created = item.get("Created", "")
    if created:
        try:
            days = (datetime.now() - datetime.strptime(created, "%Y-%m-%d")).days
            print(f"   Resolution time: {days} day(s)")
        except: pass
    log_task("Community", f"Resolved: {args.title}", "Complete", "P2")


def ticket_report(args):
    items = query_db("support_tickets")
    print("=" * 65)
    print("  🎫 SUPPORT TICKET REPORT")
    print("=" * 65)
    if not items:
        print("\n  No tickets."); return

    open_tickets  = [t for t in items if t.get("Status") != "Resolved"]
    resolved      = [t for t in items if t.get("Status") == "Resolved"]

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    open_tickets.sort(key=lambda x: priority_order.get(x.get("Priority", "P2"), 9))

    if open_tickets:
        print(f"\n  OPEN ({len(open_tickets)})")
        for t in open_tickets:
            icon = "🔴" if t.get("Priority") in ("P0", "P1") else "🟡"
            print(f"    {icon} [{t.get('Priority', '?')}] {t.get('Ticket', '?')}")
            print(f"       Channel: {t.get('Channel', '?')} | Created: {t.get('Created', '?')}")

    if resolved:
        print(f"\n  RECENTLY RESOLVED ({len(resolved)})")
        resolved.sort(key=lambda x: x.get("Resolved", ""), reverse=True)
        for t in resolved[:5]:
            print(f"    ✅ {t.get('Ticket', '?')} — {t.get('Resolved', '?')}")
        if len(resolved) > 5:
            print(f"    ... and {len(resolved) - 5} more")

    print(f"\n{'─' * 65}")
    critical = sum(1 for t in open_tickets if t.get("Priority") in ("P0", "P1"))
    print(f"  Total: {len(items)} | Open: {len(open_tickets)} | Critical: {critical} | Resolved: {len(resolved)}")
    log_task("Community", "Ticket report", "Complete", "P3",
             f"{len(open_tickets)} open, {critical} critical")


def overdue(args):
    """Show tickets open longer than N days."""
    cutoff = (datetime.now() - timedelta(days=args.days or 3)).strftime("%Y-%m-%d")
    items = query_db("support_tickets", filter={
        "and": [
            {"property": "Status", "select": {"does_not_equal": "Resolved"}},
            {"property": "Created", "date": {"on_or_before": cutoff}},
        ]
    })
    print("=" * 65)
    print(f"  ⏰ OVERDUE TICKETS (>{args.days or 3} days)")
    print("=" * 65)
    if not items:
        print(f"\n  No tickets overdue beyond {args.days or 3} days. 🎉"); return

    for t in items:
        try:
            age = (datetime.now() - datetime.strptime(t.get("Created", ""), "%Y-%m-%d")).days
        except:
            age = "?"
        print(f"\n  🔴 [{t.get('Priority', '?')}] {t.get('Ticket', '?')}")
        print(f"     Age: {age} days | Channel: {t.get('Channel', '?')}")

    print(f"\n{'─' * 65}")
    print(f"  {len(items)} overdue ticket(s)")
    log_task("Community", "Overdue check", "Complete", "P2",
             f"{len(items)} overdue tickets")


def try_bot(args):
    """Run a question through the Support Bot before creating a ticket."""
    question = args.title or "How do I install the Hedge Edge EA?"
    if not _BOT_AVAILABLE:
        print("❌ Support Bot not available (shared.support_bot import failed)")
        print("   Falling back to manual ticket creation...")
        return
    remaining = budget_remaining()
    print(f"🤖 Running question through Support Bot ({remaining} queries left today)...")
    print(f"   Question: {question}\n")
    response = support_answer(question)
    if "I don't have specific information" in response:
        print("⚠️  Bot couldn't answer — creating ticket for human triage.\n")
        print(f"   Bot said: {response[:200]}")
        args.category = "Bot-Escalation"
        create_ticket(args)
    else:
        print("✅ Bot resolved the question automatically:\n")
        print(response)
        log_task("Community", f"Bot auto-resolved: {question[:60]}", "Complete", "P3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Support Ticket Management")
    parser.add_argument("--action", required=True,
                        choices=["create-ticket", "resolve-ticket", "ticket-report", "overdue", "try-bot"])
    parser.add_argument("--title")
    parser.add_argument("--priority", default="P2")
    parser.add_argument("--channel", default="Discord")
    parser.add_argument("--status")
    parser.add_argument("--resolution", default="")
    parser.add_argument("--user", default="")
    parser.add_argument("--category", default="Support")
    parser.add_argument("--days", type=int, default=3)
    args = parser.parse_args()
    {"create-ticket": create_ticket, "resolve-ticket": resolve_ticket,
     "ticket-report": ticket_report, "overdue": overdue, "try-bot": try_bot}[args.action](args)
