# GROWTH — Skill Command Sheet

> **Adopt this department to gain**: Customer acquisition, email marketing, social media management, content creation, community building, lead qualification, CRM management, and sales pipeline skills.

> **Governance note**: Growth owns growth content. Orchestrator alone owns cross-department DOE restructuring and any `SKILL.md` rewrite that changes folder-role mapping or explains what folders now do.

---

## Skills You Gain

GROWTH houses two sub-departments — **Marketing** (awareness to lead) and **Sales** (lead to customer). Directives, executions, and human-facing resources are organised under matching `Marketing/` and `Sales/` subfolders.

`resources/.env` remains at the department resource root as the shared runtime override file for all Growth workflows.

---

### MARKETING SKILLS

#### Skill 1 — Email Marketing Engine
- **Directive**: `directives/Marketing/email-marketing.md` — campaign lifecycle, drip sequences, send rules
- **Executions**: `executions/Marketing/email_marketing/email_system.py` (full-cycle orchestration), `executions/Marketing/email_marketing/email_sequence_manager.py` (sequence building), `executions/Marketing/email_marketing/Email_send.py` (Railway send wrapper), `executions/Marketing/email_marketing/email_send_sanity.py` (read-only checks), `executions/Marketing/email_marketing/config.py` (shared constants)
- **Supporting**: `executions/Marketing/send_license_email.py` (license delivery), `executions/Marketing/resend_beta_key_webhook.py` (beta key webhook), `executions/Marketing/import_email_logs.py` (log import), `executions/Marketing/test_email_marketing_e2e.py` (E2E test)

