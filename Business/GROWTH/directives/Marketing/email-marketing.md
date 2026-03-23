---
name: email-marketing
description: |
  Manages Hedge Edge email campaigns end-to-end: creates and activates campaigns,
  builds email template sequences, assigns leads by Engagement Score and segment, and
  orchestrates sends via Resend. Runs routine CRM hygiene — evicts dead leads
  (5+ emails, zero engagement) to keep the pipeline clean. Backed by real Notion
  data — all reads and writes hit the live campaigns, email_sequences, and
  email_sends databases. Use for campaign lifecycle management, audience
  assignment, drip sequences, send orchestration, and CRM enrichment.
---

# Email Marketing

## Objective

Run Hedge Edge's outbound email engine. Every function maps directly to a Notion database operation — no mock data, no stubs. The goal is to move leads through a scored drip sequence based on their Engagement Score (accrued via opens, clicks, and replies) while maintaining clean campaign hygiene and respecting send frequency rules.

## When to Use This Skill

- A new campaign needs to be created, activated, or paused
- An email template sequence needs to be built or extended
- Leads need to be assigned to a campaign based on Engagement Score or segment
- A send run needs to be previewed, executed, or debugged
- Campaign metrics need to be read and summarised
- The audience for a campaign needs to be previewed, refreshed, or cleared
- Dead leads need to be evicted from the CRM (routine hygiene)
- The CRM needs enrichment or cleanup

## Input Specification

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `request_type` | enum | yes | — | See list below |
| `campaign_id` | string | context | — | Notion page ID |
| `campaign_name` | string | create only | — | Human-readable name |
| `send_frequency` | integer | no | 48 | Hours between sends |
| `min_score` | integer | no | 0 | Filter leads by Engagement Score |
| `dry_run` | boolean | no | true | Always preview before executing |

**Request types**: `read_campaigns`, `create_campaign`, `activate_campaign`, `pause_campaign`, `read_templates`, `create_template`, `list_sequence`, `read_leads`, `preview_audience`, `assign_leads`, `clear_audience`, `send_preview`, `send_execute`, `trigger_railway_send`, `evict_dead_leads`, `remove_leads_by_email`, `remove_leads_by_filter`, `remove_duplicates`

## Step-by-Step Process

### Step 1 — Read Current State

Before any write operation, always read first:

```python
python -c "
import sys
sys.path.insert(0, r'C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge')
sys.path.insert(0, r'C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge\Hedge Edge Business\IDE 1\agents\GROWTH\Marketing Agent\.agents\skills\email-marketing')
from execution.campaigns import read_campaigns
from execution.leads import read_leads
for c in read_campaigns():
    print(c['status'], c['name'], 'score='+str(c['campaign_score']))
print('Total leads:', len(read_leads()))
"
```

### Step 2 — Campaign Lifecycle

**Create a campaign** (starts as In building phase):
```python
from execution.campaigns import create_campaign
create_campaign(
    name="Q2 Prop Trader Nurture",
    send_frequency=48,  # hours between sends
    goal="Convert Warm leads from prop trading segment",
    campaign_score=70   # Priority score for resolving audience overlaps
)
```

**Update campaign properties**:
```python
from execution.campaigns import update_campaign
update_campaign(
    campaign_id="<id>",
    campaign_score=80,
    send_frequency=72
)
```

**Activate or pause**:
```python
from execution.campaigns import activate_campaign, pause_campaign
activate_campaign(campaign_id="<notion-page-id>")
pause_campaign(campaign_id="<notion-page-id>")
```

> **No delete.** Use `pause_campaign` to stop. Hard deletion is blocked by design.

### Step 3 — Build Template Sequence

Number templates sequentially (`Email 1`, `Email 2`, …) so the send workflow maps Pipeline Stage → next email correctly.

#### Approved CTA URLs (Use Only These)

When writing email bodies that include a call-to-action link, always pick from the three approved destinations below. **Do not invent other URLs.** The send system auto-tracks every plain HTTPS link — no special syntax needed.

