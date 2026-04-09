# Tool Integrations Directive

## Purpose
Build production-grade integration clients for the 5 target business tools. Each integration must be reliable enough to run in automated agent workflows without human supervision.

## Target Integrations

### 1. HubSpot CRM
- **Auth**: API key or OAuth2
- **Operations**: Create/read/update contacts, create/read deals, lifecycle stage changes, webhook subscriptions
- **Priority**: Day 1–2

### 2. Slack
- **Auth**: Bot token (OAuth2)
- **Operations**: Send messages, create channels, slash command handling, interactive message buttons/modals
- **Priority**: Day 1–2

### 3. Google Workspace
- **Auth**: Service account with domain-wide delegation
- **Operations**: Gmail send/read, Drive file create/read/share, Calendar event CRUD
- **Priority**: Day 1–2

### 4. Asana or Linear
- **Auth**: Personal access token (Asana) or API key (Linear)
- **Operations**: Create/read/update tasks, create projects, status changes, webhook subscriptions
- **Priority**: Day 3–4

### 5. Stripe or Xero
- **Auth**: API key (Stripe) or OAuth2 (Xero)
- **Operations**: Create/read invoices, payment status, reconciliation events
- **Priority**: Day 3–4

## Standards Per Integration

- [ ] Auth handling: token refresh, key rotation support
- [ ] CRUD operations: create, read, update, delete (where applicable)
- [ ] Rate-limit handling: respect headers, backoff, queue
- [ ] Error handling: typed exceptions, retry logic
- [ ] Tests: unit tests with mocks + integration tests with sandbox accounts
- [ ] Documentation: auth setup guide, operation reference
