# ANALYTICS — Skill Command Sheet

> **Adopt this department to gain**: Data measurement, KPI tracking, attribution auditing, funnel analysis, and reporting skills across every Hedge Edge touchpoint.

> **Governance note**: Analytics owns analytics content. Orchestrator alone owns cross-department DOE restructuring and any `SKILL.md` rewrite that changes folder-role mapping or explains what folders now do.

---

## Skills You Gain

When you adopt the Analytics department, you can execute the following skills by combining directives (what to do), executions (how to do it), and resources (reference material).

### Skill 1 — KPI Measurement & Snapshots
- **Directive**: `directives/kpi-framework.md` — defines every KPI, its target, and alert threshold
- **Executions**: `executions/kpi_snapshot.py` (point-in-time snapshot), `executions/daily_analytics.py` (daily rollup), `executions/hourly_metrics_sync.py` (hourly sync to Notion/Supabase)
- **Resource**: `resources/dashboard-layout.md` — dashboard wireframes and metric placement

### Skill 2 — Attribution Auditing
- **Directive**: `directives/attribution-tracking.md` — UTM attribution pipeline, referrer normalisation
- **Executions**: `executions/attribution_audit.py` (audit pipeline integrity), `executions/attribution_modeler.py` (model attribution weights)

### Skill 3 — Email Campaign Analytics
- **Directive**: `directives/email-analytics.md` — email campaign metrics and deliverability tracking
- **Executions**: `executions/conversion_tracker.py` (conversion events), `executions/email_template_audit.py` (template performance), `executions/beta_email_parser.py` (parse beta email logs)
- **Related**: `directives/email-marketing-analytics.md`, `directives/email-template-audit.md`

### Skill 4 — Web & GA4 Analytics
- **Directive**: `directives/web-analytics.md` — GA4 setup, pageview/event/conversion tracking
- **Execution**: `executions/web_analytics/ga4_config.py` — GA4 property configuration

### Skill 5 — Funnel Reporting
- **Directive**: `directives/funnel-reporting.md` — full-funnel conversion reporting
- **Executions**: `executions/funnel_calculator.py` (calculate funnel metrics), `executions/daily_analytics.py` (include funnel data in daily snapshots)

### Skill 6 — License & Subscription Tracking
- **Directive**: `directives/license-tracking-analytics.md` — license lifecycle tracking
- **Executions**: `executions/license_tracking_report.py` (generate report), `executions/test_license_tracking_e2e.py` (E2E test)
- **Resource**: `resources/09_License_Tracking_E2E.ipynb` — interactive license tracking notebook

### Skill 7 — Data Pipeline Management
- **Directive**: `directives/data-pipeline.md` — data sync schedules, pipeline architecture
- **Execution**: `executions/hourly_metrics_sync.py` — scheduled sync across Notion, Supabase, GA4

### Skill 8 — A/B Testing & Experimentation
- **Execution**: `executions/ab_test_manager.py` — manage A/B test configurations and analyse results

### Skill 9 — Reporting & Automation
- **Executions**: `executions/report_automator.py` (automated report generation), `executions/pdf_link_stats.py` (PDF link click stats), `executions/cohort_analyzer.py` (cohort retention analysis)

---

## Dispatcher

`executions/run.py` — routes `--task` flags to the correct execution script. Entry point for all Analytics tasks.

## Shared Dependencies

All execution scripts import from the workspace-root `shared/` package. The analytics runtime currently depends on:

- `notion_client.py` — Notion database reads/writes, schema-aware updates, task logging
- `supabase_client.py` — profiles, subscriptions, attribution, page_views, license telemetry
- `google_analytics_client.py` — GA4 Data API reports and Measurement Protocol helpers
- `resend_client.py` — email sends, audiences, contacts, webhook utilities
- `shortio_client.py` — link inventory and click statistics
- `creem_client.py` — subscription status and billing feed pulls
- `alerting.py` — Discord alert routing for KPI and pipeline failures
- `llm_router.py`, `groq_client.py`, `gemini_client.py`, `openrouter_client.py` — AI narrative generation for KPI/report summaries
- `api_registry.py`, `retry_executor.py` — dispatcher readiness checks and resilient execution

Related cross-department dependency:

- `Business/GROWTH/executions/Marketing/email_marketing/email_system.py` exports `enrich_notion_from_resend()` for analytics-side email enrichment during daily/hourly rollups.

Operational note:

- Analytics scripts should include a Windows-safe UTF-8 stdout/stderr reconfiguration guard to avoid `UnicodeEncodeError` on cp1252 terminals.

## Cross-Department Links

| Department | Analytics Provides | Analytics Needs |
|------------|-------------------|-----------------|
| GROWTH | Campaign metrics, attribution data, funnel reports | Campaign IDs, UTM parameters |
| FINANCE | MRR data, subscription metrics | Revenue events from Creem.io |
| STRATEGY | KPI scorecards, market intelligence | Strategic KPI targets |
| ORCHESTRATOR | Pipeline health metrics | Cron schedule configs |

## 6. Run Commands

```bash
# Daily KPI snapshot
python Business/ANALYTICS/executions/daily_analytics.py

# Hourly metrics sync
python Business/ANALYTICS/executions/hourly_metrics_sync.py

# Attribution audit
python Business/ANALYTICS/executions/attribution_audit.py

# Conversion tracking
python Business/ANALYTICS/executions/conversion_tracker.py
```