| Intent | URL |
|--------|-----|
| General awareness / homepage | `https://hedgedge.info` |
| Educational / soft CTA | `https://hedgedge.info/guide` |
| High-intent / hard CTA (book a call) | `https://cal.eu/hedgedge/30min` |

**Matching CTA to funnel stage:**
- **Cold / Email 1**: No CTA link. Build curiosity only.
- **Warm / Email 2–3**: Soft CTA → Guide (`https://hedgedge.info/guide`) or homepage.
- **Hot / Email 4+ or Hot Lead campaign**: Hard CTA → Book a call (`https://cal.eu/hedgedge/30min`).
- **Re-engagement**: One soft CTA only — guide or homepage. Never a straight meeting link for cold-again leads.

**Example body snippet** (Email 2):
```
If you're curious how it works, here's a quick overview:
https://hedgedge.info/guide

Ryan
```

**Example body snippet** (Hot Lead Email 2):
```
I'd love to show you how this works for your setup — grab a slot here:
https://cal.eu/hedgedge/30min

Ryan
```

**Naming convention (REQUIRED)**: Every template name must contain `Email <N>` (where N is an integer). The sequence sorter uses `re.search(r"(\d+)", name)` to extract position — if the number is missing the template sorts to position 0.

**New campaign** — use `create_template()` for the initial sequence:
```python
from execution.templates import create_template
create_template(
    campaign_id="<notion-page-id>",
    template_name="Email 1 — Welcome",
    subject_line="Welcome to Hedge Edge, {{Name}}!"
)
```

**Existing campaign** — use `add_next_template()` to extend the sequence. It auto-detects the highest existing number and names the new template accordingly:
```python
from execution.templates import add_next_template

# Adds "Email 4" (or next available number)
add_next_template(campaign_id="<notion-page-id>", subject_line="Still here?")

# Adds "Email 4 — Follow-up"
add_next_template(campaign_id="<notion-page-id>", subject_line="Still here?", label="Follow-up")
```

**Updating an existing template** — always go through `update_template()`. It captures the prior email body from the live code block, archives both the metrics and the body to `templates_archive`, then writes the new content:
```python
from execution.templates import update_template
update_template(
    "<template-page-id>",
    new_content="Format: PLAIN TEXT\nFrom: ...\nSubject: ...\n\nBody here",
    subject_line="Updated subject",
)
```

### Step 4 — Assign Audience

#### Option A — All Segments at Once (Preferred)

Use `assign_all_segments()` when assigning the full lead database across all three segments in one operation. It performs a **single bulk DB read** and routes each lead to its campaign in one pass — the most efficient option for full-audience assignments.

```python
from execution.leads import assign_all_segments
from execution.campaigns import read_campaigns

# Look up campaign IDs by name
campaigns = read_campaigns('Active')
by_name = {c['name'].lower(): c for c in campaigns}

segment_map = {
    'Cold': by_name['hedge awareness campaign']['id'],
    'Warm': by_name['warm lead conversion']['id'],
    'Hot':  by_name['hot-lead follow up']['id'],
}

# Dry run first
counts = assign_all_segments(segment_map, dry_run=True)
print(counts)  # {'Cold': 167, 'Warm': 41, 'Hot': 4, 'total': 212, 'errors': 0}

# Execute
counts = assign_all_segments(segment_map, dry_run=False)
print(f"Assigned {counts['total']} leads, errors={counts['errors']}")
```

#### Option B — Single Campaign by Score

Use `assign_leads_by_score()` when targeting one specific campaign with a score filter.

**Preview first (dry_run=True default)**:
```python
from execution.leads import preview_assignments
# Example: Targeting leads who have at least clicked a link (+3 points)
eligible = preview_assignments(campaign_id="<id>", min_score=3)
print(f'{len(eligible)} leads would be assigned')
```

