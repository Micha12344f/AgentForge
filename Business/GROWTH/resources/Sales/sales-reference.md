# Sales Resources

> Reference material for the Growth Sales sub-department.

## Sales Stack

| Tool | Purpose | Integration |
|------|---------|------------|
| Notion | CRM, beta waitlist, demo log | `shared/notion_client.py` |
| Supabase | Lead and activation data | `shared/supabase_client.py` |
| Cal.com | Demo scheduling | scheduling and handoff flows |
| Groq | Call transcription and summaries | `shared/groq_client.py` |
| Creem.io | Checkout and payment flows | `shared/creem_client.py` |

## Key Notion Databases

| DB Key | Purpose |
|--------|---------|
| `crm_pipeline` | Deal stages and pipeline visibility |
| `beta_waitlist` | Beta tester onboarding and watchlist management |
| `demo_log` | Demo call tracking, transcripts, and summaries |