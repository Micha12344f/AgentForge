# Sales Env Reference

Primary runtime override file: `Business/GROWTH/resources/.env`

Sales-specific example keys live in `Business/GROWTH/resources/Sales/.env.example`.

| Key Group | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | onboarding and CRM scripts | beta waitlist, demo log, task logs |
| `SUPABASE_*` | onboarding and lead lifecycle workflows | lead state, beta activation data |
| `CAL_*` | scheduling references and handoff flows | booking links and API integration |
| `GROQ_API_KEY` | `call_transcriber.py` | transcription and summaries |
| `CREEM_TEST_*`, `CREEM_BETA_PRODUCT_ID` | proposal and checkout-adjacent flows | payment and beta checkout references |