**Execute**:
```python
from execution.leads import assign_leads_by_score
# dry_run=True returns the count without writing
count = assign_leads_by_score(campaign_id="<id>", min_score=3, dry_run=True)
print(f'{count} leads would be assigned')

count = assign_leads_by_score(campaign_id="<id>", min_score=3, dry_run=False)
print(f'Assigned {count} leads')
```

#### Option C — Beta Activation Leads
When a lead is issued a beta license key, they enter the Beta Funnel. This requires a **dual-database write**:
1. Add/Update the lead in the `beta_waitlist` database (tag them with "Beta", "Beta Key Sent").
2. Assign the lead in the main `email_sends` CRM to the "Beta Activation" campaign.

```python
from execution.campaigns import read_campaigns
from shared.notion_client import query_db, update_row

campaigns = read_campaigns('Active')
beta_camp_id = next(c['id'] for c in campaigns if c['name'] == 'Beta Activation')

# Example: Assigning a specific email to the campaign
leads = query_db("email_sends", filter={"property": "Email", "email": {"equals": "user@example.com"}})
if leads:
    existing = leads[0].get("Campaign") or []
    if beta_camp_id not in existing:
        update_row(leads[0]["_id"], "email_sends", {"Campaign": existing + [beta_camp_id]})
```

### Step 5 — Trigger the Email Send on Railway

Use `execution/railway.py` to check Railway auth and run the production send script. Railway injects all env vars automatically — no `.env` loading needed.

**Always verify Railway is ready first:**
```python
from execution.railway import check_railway_status
check_railway_status()
# Expected output:
# {'cli_version': '4.30.5', 'logged_in_as': 'ryansossion@gmail.com',
#  'project': 'Email-Send-Service', 'environment': 'production',
#  'service': 'Email-Send-Service', 'ready': True}
```

**Preview (dry_run=True — verifies auth + prints command, does NOT send):**
```python
from execution.railway import trigger_email_send
result = trigger_email_send(dry_run=True)
print(result)  # {"sent": 0, "errors": 0, "dry_run": True, "success": True}
```

**Execute the send (dry_run=False — actually runs railway_email_send.py):**
```python
from execution.railway import trigger_email_send
result = trigger_email_send(dry_run=False)
print(f"Sent={result['sent']} Errors={result['errors']} in {result['elapsed']}")
# Example: Sent=1 Errors=0 in 37.1s
```

Once `trigger_email_send(dry_run=False)` completes:
- Resend has delivered the emails
- Email Logs DB in Notion is updated
- Discord success alert fired automatically (via `send_cron_success` inside `railway_email_send.py`)

You can also run the equivalent terminal command directly:
```bash
cd "C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge"
railway run python scripts/Railway/railway_email_send.py
```

**To verify audience before sending** (overlaps resolution preview):
```python
from execution.leads import preview_assignments
preview_assignments(campaign_id="<id>", min_score=3)
```

**Fallback sanity check when Railway is failing or suspected wrong:**
```bash
python Business/GROWTH/executions/Marketing/run.py --task email-sequences --action sanity-check
python Business/GROWTH/executions/Marketing/run.py --task email-sequences --action sanity-check --email user@example.com
```

This read-only path does not send anything. It verifies:
- which leads are assigned to each active campaign
- which template is next in-sequence for each eligible lead
- whether the lead should send now or is still cooling down on campaign frequency
- how many leads are unassigned, so assignment drift is visible before blaming Railway

### Step 6 — Engagement Score & Segment Reference

The **Engagement Score** automatically accumulates points based on interaction. Use these ranges to filter your assignments (`min_score`):

| Action | Points Earned |
|--------|---------------|
| Email Opened | +1 point |
| Link Clicked | +3 points |
| Email Replied | +10 points |
| Unsubscribed | -100 points |
| Bounced | -5 points |

**Recommended Segment Definitions (Based on Points):**
- **Cold (0–2 pts)**: Zero or minimal interaction (maybe 1-2 opens). Nurture lightly.
- **Warm (3–9 pts)**: Has shown interest (clicked a link, or opened many emails). Target with soft CTAs.
- **Hot (10+ pts)**: Actively engaged (replied to an email, or high multi-click engagement). Ready for hard CTAs.
- **Invalid (< 0 pts)**: Penalized by bounce or unsubscribe. Screened out naturally.

