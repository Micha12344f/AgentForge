# Growth Env Reference

Primary runtime file: `resources/.env`

| Key Group | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | CRM, campaign, onboarding, support scripts | campaign state, leads, tasks |
| `SUPABASE_*` | beta lead registration, attribution, onboarding | leads, auth, beta tables |
| `RESEND_API_KEY`, `UNSUBSCRIBE_SECRET` | email marketing and beta outreach scripts | sends, unsubscribe handling |
| `DISCORD_*` | Discord community/setup/support scripts | server ops, channels, roles, slash commands |
| `TWITTER_*` | `auto_tweet.py`, `Twitter_reply_system.py`, `x_manager.py`, `x_content_pipeline.py` | X posting and reply automation |
| `LINKEDIN_*` | `linkedin_manager.py` | LinkedIn publishing and OAuth |
| `INSTAGRAM_*` | `instagram_manager.py` | Instagram publishing |
| `SHORTIO_*` | `link_tracker.py`, `discord_setup.py` | short links and tracking |
| `CAL_*` | scheduling references and handoff flows | booking links / API integration |
| `GROQ_API_KEY` | `call_transcriber.py` | transcription and summaries |
| `VERCEL_TOKEN` | `deploy_landing_page.py` via shared Vercel client | landing page deploys |
| `GA4_PROPERTY_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON` | landing page and hourly metrics reporting | GA4 analytics |
| `CREEM_TEST_*`, `CREEM_BETA_PRODUCT_ID` | `seed_beta_key_pool.py` | beta checkout seeding |
