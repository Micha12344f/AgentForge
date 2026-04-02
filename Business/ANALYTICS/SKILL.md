---
name: analytics
description: "Strategic analytics operating sheet for Hedge Edge. Prefer GA4, Supabase, Resend, and Creem as direct sources; use Notion mirrors only for maintenance or explicit mirror requests."
---

# ANALYTICS — Skill Command Sheet

> **Adopt this department to gain**: direct-source KPI measurement, attribution auditing, funnel analysis, email analytics, platform activation tracking, and strategic reporting across every Hedge Edge touchpoint.

> **Governance**: Analytics owns analytics content. Orchestrator alone owns cross-department DOE restructuring.

---

## Strategic Operating Order

1. **Traffic and engagement** → GA4 first, Supabase `page_views` only as fallback
2. **Signups and attribution** → Supabase `user_attribution`
3. **Activation and license health** → Supabase `license_validation_logs` + `license_devices`
4. **Email delivery and audience health** → Resend
5. **Revenue and subscriptions** → Creem
6. **Notion** → mirror/dashboard sink only, never the default source for analytical reports

### Default Rule

- If the request says `report`, `weekly report`, `7-day report`, `analytical report`, `executive briefing`, or `business report`, use the strategic report path first.
- Use `kpi-snapshot` or `notion-report` only when the user explicitly asks for mirrored Notion data, dashboard-state verification, or Notion sync maintenance.
- Never use GA4 `sign_up` as a conversion count. Conversions come from Supabase.
- Platform Activation is the ultimate conversion metric. Desktop app opens do not count.

---

## Dispatcher

All tasks route through `executions/run.py`:

```bash
python Business/ANALYTICS/executions/run.py --list-tasks
python Business/ANALYTICS/executions/run.py --status
python Business/ANALYTICS/executions/run.py --task <TASK> --action <ACTION>
```

Preferred report entry points:

```bash
python Business/ANALYTICS/executions/run.py --task report --action daily
python Business/ANALYTICS/executions/run.py --task report --action weekly
python Business/ANALYTICS/executions/run.py --task report --action monthly
python Business/ANALYTICS/executions/run.py --task notion-report --action weekly  # only if user explicitly wants Notion-mirrored data
```

---

## Skills

### 1 — Strategic Reports & Recommendations
| Layer | Path |
|-------|------|
| Directives | `directives/kpi-framework.md` `directives/ga4-analytics.md` `directives/platform-activation-indicator.md` |
| Executions | `executions/strategic_report.py` `executions/conversion_tracker.py` `executions/license_tracking_report.py` |
| Use for | Direct-source daily, weekly, monthly, and 7-day analytical reports |

```bash
python Business/ANALYTICS/executions/strategic_report.py --action daily
python Business/ANALYTICS/executions/strategic_report.py --action weekly
python Business/ANALYTICS/executions/strategic_report.py --action monthly
python Business/ANALYTICS/executions/strategic_report.py --action weekly --days 14
```

### 2 — KPI Snapshot Maintenance (Notion Mirror)
| Layer | Path |
|-------|------|
| Directive | `directives/kpi-framework.md` |
| Executions | `executions/kpi_snapshot.py` `executions/daily_analytics.py` `executions/hourly_metrics_sync.py` |
| Resource | `resources/dashboard-layout.md` |

Use this skill when the user explicitly wants mirrored dashboard state, Notion maintenance, or snapshot verification.

```bash
python Business/ANALYTICS/executions/kpi_snapshot.py --action latest
python Business/ANALYTICS/executions/kpi_snapshot.py --action daily-report
python Business/ANALYTICS/executions/kpi_snapshot.py --action weekly-report
python Business/ANALYTICS/executions/daily_analytics.py
python Business/ANALYTICS/executions/hourly_metrics_sync.py
```

### 3 — Attribution Auditing
| Layer | Path |
|-------|------|
| Directive | `directives/attribution-tracking.md` |
| Executions | `executions/attribution_audit.py` `executions/attribution_modeler.py` |

```bash
python Business/ANALYTICS/executions/attribution_audit.py
python Business/ANALYTICS/executions/attribution_modeler.py --action first-touch
python Business/ANALYTICS/executions/attribution_modeler.py --action last-touch
python Business/ANALYTICS/executions/attribution_modeler.py --action linear
python Business/ANALYTICS/executions/attribution_modeler.py --action summary
```

### 4 — Email Campaign Analytics
| Layer | Path |
|-------|------|
| Directives | `directives/email-analytics.md` `directives/email-marketing-analytics.md` `directives/email-template-audit.md` |
| Executions | `executions/beta_email_parser.py` `executions/email_template_audit.py` `executions/email_analytics/report.py` |
| Source order | Resend first for sends and audience health, Notion only for template/body audits |

```bash
python Business/ANALYTICS/executions/beta_email_parser.py --action scan
python Business/ANALYTICS/executions/beta_email_parser.py --action cross-check
python Business/ANALYTICS/executions/beta_email_parser.py --action hot-leads
python Business/ANALYTICS/executions/email_template_audit.py --action summary
python Business/ANALYTICS/executions/email_template_audit.py --action json
```

### 5 — Web & GA4 Analytics
| Layer | Path |
|-------|------|
| Directives | `directives/web-analytics.md` `directives/ga4-analytics.md` |
| Execution | `executions/web_analytics/ga4_config.py` |

Credential rule: set `GOOGLE_SERVICE_ACCOUNT_JSON=ga4-key.json` in `.env` and keep the JSON file in the workspace root. Do not embed multiline service-account JSON in `.env`.

