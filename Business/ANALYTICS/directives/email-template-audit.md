---
name: email-template-audit
description: |
  Pulls the complete Hedge Edge email template inventory from Notion, including
  template body content blocks and full per-template performance metrics, then
  packages the result into a human-readable audit for copy analysis and
  refurbishment planning.
---

# Email Template Audit

## Purpose

This directive exists for cases where campaign-level rollups are not enough.
Use it when the user needs:

- every live email template body,
- the subject line and full performance metrics for each template,
- content-level interpretation of what drives opens, clicks, replies, and drop-off,
- a markdown-ready archive that Growth can use for refurbishment.

This is broader than `email-marketing-analytics.md`. That directive surfaces raw metrics.
This directive combines raw metrics with the actual template copy stored on the Notion page.

Operational note:

- Audit implementations must be written against live `email_sequences` rows and Notion block content, not legacy skill-local reader paths.

---

## Execution Script

Primary script:

- `Business/ANALYTICS/executions/email_template_audit.py`

Supporting readers:

- `shared.notion_client.query_db("email_sequences")` for template rows and rollup metrics
- `shared.notion_client.get_notion()` for retrieving Notion page blocks
- `Business/GROWTH/executions/Marketing/email_marketing/templates.py` for the operational template model used elsewhere in the workspace

---

## What To Pull

For every template in `email_sequences`, capture:

- template name
- subject line
- send, delivery, open, click, bounce, and reply counts
- open, click, bounce, and reply rates
- delivery rate
- invisible fail count
- full email body from Notion child blocks

The email body may live in:

- `code` blocks
- `paragraph` blocks
- headings
- list items
- quotes
- callouts

The audit should concatenate readable text blocks in order so the final output reflects the actual email copy.

---

## Required Outputs

Every template audit should produce:

1. A complete per-template inventory.
2. A per-template content diagnosis.
3. A cross-template pattern summary.
4. Insights and Improvements at the end, per Analytics SOP.

Recommended formats:

- `--action markdown` for a user-facing archive
- `--action json` for raw export
- `--action summary` for quick terminal review

---

## Interpretation Rules

- Do not judge templates with zero sends as performance failures; assess them structurally only.
- Treat very low-volume hot lead or beta templates as directional signals, not definitive truth.
- If a template has strong opens but weak clicks, inspect CTA clarity and number of asks.
- If a template has weak opens but healthy deliverability, inspect subject line novelty and sender framing.
- If a template has invisible fails, note possible deliverability/content-trigger issues.

---

## Insights & Improvements Requirement

Every audit must end with:

## Insights
- What the metrics reveal about subject lines, tone, CTA style, sequence stage, and copy structure.

## Improvements
- Concrete, template-level recommendations backed by the numbers.
- Tag the owner as `→ @growth` when the action is copy or sequencing related.
