#!/usr/bin/env python3
"""
expense_manager.py — Finance Agent Expense Management

Track and manage business expenses, budgets, and spending analysis
for Hedge Edge Ltd.

Usage:
    python expense_manager.py --action add-expense --category hosting --amount 49.99 --description "Railway Pro plan" --vendor Railway --recurring
    python expense_manager.py --action monthly-summary
    python expense_manager.py --action budget-check
    python expense_manager.py --action recurring-expenses
    python expense_manager.py --action cost-trend
"""

import sys, os, argparse, json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.notion_client import add_row, query_db, update_row, log_task

AGENT = "Finance"

VALID_CATEGORIES = ["hosting", "marketing", "software", "legal", "travel", "contractor", "other"]

MONTHLY_BUDGETS = {
    "hosting":    200.0,
    "marketing":  500.0,
    "software":   300.0,
    "legal":      100.0,
    "travel":       0.0,
    "contractor": 1000.0,
    "other":      200.0,
}

CATEGORY_ICONS = {
    "hosting": "🖥️", "marketing": "📣", "software": "💿",
    "legal": "⚖️", "travel": "✈️", "contractor": "🔧", "other": "📦",
}


def _current_month_str():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _parse_amount(row):
    val = row.get("Amount") or row.get("Value") or 0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _parse_date(row):
    d = row.get("Date", "") or ""
    try:
        return datetime.fromisoformat(d.replace("Z", "+00:00"))
    except Exception:
        return None


def add_expense(args):
    """Record a new business expense to the expense_log Notion DB."""
    now = datetime.now(timezone.utc)
    row = {
        "Name": args.description or f"{args.category} expense",
        "Category": args.category.capitalize(),
        "Amount": args.amount,
        "Vendor": args.vendor or "",
        "Recurring": args.recurring,
        "Date": now.strftime("%Y-%m-%d"),
        "Status": "Paid",
        "Notes": f"Recorded via Finance Agent on {now.strftime('%Y-%m-%d %H:%M')} UTC",
    }
    add_row("expense_log", row)

    icon = CATEGORY_ICONS.get(args.category, "📦")
    print("=" * 60)
    print(f"  {icon} EXPENSE RECORDED")
    print("=" * 60)
    print(f"\n  Category:    {args.category.capitalize()}")
    print(f"  Amount:      £{args.amount:,.2f}")
    print(f"  Description: {args.description}")
    print(f"  Vendor:      {args.vendor or '—'}")
    print(f"  Recurring:   {'Yes' if args.recurring else 'No'}")
    print(f"  Date:        {now.strftime('%Y-%m-%d')}")

    budget = MONTHLY_BUDGETS.get(args.category, 0)
    if budget > 0:
        print(f"\n  Monthly Budget ({args.category}): £{budget:,.2f}")
        print(f"  This charge: £{args.amount:,.2f} ({args.amount / budget * 100:.1f}% of budget)")
    print("─" * 60)

    log_task(AGENT, f"Recorded expense: {args.description} (£{args.amount:.2f})",
             "Complete", "P2",
             f"category={args.category}, vendor={args.vendor}, recurring={args.recurring}")


