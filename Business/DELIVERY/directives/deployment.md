# Deployment Directive

## Purpose
Ship agent systems to production reliably. Every deployment must be reproducible, monitorable, and rollback-capable.

## Deployment Targets

| Platform | Use Case |
|----------|----------|
| Railway | Always-on services, cron jobs, API endpoints |
| Docker | Container packaging for any target |
| Vercel | Web interfaces, dashboards |

## Deployment Checklist

### Pre-Deploy
- [ ] All tests pass locally
- [ ] Environment variables documented and configured
- [ ] Health check endpoint exists
- [ ] Monitoring alerts configured
- [ ] Rollback procedure documented

### Deploy
- [ ] Build container / push code
- [ ] Verify deployment succeeded
- [ ] Hit health check endpoint
- [ ] Verify logs are flowing

### Post-Deploy
- [ ] Monitor for 30 minutes
- [ ] Check alert channels for issues
- [ ] Verify key workflows still work
- [ ] Update deployment log