## Operational Lessons

### Subject Line Principles
- **Avoid shock-value clickbait** (e.g. "Epstein files" jokes). They erode trust and trigger spam filters. Email 1's clickbait subject scored only 16% open rate.
- **Pain-point curiosity** outperforms. Subjects that reference the reader's actual problem ("How much have you actually spent on prop firm challenges?") feel personal and drive opens.
- **Spam trigger words to avoid**: "loophole", "free guide", "completely legal", "secret", "act now". Email 4's "loophole" subject caused 8 invisible fails (silently spam-filtered).
- **Best performer**: Email 3 at 40% open ("We want you more than Trump wants Greenland") — bold but non-spammy humour works when it feels on-brand.

### Every Email After Email 1 Must Have a CTA Link
Emails without a link will always show 0% click rate regardless of engagement quality. Email 2 had 37% open rate but 0% clicks because there was no link in the body. After adding one, the template can actually convert openers. Rule: **if it's Email 2 or later, include a plain HTTPS link — chosen from the three approved CTAs in Step 3**.

### Approved CTAs Are Fixed — Do Not Generate New URLs
There are exactly three approved destination URLs. Never write any other domain or path in an email body. If a campaign goal seems to require a different link, raise it for review rather than inventing one:
- `https://hedgedge.info` — homepage / general awareness
- `https://hedgedge.info/guide` — educational soft CTA
- `https://cal.eu/hedgedge/30min` — book a call (hard CTA, high-intent only)
- `https://hedgedge.info/book-demo` — (**deprecated** — redirect page, no longer used)

### Plain URLs Are Auto-Tracked — No Special Syntax Required
The send system (`_resolve_tracked_links` in `email_system.py`) automatically detects all plain `https://` URLs in the template body and converts them to Short.io branded tracked links at send time. Write URLs normally in Notion templates — no `{{track:...}}` wrapper needed. Legacy `{{track:URL}}` markers are still recognised and normalised to plain URLs before processing, so old templates continue to work.

### Template Update Protocol
Always use `update_template()` — never edit Notion blocks directly. The archive protocol preserves:
1. Old email body (as a code block on the archive page)
2. Current metrics snapshot (Open Rate, Click Rate, etc.)

This creates a permanent A/B test record. The Analytics Agent can diff old vs new content against metric changes.

### Batch Lead Assignment Strategy
`assign_leads_by_score()` and `assign_all_segments()` both use a **single bulk DB read** (`_read_leads_full` internal helper) that fetches all lead rows and their current campaign relations in one API call, then filters and writes in Python. This is O(n+1) — one read, n targeted writes — regardless of audience size.

For full segment-routing (Cold/Warm/Hot → their respective campaigns), always prefer `assign_all_segments()` over calling `assign_leads_by_score()` three times separately — it does one DB read instead of three.

### Re-Engagement Targeting
Score = 0 with 3+ emails sent and 0 opens identifies truly disengaged leads. These are distinct from new leads (who also have score 0 but fewer emails). The `total_emails >= 3` check is critical — without it, brand new leads would be incorrectly sent breakup emails.

### Campaign Priority & Audience Conflict Resolution
When a lead qualifies for multiple campaigns simultaneously, the `railway_email_send.py` cron job resolves the conflict using `Campaign Score` (higher = wins) and staggers sends by `Send Frequency`. The canonical hierarchy is:

| Campaign | Score | Send Frequency |
|----------|-------|----------------|
| Hot-lead follow up | 100 | 24 h |
| Re-Engagement | 80 | 72 h |
| Warm Lead Conversion | 70 | 36 h |
| Hedge Awareness | 50 | 48 h |
| Newsletter | 10 | 336 h (2 weeks) |

Never assign the same score to two campaigns — ties break arbitrarily. Always read current scores with `read_campaigns()` before creating or updating.

