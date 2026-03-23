# Attribution Tracking

> UTM attribution pipeline — how Hedge Edge tracks where users come from.

## Pipeline

1. Landing page captures UTM params (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`)
2. Params stored in Supabase `user_attribution` table on sign-up
3. `attribution_audit.py` validates pipeline integrity
4. Referrer normalization maps raw referrers to canonical sources

## UTM Conventions

| Parameter | Convention | Example |
|-----------|-----------|---------|
| `utm_source` | Platform name | `linkedin`, `twitter`, `email`, `discord` |
| `utm_medium` | Channel type | `social`, `email`, `cpc`, `referral` |
| `utm_campaign` | Campaign slug | `beta-launch`, `waitlist-nurture` |
| `utm_content` | Creative variant | `cta-button`, `hero-link` |

## Validation Rules

- Every sign-up MUST have `utm_source` or a raw referrer
- Attribution window: 30 days first-touch
- Direct traffic (no referrer, no UTM) flagged for review
