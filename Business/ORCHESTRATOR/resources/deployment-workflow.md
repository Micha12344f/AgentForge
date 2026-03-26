# Deployment Workflow

> Step-by-step deploy checklist for Hedge Edge services.

## Landing Page (Vercel)

1. Push to main branch → Vercel auto-deploys
2. Verify at hedgedge.info
3. Check GA4 events still firing
4. Run attribution test

## Railway Services

### Existing service deploy

1. Confirm the workspace is linked to the correct active project: `railway status`
2. If the link is stale or deleted, inspect projects with: `railway list --json`
3. Deploy explicitly to the intended service: `railway up --service "<service-name>" -c`
4. Check runtime logs: `railway logs --service "<service-name>" --latest --lines 100`
5. Verify health server or startup message
6. Verify cron scheduler or worker boot path

### New service creation

1. Link to the active project first: `railway link --project <project-id>`
2. Create the new service: `railway add --service "<service-name>"`
3. Load required variables without triggering intermediate deploys: `railway variable set --service "<service-name>" --skip-deploys "KEY=value"`
4. Ensure local-only large folders are excluded from upload context (`.venv/`, `tmp/`, screenshots, caches)
5. Deploy the new service explicitly: `railway up --service "<service-name>" -c -m "<message>"`
6. Confirm the container booted successfully from logs

See `resources/railway-service-methodology.md` for the full Railway service discovery and deployment playbook.

## VPS Services

1. SSH to hedge-vps via cloudflared
2. Pull latest code: `cd /opt/hedgedge && git pull`
3. Rebuild containers: `docker compose up -d --build`
4. Verify containers running: `docker ps`
5. Check logs: `docker compose logs --tail=50`

## Electron App

See `STRATEGY/directives/Product/app-deploy.md` for the full Electron release pipeline.
