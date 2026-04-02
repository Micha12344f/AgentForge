# Marketing Env Reference

Primary runtime override file: `Business/GROWTH/resources/.env`

Marketing-specific example keys live in `Business/GROWTH/resources/Marketing/.env.example`.

| Key Group | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | campaign, email, support, and reporting scripts | campaign state, lead records, task logs |
| `SUPABASE_*` | beta lead registration, attribution, onboarding | leads, auth, beta tables |
| `RESEND_API_KEY`, `UNSUBSCRIBE_SECRET` | email marketing and beta outreach scripts | sends, unsubscribe handling |
| `DISCORD_*` | Discord community/setup/support scripts | server ops, channels, roles, slash commands |
| `TWITTER_*` | `auto_tweet.py`, `Twitter_reply_system.py`, `x_manager.py`, `x_content_pipeline.py` | X posting and reply automation |
| `IMGFLIP_USERNAME`, `IMGFLIP_PASSWORD` | `auto_tweet.py` via `shared.meme_maker` | caption TOFU meme templates before posting |
| `PEXELS_API_KEY` | `auto_tweet.py` via `shared.image_finder` | fallback atmospheric imagery for MOFU posts |
| `LINKEDIN_*` | `linkedin_manager.py` | LinkedIn publishing and OAuth |
| `INSTAGRAM_*` | `instagram_manager.py` | Instagram publishing |
| `SHORTIO_*` | `link_tracker.py`, `discord_setup.py` | short links and tracking |
| `VERCEL_TOKEN` | `deploy_landing_page.py` | landing page deploys |
| `GA4_PROPERTY_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON` | landing page and hourly metrics reporting | GA4 analytics |
| `CREEM_TEST_*`, `CREEM_BETA_PRODUCT_ID` | `seed_beta_key_pool.py` | beta checkout seeding |