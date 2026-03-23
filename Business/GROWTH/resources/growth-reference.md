# Growth Resources

> Reference material for the Growth department (Marketing + Sales).

## Marketing Stack

| Tool | Purpose | Integration |
|------|---------|------------|
| Resend | Email delivery | `shared/resend_client.py` |
| Notion | Campaign management | `shared/notion_client.py` |
| Short.io | Link tracking | `shared/shortio_client.py` |
| GA4 | Web analytics | `shared/google_analytics_client.py` |
| LinkedIn | Social outreach | `shared/linkedin_client.py` |
| Twitter/X | Social content | Twitter reply system |
| Discord | Community | `shared/discord_client.py` |

## Sales Stack

| Tool | Purpose | Integration |
|------|---------|------------|
| Cal.com | Demo scheduling | `shared/calcom_client.py` |
| Creem.io | Checkout/payments | `shared/creem_client.py` |
| Groq | Call transcription | `shared/groq_client.py` |
| Supabase | CRM data | `shared/supabase_client.py` |

## Key Notion Databases

| DB Key | Department | Purpose |
|--------|-----------|---------|
| `campaigns` | Marketing | Campaign management |
| `email_sequences` | Marketing | Drip sequence templates |
| `email_sends` | Marketing | Per-lead send records |
| `crm_pipeline` | Sales | Deal stages and pipeline |