### 6 — Funnel Reporting
| Layer | Path |
|-------|------|
| Directive | `directives/funnel-reporting.md` |
| Executions | `executions/funnel_calculator.py` `executions/conversion_tracker.py` |

```bash
python Business/ANALYTICS/executions/funnel_calculator.py --action snapshot
python Business/ANALYTICS/executions/funnel_calculator.py --action email-funnel
python Business/ANALYTICS/executions/funnel_calculator.py --action signup-funnel
```

Note: the email funnel uses cumulative counting. A lead with status `clicked` is also counted in delivered and opened.

### 7 — License Tracking & Platform Activation
| Layer | Path |
|-------|------|
| Directives | `directives/license-tracking-analytics.md` `directives/platform-activation-indicator.md` |
| Executions | `executions/license_tracking_report.py` `executions/conversion_tracker.py` `executions/test_license_tracking_e2e.py` |
| Resource | `resources/09_License_Tracking_E2E.ipynb` |

```bash
python Business/ANALYTICS/executions/license_tracking_report.py --action summary
python Business/ANALYTICS/executions/license_tracking_report.py --action dashboard --days 30
python Business/ANALYTICS/executions/license_tracking_report.py --action errors --days 30
python Business/ANALYTICS/executions/conversion_tracker.py --action activation-check
python Business/ANALYTICS/executions/conversion_tracker.py --action activation-check --email user@example.com
python Business/ANALYTICS/executions/test_license_tracking_e2e.py
```

Health labels: `HEALTHY`, `WARMING UP`, `NOT ACTIVATED`, `NEEDS_ONBOARDING_HELP`, `DESKTOP_ONLY`, `NEEDS SUPPORT`, `CHURNING`, `DORMANT`.

### 8 — Data Pipeline Management
| Layer | Path |
|-------|------|
| Directive | `directives/data-pipeline.md` |
| Execution | `executions/hourly_metrics_sync.py` |

The hourly sync collects from GA4, Resend, Supabase, Creem, and Short.io, then upserts into Notion mirrors such as `kpi_snapshots`, `funnel_metrics`, `email_sends`, `email_sequences`, `link_tracking`, `mrr_tracker`, and `campaigns`. It is infrastructure, not the default reporting source.

### 9 — A/B Testing & Experimentation
| Layer | Path |
|-------|------|
| Execution | `executions/ab_test_manager.py` |

```bash
python Business/ANALYTICS/executions/ab_test_manager.py --action list
python Business/ANALYTICS/executions/ab_test_manager.py --action create --name "Homepage CTA v2"
python Business/ANALYTICS/executions/ab_test_manager.py --action analyze --name "Homepage CTA v2"
```

### 10 — Legacy Notion Reporting & Mirror Checks
| Layer | Path |
|-------|------|
| Executions | `executions/report_automator.py` `executions/kpi_snapshot.py` `executions/cohort_analyzer.py` `executions/pdf_link_stats.py` |
| Use for | Explicit Notion-backed reports, mirror QA, or legacy automation only |

```bash
python Business/ANALYTICS/executions/report_automator.py --action daily
python Business/ANALYTICS/executions/report_automator.py --action weekly
python Business/ANALYTICS/executions/report_automator.py --action monthly
python Business/ANALYTICS/executions/cohort_analyzer.py --action summary
python Business/ANALYTICS/executions/pdf_link_stats.py
```

---

## Shared Dependencies

All scripts import from the workspace-root `shared/` package:

| Client | Purpose |
|--------|---------|
| `google_analytics_client.py` | GA4 traffic and engagement reporting |
| `supabase_client.py` | Signups, attribution, page views, license telemetry |
| `resend_client.py` | Email sends, audiences, contacts |
| `creem_client.py` | Subscription state and billing feed |
| `notion_client.py` | Mirror writes, dashboard reads, task logging |
| `shortio_client.py` | Link inventory and click stats |
| `alerting.py` | Discord alert routing |
| `llm_router.py` | AI narrative generation when explicitly needed |
| `api_registry.py` `retry_executor.py` | Readiness checks and resilient execution |

Cross-department: `Business/GROWTH/executions/Marketing/email_marketing/email_system.py` exports `enrich_notion_from_resend()` for email enrichment during mirror syncs.

### Runtime Rules

- All scripts include a Windows-safe UTF-8 stdout/stderr guard for cp1252 terminals.
- Use the workspace `.venv` for analytics executions. `executions/run.py` and `executions/strategic_report.py` auto-bootstrap into it when they detect a different interpreter.
- For analytical reports, prefer direct sources. Do not silently replace a direct source with Notion mirror data.
- If a direct source is unavailable, return a partial report and list the gap explicitly.
- All Notion API calls must use `notion_request()` (rate-limited), never raw `requests`.
- All `log_task()` calls use signature: `log_task(agent, task, status="Complete", priority="P2")`.
- If a Notion database suddenly returns 404, validate `.env` parsing before assuming the database ID is wrong.
- If `GET /databases/{id}` returns 200 but `POST /databases/{id}/query` returns 404, the database is usually archived or in trash. Restore it in Notion or update `shared/notion_client.py` `DATABASES` before rerunning mirror-maintenance tasks.

---

## Cross-Department Links

| Department | Analytics Provides | Analytics Needs |
|------------|-------------------|-----------------|
| GROWTH | Traffic, attribution, funnel reports, Platform Activation status | Campaign IDs, UTM params |
| FINANCE | Subscription and revenue state | Billing events from Creem |
| STRATEGY | KPI scorecards, Platform Activation Rate, strategic diagnostics | KPI targets and product priorities |
| ORCHESTRATOR | Pipeline health metrics and direct-source report outputs | Cron schedule configs |
