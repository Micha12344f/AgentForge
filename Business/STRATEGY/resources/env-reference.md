# Strategy Env Reference

Primary runtime file: `resources/.env`

| Key Group | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | research scripts and product docs | strategic notes and logs |
| `SUPABASE_*` | product/bug/release strategy work and product backend resource files | backend analytics and feature flags |
| `GITHUB_TOKEN` | roadmap, release, app deploy flows | issue/release automation |
| `DISCORD_BOT_TOKEN` | product directives that post updates | team and customer comms |
| `VERCEL_TOKEN` | release/product directives | landing page deployment checks |
| `GROQ_API_KEY` | `deep_researcher.py`, `competitor_intel.py`, `swot_analyzer.py`, `investor_wisdom.py` via shared LLM router | strategic generation |
| `OPENROUTER_API_KEY`, `GOOGLE_AI_KEY`, `GEMINI_API_KEY` | optional shared LLM fallbacks | fallback model routing |
| `CREEM_*` | product license backend resource files | payment/license validation |
| runtime keys like `ENVIRONMENT`, `RATE_LIMIT`, `PORT`, `HOST` | product backend resource docs/examples | deployment template values |