### Hot Lead Audience Can Silently Empty
Bulk-assignment scripts that overwrite the `Campaign` relation (instead of appending to it) will drop existing campaign links. After any bulk operation, verify the Hot Leads audience with a targeted `query_db("email_sends", filter={"property": "Campaign", "relation": {"contains": HOT_LEAD_ID}})` call. If it returns 0 when eligible leads exist, re-assign using:
```python
from shared.notion_client import query_db, update_row
hot_leads = query_db("email_sends", filter={"property": "Engagement Score", "number": {"greater_than_or_equal_to": 10}})
for l in hot_leads:
    existing = l.get("Campaign") or []
    if HOT_LEAD_ID not in existing:
        update_row(l["_id"], "email_sends", {"Campaign": existing + [HOT_LEAD_ID]})
```
The `_prop_relation` builder in `shared/notion_client.py` accepts a plain list of page-ID strings — pass `existing + [new_id]` to append safely.

### `update_row` Argument Order
`update_row(page_id, db_key, properties)` — page ID comes **first**, db_key second. Swapping them raises `ValueError: Unknown database key`.

### Template Bodies Are NOT Returned by `read_templates()`
`read_templates()` (and `list_templates_for_campaign()`) only return Notion **DB property fields** — name, subject, open rate, sent count, etc. The actual email body is stored as a Notion **code block** *inside* each template page, not as a property. To read a template body directly:
```python
from execution.config import get_notion
client = get_notion()
blocks = client.blocks.children.list(block_id="<template-page-id>")["results"]
for b in blocks:
    if b["type"] == "code":
        body = "".join(t["plain_text"] for t in b["code"]["rich_text"])
        break
```
This is how to scan ALL templates for a specific URL (e.g., to audit or bulk-replace a CTA link) — iterate all template IDs and read their code blocks. `update_template()` handles writing back correctly; never edit code blocks via `client.blocks.update()` directly.

### Railway Execution — Verified Pattern (2026-03-08)
The full end-to-end send via Railway CLI was confirmed working with this sequence:
1. `railway whoami` — confirm logged in as `ryansossion@gmail.com`
2. `railway status` — confirm project `Email-Send-Service / production` is linked
3. `railway run python scripts/Railway/railway_email_send.py` — Railway injects all env vars; output line: `[Done] Sent=1 Errors=0 in 37.1s`
4. Discord success alert fires automatically from within the script

Key facts:
- **CWD must be the workspace root** (`C:\Users\sossi\Desktop\Business\Orchestrator Hedge Edge`) — the paths in `railway_email_send.py` resolve relative to it.
- **Railway CLI version**: `4.30.5` (confirmed working)
- **Timeout**: the full send run takes ~37s for 1 email; allow 180s for larger queues.
- **`NOTION_TOKEN` fallback**: `railway_email_send.py` accepts either `NOTION_API_KEY` or `NOTION_TOKEN` — both Railway env vars are supported.
- Use `execution/railway.py` → `trigger_email_send(dry_run=False)` instead of raw `subprocess` — it validates auth, parses output, and returns structured results.

### New Script `_ws_root` Depth Rule (5 dirname calls)

All scripts in `agents/GROWTH/Marketing Agent/scripts/` sit **5 directory levels below** `IDE 1/` — where the `shared/` module lives:

```
scripts/ → Marketing Agent/ → GROWTH/ → agents/ → IDE 1/
   1            2                3          4          5
```

Any new script in this directory **must** use exactly 5 `os.path.dirname()` calls:

```python
import os, sys
_ws_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, _ws_root)
from shared.notion_client import query_db
```

Using 2 calls (a common mistake) resolves to `Marketing Agent/` — which contains no `shared/` module — causing `ModuleNotFoundError: No module named 'shared'` on import.

**Symptom**: `ModuleNotFoundError: No module named 'shared'` when running any Marketing Agent script.  
**Diagnosis**: Print `_ws_root` and confirm it ends with `IDE 1`.  
**Fix**: Count dirname depth — from `__file__` up to `IDE 1/` is exactly 5 levels.

