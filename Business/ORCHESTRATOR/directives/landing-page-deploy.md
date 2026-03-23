---
name: landing-page-deploy
description: Deploys the Hedge Edge landing page to Vercel — commits changes, pushes to GitHub as the correct author, manages Vercel env vars, and triggers production deployment. Use when the user says "deploy landing page", "push site", "update website", or "deploy to Vercel".
---

# Landing Page Deploy

End-to-end deployment skill for the **Hedge Edge landing page** (Vite + Vercel).
Follows the verified workflow used to deploy the beta launch site.

## When to Use This Skill

Use when the user wants to:

- Deploy landing page changes to production
- Add or update Vercel environment variables
- Push code to the landing page GitHub repo
- Fix deploy failures related to author identity or env vars
- Trigger a Vercel production redeploy

## Repository & Deploy Context

| Key | Value |
|-----|-------|
| GitHub repo | `Micha12344f/Hedge-Edge-Landing-Page` |
| Vercel project | `hedge-edge-landing-page` |
| Vercel team | `hedge-edges-projects` |
| Vercel plan | **Hobby** (single-owner, no collaborators) |
| Production URL | `https://hedgedge.info` |
| Build tool | Vite |
| Serverless functions | `api/` directory (Vercel serverless) |
| Local dev | `npm run dev` (port 3000) |
| Working directory | `Context/Current landing page/` |

## CRITICAL: Always Deploy to `hedge-edge-landing-page` — Never Create a New Project

**There is exactly ONE official Vercel project: `hedge-edge-landing-page` (team: `hedge-edges-projects`).**  
This is the project aliased to `https://hedgedge.info`. Do NOT create a second project.

Before every deploy, verify the local `.vercel` config points to the correct project:

```powershell
# Must show hedge-edges-projects/hedge-edge-landing-page
vercel projects ls 2>&1 | Select-String "landing-page"
```

If the local project is wrong or unlinked, **always re-link explicitly by project name**:

```bash
vercel link --project hedge-edge-landing-page --yes
```

**Never run `vercel link --yes` without `--project`** — it may create a new project with a different name (e.g. `landing-page`), which will NOT be aliased to `hedgedge.info` and will pollute the Vercel dashboard.

---

## Critical: Git Author Identity

Vercel Hobby plan **rejects pushes** if the commit author doesn't match the GitHub account linked to the Vercel project.

**Required git config for this repo:**
```bash
git config user.name "Micha12344f"
git config user.email "262809317+Micha12344f@users.noreply.github.com"
```

- The real email (`rmcap1ta7@gmail.com`) is **blocked** by GitHub's email privacy setting
- Always use the no-reply email: `262809317+Micha12344f@users.noreply.github.com`
- If a commit was made with the wrong author, amend it before pushing:

```bash
git commit --amend --author="Micha12344f <262809317+Micha12344f@users.noreply.github.com>" --no-edit
```

## Required Vercel Environment Variables

All env vars must be set in Vercel **production** environment. The serverless functions (`api/`) read these at runtime via `process.env`.

| Variable | Used By | Purpose |
|----------|---------|---------|
| `RESEND_API_KEY` | `claim-beta.ts`, `send-guide.ts` | Email delivery via Resend |
| `SUPABASE_URL` | `claim-beta.ts` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `claim-beta.ts` | Supabase service role key (pool-based key assignment) |
| `NOTION_API_KEY` | `send-guide.ts`, `handle-unsubscribe.ts` | Notion database writes |
| `UNSUBSCRIBE_SECRET` | `handle-unsubscribe.ts`, `handle-resubscribe.ts` | HMAC secret for unsubscribe tokens |
| `CREEM_API_KEY` | `creem-checkout.ts` | Creem.io payment API |
| `CREEM_API_BASE_URL` | `creem-checkout.ts` | `https://test-api.creem.io` (test) or `https://api.creem.io` (live) |
| `CREEM_PRODUCT_ID_SHIELD_MONTHLY` | `creem-checkout.ts` | Product ID |
| `CREEM_PRODUCT_ID_SHIELD_ANNUAL` | `creem-checkout.ts` | Product ID |
| `CREEM_PRODUCT_ID_MULTI_MONTHLY` | `creem-checkout.ts` | Product ID |
| `CREEM_PRODUCT_ID_MULTI_ANNUAL` | `creem-checkout.ts` | Product ID |
| `CREEM_PRODUCT_ID_UNLIMITED_MONTHLY` | `creem-checkout.ts` | Product ID |
| `CREEM_PRODUCT_ID_UNLIMITED_ANNUAL` | `creem-checkout.ts` | Product ID |
| `SITE_URL` | `creem-checkout.ts` | Redirect base URL |

