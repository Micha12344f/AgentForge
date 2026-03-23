---
name: email-marketing-analytics
description: |
  Reads and surfaces raw email performance data from the three Notion databases
  that back the Hedge Edge email marketing engine: campaigns, email_sequences,
  and email_sends. Does not interpret results — interpretation belongs to the
  agent or notebook layer.
---

# Email Marketing Analytics

## Execution Scripts

All data-access scripts live in:
`Hedge Edge Business/IDE 1/agents/ANALYTICS/Analytics Agent/.agents/skills/Email-marketing analytics/execution/`

| File | Database key | Purpose |
|------|-------------|---------|
| `config.py` | — | Path setup; exposes `query_db`, `get_notion`, `DATABASES` from `shared.notion_client` |
| `campaigns.py` | `campaigns` | Reads campaign-level rollup metrics via `read_campaign_metrics()` |
| `templates.py` | `email_sequences` | Reads per-template send/delivery/engagement counts via `read_template_metrics()` |
| `leads.py` | `email_sends` | Reads per-lead engagement scores and volume counts via `read_lead_engagement()` |

---

## How to Access Metrics

### Shared client

All scripts import from `config.py` which re-exports `query_db` from `shared.notion_client`.
`query_db(db_key, filter=None)` returns a list of dicts where every Notion property is a
top-level key using its exact Notion display name (e.g. `"Total Sent"`, `"Open Rate"`).
The page ID is always at `r["_id"]`.

```python
# minimal setup — add both roots to sys.path then:
from execution.config import query_db
rows = query_db("campaigns")
```

---

### `campaigns` database → `read_campaign_metrics(status_filter=None)`

**How it works:**  
Calls `query_db("campaigns")` with an optional `Status` filter.

**Notion properties accessed (exact keys):**

| Notion property | Python dict key | Type | Notes |
|-----------------|----------------|------|-------|
| `_id` | `id` | str | Notion page ID |
| `Name` | `name` | str | Campaign display name |
| `Status` | `status` | str | `'In building phase'` \| `'Active'` \| `'Discontinued'` |
| `Goal` | `goal` | str | Free-text campaign goal |
| `Start Date` | `start_date` | str | ISO date `YYYY-MM-DD` |
| `Send Frequency` | `send_frequency` | int | Hours between sends per lead |
| `Campaign Score` | `campaign_score` | int | Priority score for resolving audience overlaps |
| `Sequence Count` | `sequence_count` | int | Notion rollup — # linked templates |
| `Total Sent` | `total_sent` | int | Notion rollup — cumulative sends |
| `Total Delivered` | `total_delivered` | int | Notion rollup — confirmed deliveries |
| `Total Opened` | `total_opened` | int | Notion rollup |
| `Total Clicked` | `total_clicked` | int | Notion rollup |
| `Total Bounced` | `total_bounced` | int | Notion rollup |
| `Total Replied` | `total_replied` | int | Notion rollup |
| `Open Rate` | `open_rate` | int | Notion rollup — % of delivered |
| `Click Rate` | `click_rate` | int | Notion rollup — % of delivered |
| `Bounce Rate` | `bounce_rate` | int | Notion rollup — % of sent |
| `Reply Rate` | `reply_rate` | int | Notion rollup — % of delivered |

**Derived fields (computed in `campaigns.py`, not stored in Notion):**

| Key | Formula |
|-----|---------|
| `delivery_rate_pct` | `total_delivered / total_sent × 100` |
| `invisible_fail_count` | `total_sent − total_delivered − total_bounced` |

The invisible fail count surfaces emails that Resend accepted but receiving servers
silently discarded without issuing a bounce notification.

---

### `email_sequences` database → `read_template_metrics(campaign_id=None)`

**How it works:**  
Calls `query_db("email_sequences")` with an optional `Campaign` relation filter.
Results are sorted ascending by the sequence number extracted from the template name
via `re.search(r"(\d+)", name)`.

**Notion properties accessed (exact keys):**

