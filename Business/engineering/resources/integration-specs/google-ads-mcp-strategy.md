# Google Ads MCP Server — Production Strategy

**Status**: Planned  
**Date**: April 16, 2026  
**Owner**: ENGINEERING  
**Consumer**: Meesix MVP (read-only campaign launch assurance)

---

## 1. Architecture Overview

Meesix accesses **other users'** Google Ads accounts on their behalf. This requires the **multi-user OAuth 2.0 authentication workflow** — each Meesix customer connects their Google Ads account through an OAuth consent screen, and Meesix stores a per-user refresh token to make API calls while the user is offline.

```
┌──────────────┐    OAuth consent     ┌──────────────────┐
│  Meesix UI   │ ──────────────────►  │ Google OAuth 2.0  │
│  (customer)  │ ◄── refresh_token ── │ Consent Screen    │
└──────┬───────┘                      └──────────────────┘
       │ MCP call (streamable-http)
       ▼
┌──────────────────────────────────┐
│  google-ads-mcp (Docker)         │
│  FastMCP + Starlette             │
│  /mcp — MCP transport            │
│  /healthz — health check         │
│  ┌─────────────────────────────┐ │
│  │ google-ads-python SDK       │ │
│  │ per-user refresh tokens     │ │
│  │ read-only GAQL queries      │ │
│  └─────────────────────────────┘ │
└──────────────┬───────────────────┘
               │ REST / gRPC
               ▼
       Google Ads API v23+
```

---

## 2. OAuth & Scopes — Precise Configuration

### 2.1 Required OAuth Scope

| Scope | URI | Purpose |
|-------|-----|---------|
| **Google Ads API** | `https://www.googleapis.com/auth/adwords` | **Single scope** — covers all Google Ads API operations. Google Ads API does NOT use separate read/write scopes; read-only enforcement is done at the user role level. |

> **Critical**: There is no `adwords.readonly` scope. The `adwords` scope covers both read and write. Meesix enforces read-only behavior at the application layer by only executing read GAQL queries and never calling mutate endpoints.

### 2.2 Google Cloud Project Setup

| Step | Detail |
|------|--------|
| Create GCP project | `meesix-google-ads` (or use existing Meesix project) |
| Enable API | Google Ads API in API Library |
| OAuth consent screen | **External** user type (allows any Google user to connect) |
| App verification | **Required** — submit for Google OAuth App verification before production |
| Scopes requested | `https://www.googleapis.com/auth/adwords` |
| Authorized redirect URI | `https://app.meesix.com/oauth/google-ads/callback` (production) |
| Client type | **Web application** |

### 2.3 Developer Token

| Item | Value |
|------|-------|
| Obtain from | Google Ads Manager Account → API Center (`ads.google.com/aw/apicenter`) |
| Initial level | Explorer Access (auto-approved, limited daily calls) |
| Production level | **Basic Access** (apply after MVP validation) or **Standard Access** |
| Token scope | Tied to the Manager Account, usable across all linked client accounts |

### 2.4 Multi-User Auth Flow (Meesix ↔ Customer)

```
1. Customer clicks "Connect Google Ads" in Meesix UI
2. Meesix redirects to Google OAuth consent screen:
   - scope: https://www.googleapis.com/auth/adwords
   - access_type: offline  (gets refresh_token)
   - prompt: consent        (forces consent on first connect)
3. Google redirects back with authorization code
4. Meesix backend exchanges code for access_token + refresh_token
5. Meesix stores refresh_token (encrypted, per-customer) in database
6. MCP server uses refresh_token to generate short-lived access_tokens per call
7. MCP server sets login-customer-id header to the customer's MCC or account ID
```

### 2.5 Request Headers (Every API Call)

| Header | Source | Purpose |
|--------|--------|---------|
| `Authorization: Bearer <access_token>` | Per-user refresh token exchange | Authenticate as the customer |
| `developer-token: <token>` | Meesix Manager Account | Identifies the application |
| `login-customer-id: <mcc_id>` | Customer's top-level manager account | Determines access hierarchy |

---

## 3. Read-Only Enforcement for Meesix MVP

Since the Google Ads API has **no readonly scope**, Meesix enforces read-only at multiple layers:

| Layer | Mechanism |
|-------|-----------|
| **OAuth scope** | `adwords` (only option — but this is standard) |
| **User role** | Request customers grant **Read-only** access to Meesix's linked manager account where possible |
| **Application code** | MCP tools only execute `GoogleAdsService.SearchStream` with GAQL SELECT queries — **zero mutate calls** |
| **MCP tool design** | No tools expose create/update/delete operations |
| **Code review gate** | Any tool that calls a mutate endpoint requires explicit approval |

