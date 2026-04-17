# Apollo Prospecting API Directive

## Purpose
Programmatic access to Apollo.io for prospect research, company enrichment, and contact management. Use this skill whenever a task involves finding companies, enriching organization data, or managing contacts in the Apollo CRM.

## Authentication

- **API Key**: Stored as `APOLLO_API_KEY` in root `.env`
- **Header**: Pass as `x-api-key` in every request
- **Base URL**: `https://api.apollo.io/api/v1`
- **Account**: Free plan (100 credits/month). Credits recharge monthly.
- **Rate Limits**: Fixed-window per minute. Check via Usage endpoint.

## Available Endpoints (Free Plan — Verified 2026-04-15)

### Tier 1 — No Credits / Always Available

| Endpoint | Method | Path | Notes |
|----------|--------|------|-------|
| Contact Search | POST | `/contacts/search` | Search your own CRM contacts. Paginated. |
| Account Search | POST | `/accounts/search` | Search your own CRM accounts. Paginated. |
| Create Contact | POST | `/contacts` | Add a person to your Apollo CRM. |

### Tier 2 — Consumes Credits

| Endpoint | Method | Path | Credits |
|----------|--------|------|---------|
| Organization Enrichment | GET | `/organizations/enrich?domain=` | 1 per call |

Returns: name, domain, industry, employee count, revenue, LinkedIn URL, Twitter, Facebook, founded year, technologies, keywords, SIC/NAICS codes, funding data, and more.

### Tier 3 — Requires Paid Plan (Blocked on Free)

| Endpoint | Path | Upgrade Needed |
|----------|------|----------------|
| People API Search | `/mixed_people/api_search` | Master API key + paid plan |
| People Enrichment | `/people/match` | Paid plan |
| Organization Search | `/mixed_companies/search` | Paid plan |
| Create Account | `/accounts` | Paid plan |
| Sequences (all) | `/emailer_campaigns/*` | Paid plan |
| Lists | `/labels` | Paid plan |
| Contact/Account Stages | `/contact_stages`, `/account_stages` | Paid plan |
| Deals | `/opportunities/*` | Paid plan |

## Workflow Patterns

### Pattern 1 — Enrich a target company
```
GET /organizations/enrich?domain=targetcompany.com
→ Returns full firmographic profile (industry, headcount, revenue, tech stack, keywords)
```
Use case: Before outreach, enrich a prospect's company to tailor messaging.

### Pattern 2 — Build contact list from known prospects
```
POST /contacts  (body: {first_name, last_name, title, organization_name, email})
→ Creates contact in Apollo CRM
POST /contacts/search  (body: {per_page: 25})
→ List all saved contacts
```
Use case: After manually identifying prospects (LinkedIn, events, referrals), log them in Apollo for tracking.

### Pattern 3 — Company research batch
```
For each domain in target list:
    GET /organizations/enrich?domain={domain}
    → Extract industry, employee count, tech stack, revenue
    → Score fit against ICP criteria
```
Use case: Qualify a batch of companies against your Ideal Customer Profile.

## Credit Budget Rules

- Free plan: 100 credits/month, currently 2/100 remaining (resets next billing cycle)
- Org enrichment costs 1 credit per unique domain
- Contact creation and search are free (no credits)
- **Never** burn more than 10 credits in a single automated run without user confirmation
- Log credit usage after each enrichment call

## Response Fields — Organization Enrichment

Key fields returned by `/organizations/enrich`:

| Field | Description |
|-------|-------------|
| `name` | Company name |
| `primary_domain` | Main website domain |
| `industry` | Industry classification |
| `estimated_num_employees` | Headcount estimate |
| `annual_revenue` | Revenue (when available) |
| `linkedin_url` | LinkedIn company page |
| `twitter_url` | Twitter/X profile |
| `founded_year` | Year founded |
| `keywords` | Array of business keywords |
| `current_technologies` | Tech stack array (with category) |
| `sic_codes` / `naics_codes` | Industry classification codes |
| `latest_funding_stage` | Most recent funding round type |
| `latest_funding_round_amount` | Most recent round amount |
| `total_funding` | All-time funding raised |

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Invalid API key | Check `APOLLO_API_KEY` in `.env` |
| 403 | Endpoint blocked on plan | Do not retry; needs plan upgrade |
| 422 | Validation error | Check request body/params |
| 429 | Rate limit exceeded | Back off and retry after window resets |

## Upgrade Path

When the prospecting pipeline needs People Search or People Enrichment (the highest-value endpoints for outbound), upgrade to Apollo Basic ($49/mo) which unlocks:
- People API Search (net-new prospect discovery — **zero credits**)
- People Enrichment (email/phone lookups — credits per call)
- Organization Search (company discovery — credits per call)
- Sequences (automated outreach cadences)

## API Documentation
- Reference docs: https://docs.apollo.io/reference/authentication
- Tutorials: https://docs.apollo.io/docs/overview-apollo-api-tutorials
- Pricing: https://docs.apollo.io/docs/api-pricing
