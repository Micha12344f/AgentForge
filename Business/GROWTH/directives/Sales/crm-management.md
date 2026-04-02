# CRM Management

> Lead records, deal stages, and CRM hygiene for Hedge Edge sales pipeline.

## CRM Data Model

- **Primary store**: Supabase `leads` table
- **Notion mirror**: `crm_pipeline` database for visual pipeline
- **Sync**: Bidirectional via `shared/notion_client.py` + `shared/supabase_client.py`

## Deal Stages

```
New Lead → Qualified (MQL) → Sales Qualified (SQL) → Demo Scheduled → Proposal Sent → Closed Won / Closed Lost
```

## Lead Record Fields

| Field | Type | Source |
|-------|------|--------|
| Name | text | Sign-up form |
| Email | email | Sign-up form |
| Source | enum | UTM attribution |
| Engagement Score | int | Email analytics |
| Stage | enum | Sales pipeline |
| Created | datetime | Supabase auto |
| Last Activity | datetime | Event tracking |
| **Platform Activated** | **boolean** | **Supabase `license_validation_logs` + `license_devices` (mt5/mt4/ctrader with persistent device = true)** |
| **Activation Confidence** | **enum** | **confirmed / probable / desktop_only / never_seen (from `ANALYTICS/directives/platform-activation-indicator.md`)** |

> **Platform Activation** is the **ultimate conversion indicator**. A lead with `Platform Activated = true` has proven product usage on a live trading platform. Desktop app opens do NOT count. Leads should not be marked as converted until Platform Activation is confirmed.

## Hygiene Rules

- Leads with no activity >60 days → mark as stale
- Duplicate emails → merge, keep most recent
- Bounced emails → flag for review, do not send
