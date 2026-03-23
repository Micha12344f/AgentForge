# Landing Page Optimization

> CRO, A/B testing, and conversion tracking for hedgedge.info.

## Current Stack

- **Framework**: Vite + React + TypeScript
- **Hosting**: Vercel
- **Analytics**: GA4 via `shared/google_analytics_client.py`
- **Attribution**: UTM capture → Supabase

## Key Conversion Points

| Element | Event | Goal |
|---------|-------|------|
| Hero CTA | `cta_click` | Drive to sign-up |
| Beta claim form | `beta_claim` | Capture beta user |
| Pricing CTA | `checkout_start` | Drive to Creem.io checkout |
| Free guide download | `form_submit` | Lead capture |

## Optimization Process

1. Identify lowest-converting funnel stage
2. Hypothesize improvement (copy, layout, CTA placement)
3. Implement variant
4. Measure via GA4 conversion events
5. Ship winner, document learnings
