# Orchestrator Env Reference

Primary runtime file: `resources/.env`

| Key | Used By | Purpose |
|---|---|---|
| `NOTION_API_KEY` | `agent_router.py`, status logging flows | routing/task logs |
| `SUPABASE_*` | orchestration support reads | shared backend access |
| `DISCORD_BOT_TOKEN` | `read_bot_alerts.py`, shared alerting | Discord bot API |
| `DISCORD_GUILD_ID`, `DISCORD_ALERTS_CHANNEL_ID` | `read_bot_alerts.py` | alert retrieval targets |
| `GITHUB_TOKEN` | release/deploy workflows using `gh` or GitHub APIs | release automation |
| `VERCEL_TOKEN` | landing page deployment flows | Vercel deploys |
| `RAILWAY_*` | cron/container deployment tooling | Railway deploy context |
| `CLOUDFLARE_*` | DNS / tunnel workflows | infrastructure management |
| `RESEND_API_KEY` | landing page/email fallback ops | outbound mail |
| `SSH_*` | VPS connectivity docs and scripts | remote access |
| `PORT` | `cron_scheduler.py` | health check server port |
