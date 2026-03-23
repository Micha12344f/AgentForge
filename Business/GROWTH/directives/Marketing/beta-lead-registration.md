---
name: beta-lead-registration
description: |
  Standard operating procedure for registering a new beta tester as a lead
  in leads_crm (Notion). Triggered in parallel with beta key issuance.
  Owned by Marketing — ensures every beta recipient enters the marketing
  funnel for nurture sequences, attribution tracking, and conversion reporting.
---

# Beta Lead Registration — Marketing SOP

## Objective

Every user who receives a Hedge Edge beta license key must have a corresponding
lead record in `leads_crm` **at the time the key is sent**. This ensures
Marketing can attribute the lead to the correct channel, enroll them in the
appropriate nurture sequence, and track their progression from beta → paid.

## Scope

This SOP covers **only the `leads_crm` record creation**. It does not cover:
- License key generation or assignment (provisioning step)
- The `beta_waitlist` record (handled by Sales → `beta-tester-onboarding.md`)
- Sending the confirmation email (handled by `send_license_email.py`)
- Email sequence enrollment (handled by `email_marketing/` engine post-registration)

## Trigger Conditions

Execute this SOP whenever **any** of the following occur:
- A beta key is issued to a new external user
- A signup via `beta_email` method is detected in `user_attribution`
- Sales completes a `beta_waitlist` onboarding and notifies Marketing
- Automated webhook fires confirming key delivery

## Execution Script

```bash
python Business/GROWTH/executions/Marketing/beta_lead_register.py \
  --email "user@example.com" \
  --name "First Last" \
  --source "Twitter"
```

**Arguments:**

| Argument | Required | Default | Description |
|---|---|---|---|
| `--email` | Yes | — | Beta tester's email address |
| `--name` | No | derived from email | First and last name |
| `--source` | No | `Twitter` | UTM source / acquisition channel |
| `--dry-run` | No | `false` | Print the row without writing to Notion |

**Valid `--source` values:** `Twitter`, `Landing Page`, `Referral`, `Email Drip`, `Discord`, `Direct`

## Step-by-Step Process

### Step 1 — Deduplication Check
Query `leads_crm` for a row matching the email address. If a record already exists,
skip creation and log a warning. Do **not** create duplicate CRM entries.

### Step 2 — Determine Source Mapping
Map acquisition source to the standard CRM source label:

| Raw Source | CRM `Source` Value |
|---|---|
| `twitter`, `Twitter Bio` | `Twitter` |
| `landing-page`, `Landing Page` | `Landing Page` |
| `referral` | `Referral` |
| `email`, `Email Drip` | `Email Drip` |
| `discord` | `Discord` |
| `direct`, `none`, unknown | `Direct` |

### Step 3 — Create `leads_crm` Record
Write a new row with the following fields:

| Field | Value |
|---|---|
| `Email` | Beta tester email |
| `First Name` | First name (or email username if unknown) |
| `Last Name` | Last name (empty if unknown) |
| `Source` | Mapped acquisition channel |
| `Subject` | `Beta Tester — [Source]` |

> **Note:** `Pipeline stage` is a computed rollup field — do not attempt to write it directly.
> It will auto-populate based on linked campaign/email data.

### Step 4 — Sequence Enrollment (Marketing Follow-Up)

After the record is created, Marketing must enroll the lead in the appropriate sequence:
- Source = `Twitter` or `Landing Page` → **Beta Activation sequence**
- Source = `Referral` → **Beta Referral sequence** (warm tone, shorter)
- Source = `Email Drip` → already enrolled; verify sequence step and skip re-enroll

Enrollment is handled separately via the email marketing engine — this script only
creates the CRM record.

### Step 5 — Attribution Tagging

Verify the lead's `user_attribution` row (Supabase) has the correct `utm_source`,
`utm_medium`, and `utm_campaign` fields populated. If missing, note it in the row's
`Subject` field for manual attribution cleanup.

## Data Quality Rules

- `Email` is the unique key — never create two rows with the same email
- `Source` must use the standard label values from the mapping table above
- Do not populate rollup or computed fields — they will throw warnings and be ignored

## Conversion Tracking

When a beta tester converts to a paid license:
1. Update `Source` to reflect original channel (do not change)
2. Update `Subject` to `Converted — [Plan]`
3. Conversion is tracked in Supabase `user_attribution` and reported by `conversion_tracker.py`

## Related Directives

- `beta-tester-onboarding.md` (Sales) — parallel SOP for `beta_waitlist` registration
- `email-marketing.md` — sequence enrollment post-registration
- `attribution-tracking.md` — UTM attribution pipeline for lead source accuracy
- `user-onboarding.md` — activation flow after key is received

## Related Executions

- `beta_lead_register.py` — this SOP's execution script (Marketing)
- `beta_waitlist_onboard.py` — Sales' parallel script for `beta_waitlist` registration
- `send_license_email.py` — sends the license key confirmation email
- `conversion_tracker.py` — tracks beta → paid conversions over time