### Adding Env Vars (PowerShell — No Newline Corruption)

PowerShell pipes add `\r\n` to values, corrupting API keys. **Always use file redirection:**

```powershell
# CORRECT — write to temp file, redirect into vercel CLI
[System.IO.File]::WriteAllBytes("$env:TEMP\envval.txt", [System.Text.Encoding]::UTF8.GetBytes("YOUR_VALUE"))
cmd /c "vercel env add VAR_NAME production < %TEMP%\envval.txt"
```

```powershell
# WRONG — these all add \r\n to the value
echo "value" | vercel env add VAR_NAME production        # ❌
"value" | vercel env add VAR_NAME production              # ❌
cmd /c "echo|set /p=value" | vercel env add ...           # ❌
```

### Verifying Env Vars

```bash
# List all production env vars
vercel env ls production

# Pull and inspect actual values (check for \r\n corruption)
vercel env pull .env.vercel-check --environment production
cat .env.vercel-check
```

### Removing/Updating an Env Var

```bash
vercel env rm VAR_NAME production --yes
# Then re-add using the file redirection method above
```

## Deployment Workflow (4 Steps)

### Step 1 — Verify Git Identity

```bash
cd "Context/Current landing page"
git config user.name   # Should be: Micha12344f
git config user.email  # Should be: 262809317+Micha12344f@users.noreply.github.com
```

If wrong, set it:
```bash
git config user.name "Micha12344f"
git config user.email "262809317+Micha12344f@users.noreply.github.com"
```

### Step 2 — Commit Changes

```bash
git add -A
git commit -m "description of changes"
```

If the commit was made with the wrong author:
```bash
git commit --amend --author="Micha12344f <262809317+Micha12344f@users.noreply.github.com>" --no-edit
```

### Step 3 — Push to GitHub

```bash
git push origin main
```

Vercel auto-deploys on push. If push is rejected:
- **Author mismatch**: Amend commit author (see Step 2), then force push:
  ```bash
  git push --force origin main
  ```
- **Remote ahead**: Pull first:
  ```bash
  git pull --no-edit origin main
  git push origin main
  ```

### Step 4 — Verify Deployment

```bash
# Option A: Check via Vercel CLI
vercel ls --limit 3

# Option B: Direct production deploy (bypasses git push)
vercel --prod
```

Confirm the site is live at `https://hedgedge.info`.

## Env Var Changes Require Redeploy

Vercel env vars only take effect on **new deployments**. After adding/changing env vars:

```bash
vercel --prod
```

Or push a new commit to trigger auto-deploy.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Push rejected by Vercel | Commit author ≠ Vercel project owner | Amend author to `Micha12344f` with no-reply email |
| "Email service not configured" | `RESEND_API_KEY` missing in Vercel | Add env var + redeploy |
| "Unexpected error" on `vercel --prod` | Hobby plan restriction or auth issue | Check `vercel whoami`, re-link project |
| Env var values have `\r\n` | PowerShell pipe corruption | Remove + re-add using file redirection method |
| 500 errors on serverless functions | Missing env vars | Check `vercel env ls production`, add missing vars |
