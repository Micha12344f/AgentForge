# Marketing Resources

> Reference material for the Growth Marketing sub-department.

## Marketing Stack

| Tool | Purpose | Integration |
|------|---------|------------|
| Resend | Email delivery | `shared/resend_client.py` |
| Notion | Campaign management | `shared/notion_client.py` |
| Short.io | Link tracking | `shared/shortio_client.py` |
| GA4 | Web analytics | `shared/google_analytics_client.py` |
| LinkedIn | Social outreach | marketing publishing scripts |
| Twitter/X | Social content | Marketing X automation scripts |
| Discord | Community | `shared/discord_client.py` |
| Vercel | Landing page hosting | landing page deploy workflow |

## X/Twitter System

X is the primary awareness channel for Hedge Edge.

| Asset | Purpose |
|------|---------|
| `executions/Marketing/auto_tweet.py` | Automated TOFU/MOFU queue posting |
| `executions/Marketing/x_manager.py` | Validated posting, deletion, and resume flows |
| `directives/Marketing/x-management.md` | Operating procedure and safety rules |
| `resources/Marketing/x-strategy.md` | Channel positioning, content mix, and cadence |

## Key Notion Databases

| DB Key | Purpose |
|--------|---------|
| `campaigns` | Campaign management |
| `email_sequences` | Drip sequence templates |
| `email_sends` | Per-lead send records |
| `leads_crm` | Lead records used by campaigns and segmentation |