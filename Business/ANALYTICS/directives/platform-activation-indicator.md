# Platform Activation Indicator — Ultimate Conversion Metric

> **Owner**: ANALYTICS  
> **Referenced by**: GROWTH (Sales onboarding, lead qualification), STRATEGY (Product, platform integration)  
> **Source of truth**: Supabase `license_validation_logs` + `license_devices`

---

## Purpose

Platform Activation is the **ultimate conversion indicator** for Hedge Edge. It answers one question: **did this user actually connect to a trading platform and start using the product?**

Everything upstream — beta claim, key issuance, email click, even desktop app open — is a _leading indicator_. Platform Activation is the only event that proves the user has the product running on a live trading platform.

A license validation alone is **not** activation. The desktop app validates the license key on every launch. That proves the app opened, not that the user connected an Expert Advisor to a chart.

---

## Definition

A user is **Platform Activated** when ALL of the following are true:

| # | Condition | Supabase Check |
|---|-----------|----------------|
| 1 | At least one successful validation with `platform` ∈ {`mt5`, `mt4`, `ctrader`} | `license_validation_logs` WHERE `success = true` AND `platform IN ('mt5', 'mt4', 'ctrader')` |
| 2 | A persistent device row exists for that platform | `license_devices` WHERE `platform IN ('mt5', 'mt4', 'ctrader')` AND `is_active = true` |
| 3 | The platform validation is from a non-test device | `device_id` NOT IN known test devices (`test-device-*`, `dev-desktop-*`) |

### Confidence Tiers

| Tier | Evidence | Label |
|------|----------|-------|
| **Confirmed** | ≥2 successful platform validations from same device + active `license_devices` row + platform metadata (accountId, broker, instance_name) | `ACTIVATED` |
| **Probable** | 1 successful platform validation + active `license_devices` row | `ACTIVATION_PROBABLE` |
| **Unconfirmed** | Successful `desktop` or `unknown` validations only, no platform-specific events | `NOT_ACTIVATED` |
| **None** | No validation events at all | `NEVER_SEEN` |

### What Does NOT Count as Activation

| Event | Why It Doesn't Count |
|-------|---------------------|
| Beta key claimed | Just a sign-up event — no product usage |
| License key issued / emailed | Provisioning, not usage |
| Desktop app opened (`platform = desktop`) | App launched but EA not connected to chart |
| Unknown platform validation (`platform = unknown`) | Cannot confirm trading platform connection |
| Single validation with a test device ID | Internal testing, not real user activation |
| Payment / subscription created | Revenue event, not activation event |

---

## Supabase Query Reference

### Check if a user is Platform Activated

```sql
-- Step 1: Find their license
SELECT id, license_key, email FROM licenses WHERE email = '<user_email>';

-- Step 2: Check for platform-specific validations (use truncated key)
SELECT device_id, platform, success, error_code, created_at
FROM license_validation_logs
WHERE license_key LIKE '<first_20_chars>%'
  AND platform IN ('mt5', 'mt4', 'ctrader')
  AND success = true
ORDER BY created_at DESC;

-- Step 3: Check for persistent platform device
SELECT device_id, platform, broker, account_id, is_active, first_seen_at, last_seen_at
FROM license_devices
WHERE license_id = '<license_uuid>'
  AND platform IN ('mt5', 'mt4', 'ctrader')
  AND is_active = true;
```

### Python (service-role)

```python
from shared.supabase_client import get_supabase

def check_platform_activation(email: str) -> dict:
    sb = get_supabase(use_service_role=True)

    # Get license
    license_row = sb.table('licenses').select('id, license_key, email').eq('email', email).single().execute().data
    if not license_row:
        return {'status': 'NO_LICENSE', 'activated': False}

    key_prefix = license_row['license_key'][:20]
    license_id = license_row['id']

    # Check platform validations
    validations = sb.table('license_validation_logs').select('device_id, platform, success, created_at').eq('success', True).like('license_key', f'{key_prefix}%').in_('platform', ['mt5', 'mt4', 'ctrader']).order('created_at', desc=True).execute().data or []

    # Check persistent device
    devices = sb.table('license_devices').select('device_id, platform, broker, account_id, is_active, last_seen_at').eq('license_id', license_id).in_('platform', ['mt5', 'mt4', 'ctrader']).eq('is_active', True).execute().data or []

    # Filter out test devices
    test_prefixes = ('test-device-', 'dev-desktop-')
    validations = [v for v in validations if not any(v.get('device_id', '').startswith(p) for p in test_prefixes)]
    devices = [d for d in devices if not any(d.get('device_id', '').startswith(p) for p in test_prefixes)]

    if len(validations) >= 2 and devices:
        return {'status': 'ACTIVATED', 'activated': True, 'confidence': 'confirmed', 'platform_validations': len(validations), 'active_devices': len(devices)}
    elif len(validations) >= 1 and devices:
        return {'status': 'ACTIVATION_PROBABLE', 'activated': True, 'confidence': 'probable', 'platform_validations': len(validations), 'active_devices': len(devices)}
    elif validations:
        return {'status': 'ACTIVATION_PROBABLE', 'activated': False, 'confidence': 'weak', 'platform_validations': len(validations), 'active_devices': 0}
    else:
        desktop_only = sb.table('license_validation_logs').select('id').eq('success', True).like('license_key', f'{key_prefix}%').execute().data or []
        if desktop_only:
            return {'status': 'NOT_ACTIVATED', 'activated': False, 'confidence': 'none', 'note': 'Desktop/unknown validations only — EA not connected'}
        return {'status': 'NEVER_SEEN', 'activated': False}
```