| Notion property | Python dict key | Type | Notes |
|-----------------|----------------|------|-------|
| `_id` | `id` | str | Notion page ID |
| `Template` | `template_name` | str | Display name, e.g. `"Email 1 — Welcome"` |
| `Subject Line` | `subject_line` | str | |
| `Campaign` | `campaign_id` (passed in) | str | Relation — filtered by arg |
| `Sent Count` | `sent_count` | int | Total sends for this template |
| `Delivered Count` | `delivered_count` | int | Confirmed deliveries |
| `Opened Count` | `opened_count` | int | |
| `Clicked Count` | `clicked_count` | int | |
| `Bounced Count` | `bounced_count` | int | |
| `Replied Count` | `replied_count` | int | |
| `Open Rate` | `open_rate` | int | Notion rollup % |
| `Click Rate` | `click_rate` | int | Notion rollup % |
| `Bounce Rate` | `bounce_rate` | int | Notion rollup % |
| `Reply Rate` | `reply_rate` | int | Notion rollup % |

**Derived fields:**

| Key | Formula |
|-----|---------|
| `seq_num` | First integer found in `template_name` via regex |
| `delivery_rate_pct` | `delivered_count / sent_count × 100` |
| `invisible_fail_count` | `sent_count − delivered_count − bounced_count` |

---

### `email_sends` database → `read_lead_engagement(exclude_unsubscribed=True, min_score=None, max_score=None)`

**How it works:**  
Calls `query_db("email_sends")` with compound filters for `Unsubscribed` (checkbox)
and optional `Engagement Score` (number) bounds.

**Notion properties accessed (exact keys):**

| Notion property | Python dict key | Type | Notes |
|-----------------|----------------|------|-------|
| `_id` | `id` | str | Notion page ID |
| `Email` | `email` | str | |
| `First Name` | `first_name` | str | |
| `Last Name` | `last_name` | str | |
| `Source` | `source` | str | Acquisition source |
| `Unsubscribed` | `unsubscribed` | bool | |
| `Engagement Score` | `engagement_score` | int | Accumulated score (see weightings below) |
| `Pipeline stage` | `pipeline_stage` | str | Current CRM stage label |
| `Last send` | `last_send` | str | ISO datetime of most recent send |
| `Total Emails` | `total_emails` | int | Cumulative sends to this lead |
| `Total Opens` | `total_opens` | int | |
| `Total Clicks` | `total_clicks` | int | |
| `Total Replies` | `total_replies` | int | |
| `Total Bounced` | `total_bounced` | int | |

**Engagement Score weightings (applied by `railway_email_send.py` send scripts):**

| Event | Score delta |
|-------|------------|
| Email Opened | +1 |
| Link Clicked | +3 |
| Email Replied | +10 |
| Bounce | −5 |
| Unsubscribe | −100 |

**Segment boundaries (defined in `leads.py::SEGMENTS`):**

| Segment | Score range |
|---------|-------------|
| `Invalid` | < 0 |
| `Cold` | 0 – 2 |
| `Warm` | 3 – 9 |
| `Hot` | 10+ |

**Derived fields (computed in `leads.py`, not stored in Notion):**

| Key | Formula |
|-----|---------|
| `segment` | Looked up from score via `SEGMENTS` dict |
| `full_name` | `first_name + " " + last_name` |
| `open_rate_pct` | `total_opens / total_emails × 100` |
| `click_rate_pct` | `total_clicks / total_emails × 100` |
| `reply_rate_pct` | `total_replies / total_emails × 100` |
| `bounce_rate_pct` | `total_bounced / total_emails × 100` |

`segment_summary(leads=None)` groups leads by segment and returns count, avg_score,
avg_emails, avg_opens per segment.

---

## Operational Lessons

### Segment Thresholds Must Match Scoring Weights
The segment boundaries **must** be calibrated to the engagement scoring weights (+1 open, +3 click, +10 reply). With these weights, a lead needs only 3 opens to be Warm or 1 reply to be Hot. Thresholds set too high (e.g. Hot=60+) make segments meaningless — a lead with 85% open rate and 43% click rate was still classified "Cold" under the old boundaries.

**Correct thresholds**: Cold (0-2), Warm (3-9), Hot (10+).

### Invisible Fails Are a Leading Indicator of Deliverability Decay
Templates with invisible fails (sent - delivered - bounced > 0) should be flagged immediately. These are emails accepted by Resend but silently dropped by the receiving mail server — they indicate spam filtering, domain reputation issues, or content triggers. Email 4 had 8 invisible fails linked to a "loophole" spam trigger in both subject and body.

