---
name: license-tracking-analytics
description: |
  Reads and summarizes the Hedge Edge license telemetry tables in Supabase
  to produce customer-health views for activation, last activity, cadence,
  device fleet, and validation failures.
---

# License Tracking Analytics

## Purpose

This directive turns the live license telemetry schema into an operational
analytics workflow for customer support, onboarding, and churn prevention.
It assumes each customer has a unique license key. Shared keys pollute the
activation, cadence, device, and error signals.

## Data Sources

| Table | What It Tells Us |
|------|-------------------|
| `licenses` | License owner, plan tier, active status, expiry, device cap |
| `license_validation_logs` | Successful and failed validation attempts, activation evidence, cadence, error codes |
| `license_devices` | Active device fleet, platform, broker, account, last heartbeat |

## Core Signals

1. License registry: key, email, plan, status, expiry
2. Activation check: first successful validation per key
3. **Platform Activation check: first successful validation with `platform ∈ {mt5, mt4, ctrader}` + persistent device row (see `platform-activation-indicator.md`) — this is the ULTIMATE CONVERSION INDICATOR**
4. Last active: most recent `license_devices.last_seen_at`
5. Usage cadence: distinct active days across a rolling window
6. Device fleet: platform, broker, account, version per active device
7. Error signals: failed validations grouped by key and error code
8. Customer health: unified support-facing status per customer (must incorporate Platform Activation status)

## Health Logic

| Condition | Health label | Meaning |
|----------|--------------|---------|
| `activated_at == NEVER` | `NOT ACTIVATED` | User has a key but has never opened the app |
| `platform_activated == false` AND `days_since_key > 7` | `NEEDS_ONBOARDING_HELP` | Desktop opened but EA never connected to chart — highest-priority onboarding gap |
| `platform_activated == true` AND `days_since_last_active > 7` | `CHURNING` | Was platform-activated but has gone stale |
| `errors_30d > 10` | `NEEDS SUPPORT` | Repeated failures indicate setup or product friction |
| `platform_activated == true` AND `days_active_30d >= 5` | `HEALTHY` | Customer is using the product on a trading platform regularly |
| `platform_activated == true` AND `days_active_30d >= 1` | `WARMING UP` | Platform-activated but not yet habitual |
| `platform_activated == false` AND has desktop validations | `DESKTOP_ONLY` | App opened but EA not connected — not truly converted |
| otherwise | `DORMANT` | No successful activity in the window |

> **Critical distinction**: A user with only `desktop` or `unknown` validations is `DESKTOP_ONLY`, not `HEALTHY`. Platform Activation (`mt5`/`mt4`/`ctrader` with persistent device) is the true conversion gate. See `platform-activation-indicator.md`.

## Execution Scripts

| File | Purpose |
|------|---------|
| `executions/license_tracking_report.py` | Live Supabase report generator for registry, cadence, fleet, errors, and health |
| `executions/test_license_tracking_e2e.py` | End-to-end validator for the live license tracking pipeline |

## Run Commands

```bash
python Business/ANALYTICS/executions/run.py --task license-track --action summary
python Business/ANALYTICS/executions/run.py --task license-track --action dashboard
python Business/ANALYTICS/executions/run.py --task license-track --action fleet --days 30
python Business/ANALYTICS/executions/run.py --task license-track --action errors --days 30
python Business/ANALYTICS/executions/run.py --task license-track --action export-json --days 30
python Business/ANALYTICS/executions/test_license_tracking_e2e.py
```

## Operational Use

- Use `summary` for quick support snapshots and leadership checks.
- Use `dashboard` to review customer health before outreach.
- Use `errors` to find customers who need proactive help.
- Use `fleet` to inspect what a customer is actually running.
- Use `export-json` when another script or notebook needs the computed output.

## Notebook Reference

The canonical exploration notebook is:

`resources/09_License_Tracking_E2E.ipynb`

Use the notebook for exploration and schema validation. Use the execution
script for repeatable reporting and orchestration.

## Insights & Improvements Requirement

Every license tracking report must end with:
1. **Insights** — Identify customers at risk (CHURNING, NEEDS SUPPORT), activation trends, device fleet health.
2. **Improvements** — Proactive outreach recommendations for at-risk customers, onboarding friction points to fix, tagged with owning department (`→ @growth`, `→ @strategy`).

See SKILL.md §11 for the full SOP.