### Notion API Timeout Behaviour (Production Incident 2026-03-17)

Notion API response times can spike to **8–15+ seconds** under load. The `email_sends` DB full read typically takes 3–8s; under Notion degradation it exceeds the old 15s limit, crashing the Railway crons with:

```
ReadTimeoutError: HTTPSConnectionPool(host='api.notion.com', port=443): Read timed out. (read timeout=15)
```

**Three `[CRITICAL]` alert emails were sent on 2026-03-17 at 09:01, 09:05, and 21:01 UTC — same root cause.**

**Current configuration (post-fix):**

| File | Setting | Value |
|------|---------|-------|
| `shared/notion_client.py` | default `timeout` | 30s (was 15s) |
| `scripts/Railway/email_send.py` | `query_db_raw()` + `load_template_body()` | 45s (was 15s) |
| `notion_client.py` | `ReadTimeout` + `ConnectionError` auto-retry | 5× with 1/2/4/8s backoff |

**If this error recurs**, verify:
1. `shared/notion_client.py` — `timeout: int = 30` in function signature and `ReadTimeout` in the retry `except` clause
2. `scripts/Railway/email_send.py` — both hardcoded `timeout=15` raised to `timeout=45`
3. Notion status page (`status.notion.so`) — if Notion is degraded, all agents with Notion calls will slow down


### New Script `_ws_root` Depth Rule (5 dirname calls)

All scripts in `agents/GROWTH/Marketing Agent/scripts/` sit **5 directory levels below** `IDE 1/` — where the `shared/` module lives:

```
scripts/ → Marketing Agent/ → GROWTH/ → agents/ → IDE 1/
   1            2                3          4          5
```

Any new script in this directory **must** use exactly 5 `os.path.dirname()` calls:

```python
import os, sys
_ws_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, _ws_root)
from shared.notion_client import query_db
```

Using 2 calls (a common mistake) resolves to `Marketing Agent/` — which contains no `shared/` module — causing `ModuleNotFoundError: No module named 'shared'` on import.

**Symptom**: `ModuleNotFoundError: No module named 'shared'` when running any Marketing Agent script.  
**Diagnosis**: Print `_ws_root` and confirm it ends with `IDE 1`.  
**Fix**: Count dirname depth — from `__file__` up to `IDE 1/` is exactly 5 levels.

### Notion API Timeout Behaviour (Production Incident 2026-03-17)

Notion API response times can spike to **8–15+ seconds** under load. The `email_sends` DB full read typically takes 3–8s; under Notion degradation it exceeds the old 15s limit, crashing the Railway crons with:

```
ReadTimeoutError: HTTPSConnectionPool(host='api.notion.com', port=443): Read timed out. (read timeout=15)
```

**Three `[CRITICAL]` alert emails were sent on 2026-03-17 at 09:01, 09:05, and 21:01 UTC — same root cause.**

**Current configuration (post-fix):**

| File | Setting | Value |
|------|---------|-------|
| `shared/notion_client.py` | default `timeout` | 30s (was 15s) |
| `scripts/Railway/email_send.py` | `query_db_raw()` + `load_template_body()` | 45s (was 15s) |
| `notion_client.py` | `ReadTimeout` + `ConnectionError` auto-retry | 5× with 1/2/4/8s backoff |

**If this error recurs**, verify:
1. `shared/notion_client.py` — `timeout: int = 30` in function signature and `ReadTimeout` in the retry `except` clause
2. `scripts/Railway/email_send.py` — both hardcoded `timeout=15` raised to `timeout=45`
3. Notion status page (`status.notion.so`) — if Notion is degraded, all agents with Notion calls will slow down


### CRM Hygiene — Dead Lead Eviction (Routine)

**Run this after every send cycle or at minimum weekly.** Leads that have received 5+ emails with an Engagement Score of 0 are confirmed dead — they never opened, clicked, or replied. Keeping them inflates audience counts, drags down open/click rates, and wastes Resend credits.