---

## Platform Metadata Fields

When a platform validation occurs, the backend may capture additional metadata that strengthens the activation signal:

| Field | Purpose | Activation Value |
|-------|---------|-----------------|
| `platform` | Which trading platform | Must be `mt5`, `mt4`, or `ctrader` |
| `device_id` | Unique device fingerprint | Persistent device = real installation |
| `accountId` | Trading account number | Proves broker account linked |
| `broker` | Broker name | Confirms broker setup |
| `instance_name` | EA instance identifier | Confirms EA attached to chart |
| `version` | EA version string | Confirms correct EA version |

---

## Reporting Integration

### KPIs (→ kpi-framework.md)
- **Platform Activation Rate** = `ACTIVATED users / total license holders` — target ≥60%, alert <30%
- **Time-to-Activation** = median days from key issuance to first platform validation — target ≤3 days, alert >7 days
- **Activation-to-Desktop Ratio** = platform activations / desktop-only validations — measures EA setup friction

### Funnel (→ funnel-reporting.md)
Platform Activation is the critical stage between "Desktop App Opened" and "First Hedge Executed":
```
Beta Claim → Key Issued → Desktop Opened → ★ Platform Activated ★ → First Hedge → Retained User
```

### License Health (→ license-tracking-analytics.md)
The health score must incorporate activation status:
- `NOT_ACTIVATED` after 7+ days = `NEEDS_ONBOARDING_HELP`
- `ACTIVATED` + no activity for 7+ days = `CHURNING`
- `ACTIVATED` + regular activity = `HEALTHY`

### Lead Scoring (→ GROWTH lead-qualification.md)
- Platform Activation = +50 points (highest single action)
- Desktop-only validation = +10 points
- Beta claim without any validation = +5 points

### Sales Onboarding (→ GROWTH beta-tester-onboarding.md)
- `Beta Activated` field must be set to `true` ONLY when Platform Activation is confirmed
- `Product Used` field must be set to `true` ONLY when Platform Activation is confirmed
- Follow-up rules should key off activation status, not desktop validation

### Product Telemetry (→ STRATEGY platform-integration.md)
- Every platform EA/cBot must send `platform`, `device_id`, `accountId`, `broker` on validation
- Future: add explicit `ea_connected` event distinct from license validation
- Platform integration rollout gates must include activation rate thresholds

---

## Operational Checklist — Verify a Specific User

1. Get their email or license key
2. Query `license_validation_logs` filtered to today / recent window
3. Filter to `platform IN ('mt5', 'mt4', 'ctrader')`
4. Confirm `success = true`
5. Check `license_devices` for a matching platform + `is_active = true`
6. Look for ≥2 events from the same device (rules out single test hit)
7. Check for metadata: `accountId`, `broker`, `instance_name`

**Decision matrix:**

| Evidence Found | Verdict |
|----------------|---------|
| Only `desktop` / `unknown` validations | ❌ Not activated — app opened, EA not connected |
| 1× platform validation, no device row | ⚠️ Probable test, not confirmed |
| 1× platform validation + device row | ✅ Probable activation |
| ≥2× platform validations + device row | ✅✅ Confirmed activation |
| ≥2× platform + device + metadata (broker/account) | ✅✅✅ Strong confirmed activation |

---

## Future Improvements

1. **Explicit `ea_connected` event**: Separate from generic license validation — sent when EA successfully attaches to a chart
2. **Chart symbol capture**: Log which instrument the EA is monitoring (`EURUSD`, `GBPJPY`, etc.)
3. **Heartbeat-based activation**: Treat sustained heartbeats from a platform device as stronger signal than one-time validation
4. **Activation webhook**: Fire a webhook/Discord alert on first confirmed Platform Activation per user
5. **Supabase `activation_events` table**: Dedicated table for activation milestones with richer metadata
