# DSAR (Data Subject Access Request) Process — Hedge Edge Ltd
> Step-by-step procedure for handling data subject rights requests
> UK GDPR Articles 15-22

---

## Overview

Any individual whose data we process can exercise their rights under the UK GDPR. Hedge Edge must respond within **30 calendar days** of receiving a valid request.

---

## Step 1: Receive Request

Requests may arrive via:
- Email to hedgeedgebusiness@gmail.com
- Discord DM to community manager
- Chat widget on hedgedge.info
- Post to registered address

**Any request counts** — it does not need to mention "GDPR" or "DSAR" specifically. If someone asks "what data do you have on me?" or "delete my account", that's a valid request.

## Step 2: Verify Identity

Before disclosing any personal data:

1. **Known user (email matches account)**: Respond to the same email address = verified
2. **Unknown requester**: Ask for the email address associated with their Hedge Edge account
3. **Suspicious request**: Request additional verification (e.g., account creation date, subscription tier)
4. **NEVER** disclose data to an unverified third party

## Step 3: Log the Request

Record in the DSAR register:

| Field | Value |
|---|---|
| Date received | [DATE] |
| Requester email | [EMAIL] |
| Type of request | Access / Rectification / Erasure / Restriction / Portability / Objection |
| Verified | Yes / No |
| Deadline (30 days) | [DATE + 30] |
| Status | Open / In Progress / Complete |
| Response date | [DATE] |

## Step 4: Gather Data

For a **Data Subject Access Request** (Article 15), collect all data from:

| System | Data to Export | How |
|---|---|---|
| Supabase | User record, subscription, usage logs | SQL query on user table by email |
| Creem | Payment history, subscription status | Creem dashboard or API |
| Resend | Email send logs, engagement events | Resend dashboard |
| Discord | Support conversation logs | Export from support_chat_logs table |
| Analytics | Not applicable | IP addresses are anonymised |

### SQL Example (Supabase)
```sql
-- Export all user data for a DSAR
SELECT * FROM users WHERE email = '[EMAIL]';
SELECT * FROM subscriptions WHERE user_id = (SELECT id FROM users WHERE email = '[EMAIL]');
SELECT * FROM license_activations WHERE user_id = (SELECT id FROM users WHERE email = '[EMAIL]');
```

## Step 5: Respond

### For Access Requests (Article 15)
Provide:
1. Confirmation that we process their data
2. Copy of all personal data held
3. Information about: purposes, categories, recipients, retention, rights, source
4. Format: JSON or PDF (machine-readable for portability requests)

### For Erasure Requests (Article 17)
1. Delete user account in Supabase (run `supabase-delete-account.sql`)
2. Request deletion from Creem (contact support if needed)
3. Remove from Resend mailing lists
4. Delete Discord support logs
5. Confirm deletion to the requester
6. **Retain**: Financial records required by law (6 years) — inform the requester

### For Rectification Requests (Article 16)
1. Update the incorrect data in Supabase
2. Confirm the correction to the requester

### For Objection to Marketing (Article 21)
1. Immediately remove from all marketing lists
2. Add to suppression list (do NOT delete — they might re-enter the funnel)
3. Confirm removal to the requester

## Step 6: Timeline

| Action | Deadline |
|---|---|
| Acknowledge receipt | 3 business days |
| Complete response | 30 calendar days |
| Extension (complex requests) | Up to 60 additional days (must notify requester) |
| Refusal (manifestly unfounded) | 30 days (must explain why and inform of right to complain) |

## Step 7: Record Keeping

After completing each request:
1. Update DSAR register with completion date and outcome
2. Retain a record of what was provided/deleted (for audit purposes)
3. Do NOT retain copies of the personal data disclosed

---

## Template Responses

### Acknowledgement Email
```
Subject: Your Data Request — Hedge Edge

Hi [NAME],

Thank you for your request dated [DATE]. We have received your [type] request 
and will respond within 30 days.

If we need any additional information to verify your identity or clarify your 
request, we will contact you.

Best regards,
Hedge Edge Ltd
```

### Completion Email (Access)
```
Subject: Your Data — Hedge Edge

Hi [NAME],

Please find attached all personal data we hold about you, as requested on [DATE].

This includes:
- Account information
- Subscription history
- Communication records

If you have any questions about this data, or wish to exercise any additional 
rights (correction, deletion, etc.), please reply to this email.

Best regards,
Hedge Edge Ltd
```

### Completion Email (Erasure)
```
Subject: Account Deletion Complete — Hedge Edge

Hi [NAME],

As requested, we have deleted your Hedge Edge account and associated personal data.

Please note:
- Financial transaction records are retained for 6 years as required by UK law
- Your email has been added to our suppression list to prevent re-marketing

This action is irreversible. If you wish to use Hedge Edge in the future, 
you will need to create a new account.

Best regards,
Hedge Edge Ltd
```