### Open Rate Benchmarks by Sequence Position
- **Email 1**: First touch — expect 15-25%. Below 15% signals subject/deliverability problem. Above 25% is strong.
- **Email 2-3**: Engaged survivors — expect 30-45%. These leads already opened Email 1.
- **Email 4+**: Late sequence — expect 20-35%. Drop-off is natural but should not fall below Email 1.
- **Any email at 0% open**: Either not yet sent or a major deliverability failure.

### Click Rate Without CTA Is Always Zero
Emails without a trackable link (`{{track:...}}`) will always show 0% click rate regardless of engagement. When reporting low click rates, first verify a link exists in the email body before diagnosing interest problems.

---

## Insights & Improvements Requirement

Every email analytics report must end with:
1. **Insights** — Identify top/bottom performing templates, deliverability trends, invisible fail patterns, segment shifts.
2. **Improvements** — Subject line changes, send-time adjustments, segment-specific actions — all backed by the data. Tag owning department (`→ @growth`).

See SKILL.md §11 for the full SOP.

---

## Notebook

`resources/Email_marketing_analytics.ipynb` — end-to-end notebook that runs all three
scripts and prints formatted tables for campaigns, templates, leads segments, and the
full Sent -> Delivered -> Opened -> Clicked -> Replied funnel.

---

## Operational Lessons (Session — March 2026)

### Campaign Score Is Now a Readable Analytics Dimension
`Campaign Score` (Number property on the campaigns database) reflects the priority hierarchy used by `railway_email_send.py` to resolve audience overlaps. When reporting on campaign effectiveness, include the score alongside metrics — it contextualises why a higher-score campaign may appear to have a smaller but more engaged audience (it wins conflicts and runs more frequently).

### Verify Hot Leads Audience After Any Bulk Operation
After large batch assignments (e.g. adding 100+ leads to Newsletter), always re-query the Hot Leads campaign audience. Bulk scripts that **overwrite** the relation field instead of appending will silently drop existing high-priority campaign links. The diagnostic query:
```python
from execution.config import query_db
HOT_LEAD_ID = "319652ea-6c6d-81a3-88db-e3ad0ac8e7c5"
hot = query_db("email_sends", filter={
    "property": "Campaign",
    "relation": {"contains": HOT_LEAD_ID}
})
print(f"Hot Leads audience: {len(hot)} leads")
for l in hot:
    print(l.get("First Name"), l.get("Engagement Score"))
```
Expected: every lead with `Engagement Score >= 10` should appear here.

### Eligible-but-Unassigned Leads Indicate a Relation Overwrite Bug
If `query_db` with a score filter returns leads that are **not** in the Hot Leads audience, the Campaign relation was overwritten rather than appended. This is a data-integrity issue, not a scoring issue — escalate to the Growth Agent to re-run the targeted reassignment script.

### A/B Archive Enables Metric-to-Content Attribution
Every call to `update_template()` in the Growth Agent archives the old body + metric snapshot to `templates_archive`. The Analytics Agent can diff the archived content against the new metrics to attribute open/click changes to specific copy or subject-line changes — this is the only auditable A/B record in the system.

### `email_sends` Is a Large Database — Always Use Increased Timeout

The `email_sends` database can have 1000+ rows. Notion API responses regularly take 5–20s per page.
With the default 15s timeout in `Orchestrator/shared/notion_client.py` `query_db()`, full lead pulls time out consistently.

**Confirmed fix (2026-03-18):** `Orchestrator/shared/notion_client.py` → `query_db()` loop → change `timeout=15` to `timeout=60`.

**Two `shared/notion_client.py` files exist in the repo:**

- `Orchestrator/shared/notion_client.py` (local scripts) — `query_db()` had hardcoded `timeout=15` (now 60, fixed 2026-03-18).
- `Hedge Edge Business/IDE 1/shared/notion_client.py` (Railway) — default `timeout=30` (fixed 2026-03-17).

Both must stay above 30s. If timeouts recur, verify which file is resolved first on `sys.path`.

**In batch/report scripts** always wrap `read_lead_engagement()` in a `try/except`:

```python
try:
    leads = read_lead_engagement()
except Exception as e:
    print(f"WARNING: lead data unavailable, using empty dataset")
    leads = []
```