def monthly_summary(args):
    """Show expenses grouped by category for the current month."""
    rows = query_db("expense_log")
    month = _current_month_str()
    monthly = [r for r in rows if (r.get("Date", "") or "").startswith(month)]

    by_cat = defaultdict(list)
    for r in monthly:
        cat = (r.get("Category", "") or "other").lower()
        by_cat[cat].append(r)

    grand_total = 0.0
    print("=" * 60)
    print(f"  💰 MONTHLY EXPENSE SUMMARY — {month}")
    print("=" * 60)
    print(f"\n  {'Category':<14} {'Count':>6} {'Total':>12} {'Avg':>10}")
    print(f"  {'─' * 46}")

    for cat in VALID_CATEGORIES:
        items = by_cat.get(cat, [])
        total = sum(_parse_amount(r) for r in items)
        grand_total += total
        avg = total / len(items) if items else 0
        icon = CATEGORY_ICONS.get(cat, "📦")
        print(f"  {icon} {cat:<11} {len(items):>6} £{total:>10,.2f} £{avg:>8,.2f}")

    print(f"  {'─' * 46}")
    print(f"  {'TOTAL':<14} {len(monthly):>6} £{grand_total:>10,.2f}")
    total_budget = sum(MONTHLY_BUDGETS.values())
    pct = (grand_total / total_budget * 100) if total_budget > 0 else 0
    print(f"\n  Total Budget: £{total_budget:,.2f}  |  Utilised: {pct:.1f}%")
    print("─" * 60)

    log_task(AGENT, f"Monthly expense summary for {month}",
             "Complete", "P3",
             f"total=£{grand_total:,.2f}, {len(monthly)} expenses, {pct:.1f}% of budget")


def budget_check(args):
    """Compare actual spend vs budget and flag overages."""
    rows = query_db("expense_log")
    month = _current_month_str()
    monthly = [r for r in rows if (r.get("Date", "") or "").startswith(month)]

    by_cat = defaultdict(float)
    for r in monthly:
        cat = (r.get("Category", "") or "other").lower()
        by_cat[cat] += _parse_amount(r)

    print("=" * 60)
    print(f"  📊 BUDGET CHECK — {month}")
    print("=" * 60)
    print(f"\n  {'Category':<14} {'Budget':>10} {'Actual':>10} {'Remaining':>10} {'Status':>8}")
    print(f"  {'─' * 56}")

    overages = []
    for cat in VALID_CATEGORIES:
        budget = MONTHLY_BUDGETS[cat]
        actual = by_cat.get(cat, 0.0)
        remaining = budget - actual
        pct = (actual / budget * 100) if budget > 0 else (100 if actual > 0 else 0)

        if pct > 100:
            status = "🔴 OVER"
            overages.append((cat, actual, budget, actual - budget))
        elif pct > 80:
            status = "🟡 WARN"
        else:
            status = "🟢 OK"

        print(f"  {cat:<14} £{budget:>8,.2f} £{actual:>8,.2f} £{remaining:>8,.2f} {status}")

    total_budget = sum(MONTHLY_BUDGETS.values())
    total_actual = sum(by_cat.values())

    print(f"  {'─' * 56}")
    print(f"  {'TOTAL':<14} £{total_budget:>8,.2f} £{total_actual:>8,.2f} £{total_budget - total_actual:>8,.2f}")

    if overages:
        print(f"\n  🚨 BUDGET OVERAGES:")
        for cat, actual, budget, over in overages:
            print(f"     {cat}: £{over:,.2f} over budget ({actual / budget * 100:.0f}%)")
    else:
        print(f"\n  ✅ All categories within budget")
    print("─" * 60)

    log_task(AGENT, f"Budget check for {month}",
             "Complete", "P2",
             f"total_spend=£{total_actual:,.2f}/{total_budget:,.2f}, overages={len(overages)}")


def recurring_expenses(args):
    """List all recurring expenses with monthly total."""
    rows = query_db("expense_log")
    recurring = [r for r in rows if r.get("Recurring")]

    seen = {}
    for r in recurring:
        key = f"{(r.get('Vendor') or '').lower()}:{(r.get('Category') or '').lower()}"
        amt = _parse_amount(r)
        if key not in seen or amt > _parse_amount(seen[key]):
            seen[key] = r

    deduped = list(seen.values())
    monthly_total = sum(_parse_amount(r) for r in deduped)

    print("=" * 60)
    print("  🔄 RECURRING EXPENSES")
    print("=" * 60)
    print(f"\n  {'Vendor':<18} {'Category':<12} {'Amount':>10} {'Description'}")
    print(f"  {'─' * 58}")

    for r in sorted(deduped, key=lambda x: _parse_amount(x), reverse=True):
        vendor = (r.get("Vendor") or "—")[:17]
        cat = (r.get("Category") or "—")[:11]
        amt = _parse_amount(r)
        desc = (r.get("Name") or "—")[:30]
        print(f"  {vendor:<18} {cat:<12} £{amt:>8,.2f}  {desc}")

    print(f"  {'─' * 58}")
    print(f"  Monthly Recurring Total: £{monthly_total:,.2f}")
    print(f"  Annual Projected:        £{monthly_total * 12:,.2f}")
    print("─" * 60)

    log_task(AGENT, "Listed recurring expenses",
             "Complete", "P3",
             f"count={len(deduped)}, monthly=£{monthly_total:,.2f}")