**Two eviction tiers — both run every time `evict_dead_leads()` is called:**

| Tier | Rule | Threshold |
|------|------|-----------|
| **Rule 1 — Never opened** | `Total Emails >= 5` AND `score == 0` | 5 emails, zero engagement ever |
| **Rule 2 — Went cold** | `Total Opens >= 1` AND `Total Clicks == 0` AND `Total Replies == 0` AND `(Total Emails − Total Opens) >= 7` | Opened once, then silent for 7+ more emails (~12-13 total) |

Archived leads are soft-deleted (Notion trash, recoverable for 30 days). This is not a hard delete.

**Preview first (always dry_run=True):**
```python
from execution.leads import evict_dead_leads

# Preview — shows who would be evicted, writes nothing
result = evict_dead_leads(dry_run=True)  # min_emails=5, cold_window=7
print(f"{result['evicted']} dead leads would be evicted")
print(f"  Rule 1 (never opened):  {result['evicted_rule1']}")
print(f"  Rule 2 (went cold):     {result['evicted_rule2']}")
for lead in result['preview']:
    print(f"  {lead['email']}  emails={lead['total_emails']}  score={lead['score']}")
```

**Execute eviction:**
```python
from execution.leads import evict_dead_leads

result = evict_dead_leads(dry_run=False)
print(f"Evicted {result['evicted']} (R1={result['evicted_rule1']}, R2={result['evicted_rule2']}). Errors: {result['errors']}")
```

**Routine schedule** — integrate into the post-send workflow:

| When | Action |
|------|--------|
| After every Railway send run | Run `evict_dead_leads(dry_run=True)` to preview |
| Weekly (minimum) | Run `evict_dead_leads(dry_run=False)` to clean the CRM |
| Before major campaign launches | Preview eviction to ensure audience counts are realistic |

**What qualifies as a dead lead:**

- **Rule 1 — Never opened:** Received **5+** emails with score **= 0** (never opened, clicked, or replied). Given a fair chance, showed zero interest.
- **Rule 2 — Went cold:** Opened **at least once** (showed initial interest) but never clicked or replied, and received **7 or more** emails beyond their total open count. Typically triggers around email 12–13 total.