#### Skill 2 — Beta Key & Lead Registration
- **Directive**: `directives/Marketing/beta-lead-registration.md` — beta waitlist flow, key provisioning
- **Executions**: `executions/Marketing/beta_lead_register.py` (register leads), `executions/Marketing/seed_beta_key_pool.py` (seed key pool), `executions/Marketing/revoke_expired_claims.py` (key cleanup), `executions/Marketing/check_new_beta_users.py` (monitor signups), `executions/Marketing/check_supabase_beta.py` (check Supabase), `executions/Marketing/check_today_signup.py` (today's signups), `executions/Marketing/fetch_beta_sequences.py` (sequence status), `executions/Marketing/check_beta_campaign_sequences.py` (campaign check)

#### Skill 3 — Attribution & Link Tracking
- **Directive**: `directives/Marketing/attribution-tracking.md` — UTM attribution, referrer normalisation
- **Executions**: `executions/Marketing/attribution_tracker.py`, `executions/Marketing/link_tracker.py` (Short.io UTM links), `executions/Marketing/campaign_tracker.py` (campaign performance)
- **Resource**: `resources/Marketing/Attribution_Tracking_Pipeline.ipynb`

#### Skill 4 — Landing Page Optimisation
- **Directive**: `directives/Marketing/landing-page-optimization.md` — CRO, A/B testing
- **Executions**: `executions/Marketing/landing_page_optimizer.py`, `executions/Marketing/deploy_landing_page.py`

#### Skill 5 — Social Media (Twitter/X)
- **Directive**: `directives/Marketing/x-management.md` — posting workflow, safety rules, channel strategy for X, and full file-location reference
- **Executions**: `executions/Marketing/auto_tweet.py` (automated TOFU/MOFU posting pipeline), `executions/Marketing/Twitter_reply_system.py` (reply bot), `executions/Marketing/tw_search_reply.py` (search-based replies), `executions/Marketing/x_content_pipeline.py` (content pipeline workspace — run cells to review library state, runway, and next tweet), `executions/Marketing/x_manager.py` (validated thread and single-post publisher)
- **Content library**: `resources/Marketing/x-pipeline/tweet_demos_100.json` — 55 ready-to-post demos (TOFU: funny_meme, gif_meme, viral_hook; MOFU: industry_take, stat_truth, uncomfortable_truth; BOFU: direct_cta). Edit here to add or retire assets.
- **Pipeline state**: `resources/Marketing/x-pipeline/auto_tweet_state.json` — tracks every shipped post; never delete, append-only
- **Media assets**: `resources/Marketing/x-assets/library/` — 17 meme templates (`tofu/images/`), 18 GIF moods (`tofu/gifs/`), 30 MOFU atmospheric photos (`mofu/`), manifest index (`manifest.json`)
- **Generated output**: `resources/Marketing/x-assets/generated/` — Imgflip-captioned memes and Pillow-captioned GIFs produced at post time
- **Resource**: `resources/Marketing/x-strategy.md` — profile, content mix, voice, cadence, and examples for X

#### Skill 6 — Social Media (LinkedIn + Instagram)
- **Executions**: `executions/Marketing/linkedin_manager.py`, `executions/Marketing/instagram_manager.py`

#### Skill 7 — Discord Community
- **Executions**: `executions/Marketing/discord_manager.py` (server management), `executions/Marketing/discord_setup.py` (setup), `executions/Marketing/discord_audit.py` (audit), `executions/Marketing/discord_brand_channels.py` (branding), `executions/Marketing/discord_brand_messages.py` (brand messages), `executions/Marketing/setup_log_channels.py` (log channels), `executions/Marketing/register_commands.py` (slash commands), `executions/Marketing/reply_poll.py` (polls), `executions/Marketing/support_bot.py` (support), `executions/Marketing/ticket_manager.py` (tickets)

#### Skill 8 — Content & Video
- **Executions**: `executions/Marketing/content_creator.py`, `executions/Marketing/content_calendar_sync.py`, `executions/Marketing/video_pipeline_manager.py`, `executions/Marketing/generate_voiceover.py`

#### Skill 9 — Analytics & Feedback
- **Executions**: `executions/Marketing/chat_analytics.py`, `executions/Marketing/feedback_collector.py`, `executions/Marketing/retention_engagement.py`, `executions/Marketing/beta_feedback_outreach.py`, `executions/Marketing/user_onboarding.py`

#### Skill 10 — Metrics Sync
- **Execution**: `executions/Marketing/hourly_metrics_sync.py` — hourly sync of all marketing metrics to Notion/Supabase

---

### SALES SKILLS

#### Skill 11 — Beta Tester Onboarding
- **Directive**: `directives/Sales/beta-tester-onboarding.md` — beta user activation flow
- **Execution**: `executions/Sales/beta_waitlist_onboard.py`
- **Activation gate**: `Beta Activated` and `Product Used` must only be set to `true` when **Platform Activation** is confirmed (mt5/mt4/ctrader validation + persistent device). Desktop-only validation does NOT count. See `ANALYTICS/directives/platform-activation-indicator.md`

#### Skill 12 — CRM & Lead Management
- **Directive**: `directives/Sales/crm-management.md` — lead records, deal stages, CRM hygiene
- **Conversion gate**: Lead records must track `Platform Activated` (boolean) and `Activation Confidence` (confirmed/probable/desktop_only/never_seen). Only platform-activated leads count as truly converted.

#### Skill 13 — Lead Qualification
- **Directive**: `directives/Sales/lead-qualification.md` — BANT scoring, MQL to SQL criteria
- **Scoring**: Platform Activation = **+50 points** (highest single action). Desktop-only validation = +10 points. This makes Platform Activation the most impactful scoring event.

#### Skill 14 — Call Transcription
- **Execution**: `executions/Sales/call_transcriber.py` — Groq Whisper transcription and summaries

---

## Dispatchers

- `executions/Marketing/run.py` — Marketing task dispatcher
- `executions/Sales/run.py` — Sales task dispatcher

## Resources

- `resources/Marketing/marketing-reference.md` — marketing toolchain, systems, and Notion database map
- `resources/Marketing/env-reference.md` — marketing environment variables and integrations
- `resources/Marketing/x-strategy.md` — X/Twitter strategy, posting cadence, and safety rules
- `resources/Marketing/Attribution_Tracking_Pipeline.ipynb` — interactive attribution notebook
- `resources/Sales/sales-reference.md` — sales toolchain, systems, and CRM database map
- `resources/Sales/env-reference.md` — sales environment variables and integrations

## Shared Dependencies

Imports from workspace-root `shared/`: `resend_client.py`, `discord_client.py`, `notion_client.py`, `supabase_client.py`, `alerting.py`.

## Cross-Department Links

| Department | Growth Provides | Growth Needs |
|------------|----------------|--------------|
| ANALYTICS | Campaign IDs, UTM parameters | Funnel metrics, attribution reports, **Platform Activation status per user** |
| FINANCE | Lead-to-customer conversion data | Revenue per customer data |
| STRATEGY | Market feedback, user sentiment | Strategic positioning, pricing |
| ORCHESTRATOR | Task completion events | Cron scheduling, error handling |
