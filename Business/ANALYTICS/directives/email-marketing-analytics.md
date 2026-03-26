---
name: email-marketing-analytics
description: |
  Reads and surfaces operational email marketing data from the live Notion-backed
  campaign, template, and lead systems used by Hedge Edge. This directive reflects
  the current workspace architecture, where the operational data layer lives under
  GROWTH and Analytics consumes those readers for reporting.
---

# Email Marketing Analytics

## Active Code Paths

The current workspace does not use the old skill-local `execution/*.py` readers for day-to-day email analytics.
The operational data layer lives here instead:

| File | Database key | Purpose |
|------|-------------|---------|
| `Business/GROWTH/executions/Marketing/email_marketing/campaigns.py` | `campaigns` | Reads campaign metadata and performance rates via `read_campaigns()` |
| `Business/GROWTH/executions/Marketing/email_marketing/templates.py` | `email_sequences` | Reads template metadata and sequence ordering via `read_templates()` / `list_templates_for_campaign()` |
| `Business/GROWTH/executions/Marketing/email_marketing/leads.py` | `leads_crm` | Reads lead scores, segments, unsubscribe state, and campaign relations via `read_leads()` / `_read_leads_full()` |
| `Business/GROWTH/executions/Marketing/Send_Emails.ipynb` | all three | Interactive reporting and send-eligibility notebook |
| `Business/ANALYTICS/executions/email_template_audit.py` | `email_sequences` | Analytics-side body audit using direct Notion reads |

## Shared Access Pattern

Operational scripts add the workspace root and Marketing directory to `sys.path`, then import the Growth-side readers.
Raw Notion access still comes from `shared.notion_client.query_db()`.

```python
import os
import sys

ws = r"C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
marketing = os.path.join(ws, "Business", "GROWTH", "executions", "Marketing")
for path in (ws, marketing):
    if path not in sys.path:
        sys.path.insert(0, path)

from email_marketing.campaigns import read_campaigns
from email_marketing.templates import read_templates, list_templates_for_campaign
from email_marketing.leads import read_leads, _read_leads_full
```

## Current Readers

### `campaigns` → `read_campaigns(status_filter=None)`

Returns campaign dicts with:

- `id`
- `name`
- `status`
- `send_frequency`
- `campaign_score`
- `priority`
- `goal`
- `notes`
- `start_date`
- `open_rate`
- `click_rate`
- `bounce_rate`
- `reply_rate`
- `sequence_count`

Use raw Notion properties when count-based campaign rollups are required beyond these mapped fields.

### `email_sequences` → `read_templates(campaign_id=None)` / `list_templates_for_campaign(campaign_id)`

Returns template dicts with:

- `id`
- `template_name`
- `subject_line`
- `campaign_ids`
- `status`
- `trigger`
- `send_delay_hours`
- `notes`
- `open_rate`
- `click_rate`
- `bounce_rate`
- `reply_rate`
- `_seq_num`

Relation extraction is patched so the `Campaign` property returns page ID lists instead of `None`.

### `leads_crm` → `read_leads(segment=None, exclude_unsubscribed=True)`

Returns lead dicts with:

- `id`
- `email`
- `first_name`
- `last_name`
- `score`
- `segment`
- `pipeline_stage`
- `last_send`
- `source`
- `unsubscribed`

`_read_leads_full()` additionally returns `email -> campaign_ids` mappings for assignment and audience diagnostics.

## Operational Rules

- Include `campaign_score` when explaining campaign overlap behavior or audience priority.
- Use `list_templates_for_campaign()` when sequence order matters; it sorts by `Send Delay Hours`.
- Treat `leads_crm` as the current operational lead store for segmentation and assignment analysis.
- Keep Notion query timeouts high enough for large datasets; local analytics workflows currently assume 60s request timeouts in `shared/notion_client.py`.
- Wrap large lead/template pulls in `try/except` during reporting flows so one slow Notion response does not crash the whole report.

## Insights & Improvements Requirement

Every email analytics report must end with:
1. **Insights** — top/bottom performers, segment shifts, deliverability issues, sequence behavior.
2. **Improvements** — subject-line, sequencing, CTA, or audience recommendations backed by the data and tagged `→ @growth` when Growth owns the fix.