**What does NOT get evicted:**
- New leads with < 5 emails (Rule 1 hasn't triggered yet)
- Leads with any clicks or replies (still worth nurturing)
- Leads where `(Total Emails − Total Opens) < 7` (Rule 2 hasn't triggered yet)
- Unsubscribed leads (already excluded from sends)

**Adjustable thresholds:**
```python
# Tighten Rule 1: evict after 3 emails with zero engagement
evict_dead_leads(min_emails=3, cold_window=7, dry_run=False)

# Loosen Rule 2: require 10 cold emails before eviction
evict_dead_leads(min_emails=5, cold_window=10, dry_run=False)
```

A Discord/email alert is sent automatically on each eviction run via `send_alert()`.


### CRM Removal — Targeted Lead Archival

Three dedicated functions for removing leads beyond the automated dead-lead eviction above. All use Notion soft-delete (recoverable for 30 days). All default to `dry_run=True`.

#### Remove Specific Leads by Email

Use when you have a known list of emails to purge (e.g. spam signups, test accounts, opt-out requests via channels other than the unsub link).

```python
from execution.leads import remove_leads_by_email

# Single email
result = remove_leads_by_email("spam@example.com", dry_run=True)
print(result)  # {'removed': 1, 'not_found': [], 'preview': [...], 'errors': 0}

# Multiple emails
result = remove_leads_by_email([
    "test1@example.com",
    "test2@example.com",
    "fake@noreply.com",
], dry_run=False)
print(f"Removed {result['removed']}, not found: {result['not_found']}")
```

#### Remove Leads by Filter

Use for bulk cleanup based on CRM properties. Filters are AND-combined — a lead must match **all** specified criteria. At least one filter is required (prevents accidental mass deletion).

```python
from execution.leads import remove_leads_by_filter

# Remove all bounced Cold leads
result = remove_leads_by_filter(
    bounced_only=True,
    segment="Cold",
    dry_run=True,
)
print(f"{result['removed']} bounced Cold leads would be archived")
for lead in result['preview']:
    print(f"  {lead['email']}  score={lead['score']}  emails={lead['total_emails']}")

# Remove leads from a bad source that scored zero
result = remove_leads_by_filter(
    source="scraped-list",
    max_score=0,
    dry_run=False,
)

# Remove leads with score <= 0 who've had at least 3 emails
result = remove_leads_by_filter(
    max_score=0,
    min_emails=3,
    dry_run=False,
)
```

**Available filters:**

| Filter | Type | Effect |
|--------|------|--------|
| `max_score` | int | Score <= value |
| `min_emails` | int | Total Emails >= value |
| `max_emails` | int | Total Emails <= value |
| `bounced_only` | bool | Only leads with Total Bounced > 0 |
| `source` | str | Case-insensitive match on Source field |
| `segment` | str | `'Cold'`, `'Warm'`, or `'Hot'` |

#### Remove Duplicate Leads

Scans all CRM rows, groups by email, and archives every duplicate (keeps the earliest row). Run periodically or after bulk ingests.

```python
from execution.leads import remove_duplicate_leads

# Preview duplicates
result = remove_duplicate_leads(dry_run=True)
print(f"{result['duplicates']} duplicate rows found")
for email, page_id in result['preview']:
    print(f"  {email} → {page_id}")

# Execute dedup
result = remove_duplicate_leads(dry_run=False)
print(f"Archived {result['duplicates']} duplicates. Errors: {result['errors']}")
```

#### Safety Rules for All Removal Functions

- **Always `dry_run=True` first** — preview before committing.
- All removals are **Notion soft-deletes** — recoverable from trash for 30 days.
- Every execution run fires a **Discord/email alert** via `send_alert()` with counts.
- `remove_leads_by_filter()` **requires at least one filter** — calling with no filters raises `ValueError`.
- Unsubscribed leads are excluded from filter-based removal (they're already handled by the unsub system).


## Legal & FCA Compliance Gate

**Any email containing financial claims, ROI references, past performance data, broker links, or IB disclosures must be reviewed by the Legal Agent before scheduling.**

Mandatory triggers — route to Legal Agent (`fca-scan` skill) before `send_execute`:
- Email contains "ROI", "%", "profit", "pass rate", "challenge", "28x", or any performance metric
- Email links to a broker partner (Vantage, BlackBull) — IB disclosure must be present
- Email is promoting a new pricing tier with value claims ("save X", "earn Y")
- Email is targeting a new geography (US, AU, EU — different disclaimer requirements)

**Required disclaimer language** (from `agents/STRATEGY/.agents/skills/legal-compliance/resources/risk-disclaimers.md`):
- Capital risk disclaimer must appear in all emails with financial context
- IB disclosure required in any email with broker affiliate links
- Past performance disclaimer if any historical results are referenced

**Workflow**:
1. Marketing Agent drafts email copy
2. Marketing passes copy to Legal Agent via `fca-scan` execution script
3. Legal returns: PASS (proceed), PASS_WITH_EDITS (apply redlines then proceed), or FAIL (do not send — escalate)
4. Only after Legal PASS does `send_execute` or `trigger_railway_send` proceed

## Constraints

- **Never hard-delete** campaigns or templates — use pause instead.
- **Dead lead eviction** is the one exception: leads with >= 5 emails and Engagement Score = 0 are archived (Notion soft-delete, recoverable for 30 days). Run `evict_dead_leads()` routinely.
- **Always dry_run=True first** for lead assignment, eviction, and send operations. For Railway triggers, call `trigger_email_send(dry_run=True)` before `dry_run=False`.
- `email_sends` (leads) is read-only for all fields except the Campaign relation.
- **Railway sends require explicit approval** — `trigger_email_send(dry_run=False)` actually delivers emails via Resend. Do not execute without user confirmation.
