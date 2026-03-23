# FINANCE — Skill Command Sheet

> **Adopt this department to gain**: Revenue tracking, IB commission reconciliation, expense management, financial reporting, and invoicing skills for all Hedge Edge money flows.

---

## Skills You Gain

When you adopt the Finance department, you can execute the following skills by combining directives (what to do), executions (how to do it), and resources (reference material).

### Skill 1 — IB Commission Tracking
- **Directive**: `directives/ib-commission-tracking.md` — monitor, reconcile, and forecast IB commissions from Vantage Markets and BlackBull Markets
- **Executions**: `executions/scrape_vantage_ib.py` (scrape Vantage portal), `executions/scrape_blackbull_ib.py` (scrape BlackBull portal), `executions/ib_report_aggregator.py` (aggregate and reconcile across brokers)
- **Resource**: `resources/finance-reference.md`

### Skill 2 — SaaS Revenue & MRR Tracking
- **Directive**: `directives/revenue-tracking.md` — MRR waterfall, subscription lifecycle, Creem.io integration
- **Executions**: `executions/revenue_tracker.py` (pull Creem.io data, calculate MRR), `executions/subscription_analyzer.py` (churn, expansion, contraction analysis)

### Skill 3 — Expense Management
- **Directive**: `directives/expense-management.md` — categorise and track business expenses
- **Execution**: `executions/expense_manager.py` — expense categorisation, anomaly flagging

### Skill 4 — Financial Reporting
- **Directive**: `directives/financial-reporting.md` — P&L, cash flow, runway calculations
- **Execution**: `executions/financial_reporter.py` — generate P&L and cash flow statements

### Skill 5 — Invoicing
- **Directive**: `directives/invoicing.md` — invoice generation for IB commission payouts
- **Execution**: `executions/invoice_generator.py` — create invoices for broker payouts

---

## Revenue Streams

**Stream 1 — SaaS Subscriptions (Creem.io)**: User signup -> Supabase auth -> Creem.io checkout -> revenue_tracker.py -> Notion mrr_tracker

**Stream 2 — IB Commissions (Vantage + BlackBull)**: Referred trader trades -> broker accrues commission -> scrape scripts pull data -> ib_report_aggregator.py reconciles -> invoice_generator.py creates payout

---

## Dispatcher

`executions/run.py` routes `--task` flags to execution scripts. Entry point for all Finance tasks.

## Shared Dependencies

Imports from workspace-root `shared/`: `notion_client.py`, `supabase_client.py`, `alerting.py`, `llm_router.py`.

## Cross-Department Links

| Department | Finance Provides | Finance Needs |
|------------|-----------------|---------------|
| STRATEGY | MRR + commission data for growth models | IB agreement terms |
| ANALYTICS | Subscriber counts for MRR validation | Revenue events |
| ORCHESTRATOR | Revenue alerts | Cron scheduling |
| GROWTH | Commission data for partnerships | Conversion data |
