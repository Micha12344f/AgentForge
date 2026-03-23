---
name: beta-tester-onboarding
description: |
  Standard operating procedure for registering a new beta tester in the
  beta_waitlist (Notion). Triggered whenever a beta license key is issued
  to an external user. Owned by Sales — this ensures every key recipient
  is tracked for activation follow-up and sales watchlist monitoring.
---

# Beta Tester Onboarding — Sales SOP

## Objective

Every user who receives a Hedge Edge beta license key must have a corresponding
record in the `beta_waitlist` Notion database **before or at the time the key is sent**.
This ensures Sales can track activation status, follow up on non-activators, and
escalate high-priority beta testers to the sales watchlist.

## Scope

This SOP covers **only the `beta_waitlist` record creation**. It does not cover:
- License key generation (handled by `seed_beta_key_pool.py`)
- License table assignment in Supabase (one-off provisioning step)
- Sending the confirmation email (handled by Marketing → `send_license_email.py`)
- Adding the user to `leads_crm` (handled by Marketing → `beta-lead-registration.md`)

## Trigger Conditions

Execute this SOP whenever **any** of the following occur:
- A new beta tester signs up via the landing page beta form
- A user is manually selected for beta access by the team
- A Twitter/social DM conversion is identified as a beta signup
- The automated beta signup webhook fires (`signup_method = beta_email`)

## Execution Script

```bash
python Business/GROWTH/executions/Sales/beta_waitlist_onboard.py \
  --email "user@example.com" \
  --name "First Last" \
  --source "Twitter Bio" \
  --key "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
```

**Arguments:**

| Argument | Required | Default | Description |
|---|---|---|---|
| `--email` | Yes | — | Beta tester's email address |
| `--name` | No | derived from email | Display name (first + last) |
| `--source` | No | `Twitter Bio` | Acquisition source |
| `--key` | No | — | License key (if already assigned) |
| `--priority` | No | `P2` | `P1` (high-intent) / `P2` (standard) / `P3` (passive) |
| `--watchlist` | No | `false` | Flag for sales watchlist (`true`/`false`) |
| `--dry-run` | No | `false` | Print the row without writing to Notion |

## Step-by-Step Process

### Step 1 — Deduplication Check
Before writing, query `beta_waitlist` for an existing record with the same email.
If a record already exists, skip creation and log a warning. Do **not** create duplicates.

### Step 2 — Determine Priority
Assign priority based on source:
- **P1**: Direct referral, sales-sourced, high-intent DM reply
- **P2**: Twitter Bio, organic social, landing page beta form
- **P3**: Email drip opt-in, cold list

### Step 3 — Create `beta_waitlist` Record
Write a new row with the following fields:

| Field | Value |
|---|---|
| `Name` | First name (or email prefix if unknown) |
| `First Name` | First name |
| `Last Name` | Last name (empty if unknown) |
| `Email` | Beta tester email |
| `Source` | Acquisition channel (e.g. `Twitter Bio`, `Landing Page`, `Referral`) |
| `Beta Key` | License key (if assigned; leave blank if key not yet issued) |
| `Beta Key Sent` | `true` if key was sent; `false` if pending |
| `Key Sent Date` | Today's date (ISO format) |
| `Tags` | `["Beta", "Beta Key Sent"]` |
| `Priority` | `P1` / `P2` / `P3` |
| `Sales Watchlist` | `false` by default; set `true` for high-intent signals |
| `Beta Activated` | `false` |
| `Beta Key Clicked` | `false` |
| `Product Used` | `false` |
| `Lifecycle Owner` | `Marketing` |
| `Notes` | Auto-generated: source + signup date |

### Step 4 — Post-Creation Tasks (Sales Responsibility)

After the record is created:
1. If `Sales Watchlist = true`, Sales agent reviews within 24 hours and logs initial outreach in `leads_crm`
2. If user does not activate within **7 days**, flag as `Activation Pending` and trigger re-engagement email
3. If user does not activate within **14 days**, escalate to Sales for direct Discord/email outreach

## Activation Follow-Up Rules

| Days Since Key Sent | Action |
|---|---|
| 0–2 | No action needed |
| 3–7 | Check `Beta Key Clicked` flag; if false, trigger reminder email |
| 8–14 | Move Tags to include `Activation Pending`; assign Sales owner |
| 15+ | Escalate to P1 follow-up DM; update `Priority` to P1 |

## Data Quality Rules

- `Email` is the unique key — never create two rows with the same email
- `Beta Key` must be a valid pool key from the `licenses` table (plan = `professional` or `enterprise`)
- `Source` must map to one of: `Twitter Bio`, `Landing Page`, `Referral`, `Email Drip`, `Discord`, `Direct`
- `Key Sent Date` must be populated when `Beta Key Sent = true`

## Related Directives

- `crm-management.md` — after activation, Sales creates a full CRM record in `leads_crm`
- `lead-qualification.md` — activated beta testers are scored and may be promoted to MQL
- `sales-pipeline.md` — converted beta testers enter pipeline at `Demo Requested` stage

## Related Executions

- `beta_waitlist_onboard.py` — this SOP's execution script (Sales)
- `beta_lead_register.py` — Marketing's parallel script for `leads_crm` registration
- `seed_beta_key_pool.py` — generates and pools beta license keys
- `send_license_email.py` — sends the license key confirmation email
