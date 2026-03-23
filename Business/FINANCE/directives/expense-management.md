# Expense Management

> Categorise and track all business expenses.

## Expense Categories

| Category | Examples |
|----------|---------|
| Infrastructure | Railway, Vercel, Supabase, Cloudflare |
| SaaS Tools | Notion, Resend, Short.io, Cal.com |
| Marketing | Ad spend, content creation tools |
| Development | GitHub, API credits (OpenAI, Groq, Gemini) |
| Legal | Company formation, compliance consulting |
| Operations | Domain renewals, SSL certificates |

## Tracking Rules

- All expenses logged with date, amount, category, vendor, description
- Monthly reconciliation against bank (Tide) transactions
- Anomaly detection: flag expenses >2× monthly average for category
