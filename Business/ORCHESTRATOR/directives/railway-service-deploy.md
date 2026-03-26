# Railway Service Deployment & Discovery

Use this directive when Orchestrator needs to find active Railway services, recover from a broken project link, create a brand new service, or deploy a container-backed service safely.

## Objective

Make Railway service operations repeatable and non-interactive where possible:
- find the active Railway project
- determine whether a service already exists
- create a new service if needed
- set required variables before first boot
- deploy with the smallest safe upload context
- verify runtime health after deploy

## Standard Method

### 1. Inspect the current Railway link first

Run:
```powershell
railway whoami
railway status
```

If `railway status` reports that the project is deleted or missing, do not deploy yet. Find the active project first.

### 2. Find active projects and detect deleted/orphaned ones

Run:
```powershell
railway list --json
```

Use the JSON output as the source of truth.

Rules:
- if `deletedAt` is non-null, treat the project as inactive
- if `services.edges` is empty, do not assume the project is usable for production
- prefer linking to an active project that already holds adjacent production services

### 3. Link the workspace to the correct project and service

Run:
```powershell
railway link --project <project-id>
railway service link <service-name>
```

If the target service does not exist yet, create it first.

### 4. Create a new service deliberately

Run:
```powershell
railway add --service "<service-name>"
```

Guidelines:
- use explicit service names, not random generated names
- create the service before setting variables or deploying
- after creation, confirm `railway status` points at the intended service

### 5. Set required variables before first deploy

Inspect the entrypoint and imported shared modules for required `os.getenv(...)` usage.

Set variables with:
```powershell
railway variable set --service "<service-name>" --skip-deploys "KEY=value"
```

Guidelines:
- use `--skip-deploys` while loading multiple variables
- set the minimum boot-critical variables first
- only trigger a deploy after required runtime secrets are present

### 6. Keep the upload context small

Before `railway up`, check whether the repo contains large local-only directories such as:
- `.venv/`
- `tmp/`
- screenshots, browser profiles, exports, caches, notebooks with heavy outputs

If necessary, exclude them in `.gitignore` so Railway does not upload them.

Common failure:
- `413 Payload Too Large` from Cloudflare during upload

### 7. Deploy explicitly to the target service

Run:
```powershell
railway up --service "<service-name>" -c -m "<deploy message>"
```

Guidelines:
- use `-c` for CI-style non-interactive output
- always pass `--service` when multiple services exist in the project
- record whether Railway used the intended Dockerfile or a detected fallback

### 8. Verify runtime, not just build success

After deployment, check:
```powershell
railway status
railway logs --service "<service-name>" --latest --lines 100
```

Look for:
- container startup line
- health server bind
- scheduler/job registration
- missing env var errors
- import errors
- provider API auth failures

## Preferred Service Discovery Flow

When the user says they cannot see a service on Railway:
1. run `railway status`
2. if the linked project is deleted or wrong, run `railway list --json`
3. identify the active project by `deletedAt == null`
4. link to that project
5. inspect whether the target service already exists
6. only create a new service if there is no existing active one with the intended role

## Orchestrator Rules

- Never assume the currently linked Railway project is correct.
- Never deploy a new service before checking whether a deleted project link is masking the real active project.
- Never rely on build success alone; inspect runtime logs after deploy.
- Prefer explicit `--service` targeting for all Railway operations in multi-service projects.
- If a deploy requires a huge workspace upload, reduce context first instead of brute-forcing repeated deploy attempts.