# Deployment Workflow

> Step-by-step deploy checklist for Hedge Edge services.

## Landing Page (Vercel)

1. Push to main branch → Vercel auto-deploys
2. Verify at hedgedge.info
3. Check GA4 events still firing
4. Run attribution test

## Railway Services

1. Push to main branch → Railway auto-deploys
2. Check service logs for startup errors
3. Verify cron scheduler is running
4. Test email send pipeline

## VPS Services

1. SSH to hedge-vps via cloudflared
2. Pull latest code: `cd /opt/hedgedge && git pull`
3. Rebuild containers: `docker compose up -d --build`
4. Verify containers running: `docker ps`
5. Check logs: `docker compose logs --tail=50`

## Electron App

See `STRATEGY/directives/Product/app-deploy.md` for the full Electron release pipeline.