def cost_trend(args):
    """Show expense trend over last 6 months with increase/decrease flags."""
    rows = query_db("expense_log")
    now = datetime.now(timezone.utc)

    months = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30 * i)
        months.append(d.strftime("%Y-%m"))

    by_month_cat = defaultdict(lambda: defaultdict(float))
    for r in rows:
        date_str = (r.get("Date", "") or "")[:7]
        if date_str in months:
            cat = (r.get("Category", "") or "other").lower()
            by_month_cat[date_str][cat] += _parse_amount(r)

    print("=" * 60)
    print("  📈 EXPENSE TREND — LAST 6 MONTHS")
    print("=" * 60)

    # Monthly totals
    month_totals = {m: sum(by_month_cat[m].values()) for m in months}
    print(f"\n  {'Month':<10}", end="")
    for cat in VALID_CATEGORIES[:5]:  # top 5 categories fit on screen
        print(f"  {cat[:8]:>8}", end="")
    print(f"  {'TOTAL':>10}")
    print(f"  {'─' * 62}")

    prev_total = None
    for m in months:
        print(f"  {m:<10}", end="")
        for cat in VALID_CATEGORIES[:5]:
            val = by_month_cat[m].get(cat, 0)
            print(f"  £{val:>6,.0f}", end="")
        total = month_totals[m]
        trend = ""
        if prev_total is not None and prev_total > 0:
            change = ((total - prev_total) / prev_total) * 100
            trend = f" ▲{change:+.0f}%" if change > 0 else f" ▼{change:+.0f}%"
        print(f"  £{total:>8,.2f}{trend}")
        prev_total = total

    # Category trends
    print(f"\n  Category Change (first → last month):")
    for cat in VALID_CATEGORIES:
        first = by_month_cat[months[0]].get(cat, 0)
        last = by_month_cat[months[-1]].get(cat, 0)
        if first > 0:
            chg = ((last - first) / first) * 100
            icon = "🔺" if chg > 10 else ("🔻" if chg < -10 else "➡️")
            print(f"    {icon} {cat:<12} £{first:,.0f} → £{last:,.0f} ({chg:+.1f}%)")
        elif last > 0:
            print(f"    🆕 {cat:<12} £0 → £{last:,.0f} (new)")
    print("─" * 60)

    log_task(AGENT, "Generated 6-month expense trend",
             "Complete", "P3",
             f"months={months[0]}..{months[-1]}, latest=£{month_totals.get(months[-1], 0):,.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Expense Manager — Finance Agent")
    p.add_argument("--action", required=True,
                   choices=["add-expense", "monthly-summary", "budget-check",
                            "recurring-expenses", "cost-trend"])
    p.add_argument("--category", choices=VALID_CATEGORIES, help="Expense category")
    p.add_argument("--amount", type=float, help="Expense amount in GBP")
    p.add_argument("--description", help="Expense description")
    p.add_argument("--vendor", help="Vendor / supplier name")
    p.add_argument("--recurring", action="store_true", help="Mark as recurring expense")

    args = p.parse_args()
    actions = {
        "add-expense": add_expense,
        "monthly-summary": monthly_summary,
        "budget-check": budget_check,
        "recurring-expenses": recurring_expenses,
        "cost-trend": cost_trend,
    }
    actions[args.action](args)
