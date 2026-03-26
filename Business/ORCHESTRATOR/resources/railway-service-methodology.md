# Railway Service Methodology

Reference for creating new Railway services, finding active services, and validating production container deploys.

## Core Commands

### Identify account and current link
```powershell
railway whoami
railway status
```

### List projects and inspect active state
```powershell
railway list --json
```

Read these fields carefully:
- `id`
- `name`
- `deletedAt`
- `services.edges`
- `environments.edges`

### Link to a project
```powershell
railway link --project <project-id>
```

### Create a service
```powershell
railway add --service "<service-name>"
```

### Link to an existing service
```powershell
railway service link "<service-name>"
```

### List or set variables
```powershell
railway variable list --service "<service-name>" -k
railway variable set --service "<service-name>" --skip-deploys "KEY=value"
```

### Deploy
```powershell
railway up --service "<service-name>" -c -m "<deploy message>"
```

### Verify runtime
```powershell
railway logs --service "<service-name>" --latest --lines 100
```

## Service Discovery Checklist

Use this sequence when a user says a service is missing or invisible:

1. Check `railway status`
2. If status says project is deleted or missing, run `railway list --json`
3. Ignore projects where `deletedAt` is not null
4. Prefer active projects already holding neighboring production services
5. Link the workspace to the target project
6. Confirm the target service exists before creating anything new

## New Service Boot Checklist

Before first deploy:
1. Create the service
2. Set minimum required secrets
3. Confirm deploy context is small enough
4. Confirm the intended Dockerfile path is actually used

After first deploy:
1. Check startup logs
2. Confirm health endpoint bind
3. Confirm scheduler or worker boot behavior
4. Confirm no missing env var errors

## Known Failure Modes

### Deleted linked project
Symptoms:
- `railway status` says the project is deleted
- the user cannot see the expected service

Fix:
```powershell
railway list --json
railway link --project <active-project-id>
```

### 413 Payload Too Large
Symptoms:
- upload fails before build starts
- Cloudflare returns `413 Payload Too Large`

Typical causes:
- `.venv/`
- `tmp/`
- screenshots, profiles, cached exports, large local artifacts

Fix:
- exclude local-only directories in `.gitignore`
- retry `railway up`

### Service created but not booting
Symptoms:
- build succeeds
- runtime logs show import or missing env failures

Fix:
- inspect `railway logs --service "<service-name>" --latest --lines 100`
- set missing variables
- redeploy

## Verified Pattern

For dedicated container services:
1. link to the active project
2. create the service explicitly
3. load secrets with `railway variable set --skip-deploys`
4. shrink upload context if needed
5. deploy with `railway up --service ... -c`
6. verify startup via logs immediately