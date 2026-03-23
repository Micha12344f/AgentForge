# Attribution Tracking

> UTM attribution pipeline, referrer normalization, and multi-touch tracking.

## Pipeline

```
User clicks link with UTMs → Landing page captures params → Supabase stores on sign-up
→ attribution_audit.py validates → daily_analytics.py reports
```

## First-Touch Attribution

- Attribution window: 30 days
- First UTM params stored in localStorage, persisted to Supabase on sign-up
- Raw referrer captured as fallback when no UTM present

## Referrer Normalization Map

| Raw Referrer | Canonical Source |
|-------------|-----------------|
| `l.linkedin.com` | `linkedin` |
| `t.co` | `twitter` |
| `lm.facebook.com` | `facebook` |
| `discord.com` | `discord` |
| `mail.google.com` | `email` |
| (empty) | `direct` |
