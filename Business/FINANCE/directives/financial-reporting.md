# Financial Reporting

> P&L, cash flow, and runway calculations.

## Reports

| Report | Frequency | Audience |
|--------|-----------|----------|
| P&L Statement | Monthly | Board, Strategy |
| Cash Flow | Monthly | Board, Strategy |
| Runway Projection | Monthly | Board |
| MRR Waterfall | Weekly | Growth, Strategy |
| IB Commission Summary | Monthly | Strategy |

## P&L Structure

```
Revenue
  + SaaS Subscriptions (Creem.io MRR × period)
  + IB Commissions (Vantage + BlackBull)
  = Total Revenue

Expenses
  - Infrastructure (Railway, Vercel, Supabase, Cloudflare)
  - SaaS Tools (Notion, Resend, API credits)
  - Marketing (ad spend, content tools)
  - Legal & Compliance
  = Total Expenses

Net Income = Total Revenue − Total Expenses
```

## Runway Calculation

```
Runway (months) = Cash Balance / Monthly Burn Rate
Monthly Burn Rate = Average(last 3 months Total Expenses) − Average(last 3 months Total Revenue)
```