---

## 4. MCP Tools — MVP Tool Set

All tools are read-only GAQL queries. Maximum 7 tools per the AgentForge design constraint.

| # | Tool | GAQL Target | Meesix Use Case |
|---|------|-------------|-----------------|
| 1 | `list_accessible_customers` | `CustomerService.ListAccessibleCustomers` | Discover which accounts the connected user can access |
| 2 | `get_campaign_details` | `campaign` resource | Fetch campaign config: status, budget, bidding, network settings |
| 3 | `get_ad_groups` | `ad_group` resource | List ad groups under a campaign with status and targeting |
| 4 | `get_ads` | `ad_group_ad` resource | Retrieve ad creatives, approval status, policy info |
| 5 | `get_campaign_budget` | `campaign_budget` resource | Budget amount, delivery method, shared budget linkage |
| 6 | `get_conversion_tracking` | `conversion_action` resource | Verify conversion tracking is configured and active |
| 7 | `get_campaign_metrics` | `campaign` + `metrics` | Recent performance: impressions, clicks, cost, conversions |

---

## 5. Security & Compliance

| Concern | Mitigation |
|---------|------------|
| Refresh token storage | AES-256 encrypted at rest, never logged, never in container image |
| Token rotation | Refresh tokens exchanged for short-lived access tokens (1hr) per request |
| Secrets injection | All secrets via environment variables at container runtime, never baked |
| Developer token protection | Single env var, never committed to source |
| HTTPS only | MCP server behind reverse proxy with TLS termination |
| OAuth App Verification | Submit to Google before going beyond test users |
| Consent screen branding | Meesix logo, privacy policy URL, terms URL (already at `shared/meesix-privacy/`) |
| Rate limiting | Google Ads API has per-developer-token quotas; implement backoff |
| Container hardening | Non-root, read-only FS, cap drop ALL, mem/CPU limits, no Docker socket |

---

## 6. Google Cloud Prerequisites Checklist

- [ ] Create or select GCP project for Meesix
- [ ] Enable Google Ads API in the project
- [ ] Configure OAuth consent screen (External, app name "Meesix")
- [ ] Add scope `https://www.googleapis.com/auth/adwords`
- [ ] Set authorized redirect URIs
- [ ] Create OAuth 2.0 Client ID (Web application type)
- [ ] Record `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`
- [ ] Create Google Ads Manager Account for Meesix
- [ ] Apply for Developer Token at `ads.google.com/aw/apicenter`
- [ ] Record `GOOGLE_ADS_DEVELOPER_TOKEN`
- [ ] Apply for Basic Access once MVP is validated
- [ ] Submit OAuth App for Google verification before public launch

---

## 7. Environment Variables

```env
# Google Ads API credentials
GOOGLE_ADS_CLIENT_ID=           # OAuth 2.0 client ID
GOOGLE_ADS_CLIENT_SECRET=       # OAuth 2.0 client secret
GOOGLE_ADS_DEVELOPER_TOKEN=     # Developer token from API Center
GOOGLE_ADS_LOGIN_CUSTOMER_ID=   # Default MCC ID (overridden per-user)

# MCP Server config
MCP_PORT=8000
MCP_TRANSPORT=streamable-http
```

---

## 8. Docker Strategy

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Base image | `python:3.12-slim` | Matches AgentForge standard |
| Framework | `FastMCP` + `Starlette` wrapper | `/mcp` transport + `/healthz` health |
| Transport | `streamable-http` | Production default per directive |
| Container runtime | Docker on WSL2 (local dev) → Linux (production) | Existing infra pattern |
| Compose | Single-service `docker-compose.yml` | One MCP per container |
| Health check | `GET /healthz` → 200 | Container orchestrator readiness |

---

## 9. Implementation Sequence

1. **Docker Desktop install** — `winget install Docker.DockerDesktop`
2. **Scaffold MCP server** — use `mcp_container_scaffold.py` pattern
3. **Implement tools** — `google-ads-python` SDK + GAQL queries
4. **OAuth callback endpoint** — token exchange and storage
5. **Local test** — stdio transport against test Google Ads account
6. **Containerize** — Dockerfile + Compose with hardening flags
7. **Deploy** — WSL2 Docker local → VPS production
