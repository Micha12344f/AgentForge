# Record of Processing Activities (ROPA) — Hedge Edge Ltd
> Article 30 UK GDPR — Data Controller Record
> Last updated: 2026-03-15

---

## Controller Details

| Field | Value |
|---|---|
| **Controller Name** | Hedge Edge Ltd |
| **Registered Address** | Office 14994, 182-184 High Street North, East Ham, London, E6 2JA |
| **Contact Email** | hedgeedgebusiness@gmail.com |
| **ICO Registration** | Pending |

---

## Processing Activities

### 1. User Registration & Authentication

| Field | Detail |
|---|---|
| Purpose | Create and manage user accounts |
| Categories of data subjects | Registered users |
| Categories of personal data | Email address, hashed password, account creation date |
| Lawful basis | Contract performance (Art 6(1)(b)) |
| Recipients | Supabase Inc. (processor) |
| International transfers | US (Supabase) — SCCs required |
| Retention period | Until account deletion + 30 days |
| Technical measures | Encryption at rest, TLS in transit, bcrypt password hashing |

### 2. Subscription & Payment Processing

| Field | Detail |
|---|---|
| Purpose | Process subscription payments and manage billing |
| Categories of data subjects | Paying subscribers |
| Categories of personal data | Email, subscription tier, payment status, Creem customer ID |
| Lawful basis | Contract performance (Art 6(1)(b)) |
| Recipients | Creem.io (processor) |
| International transfers | US (Creem) — SCCs required |
| Retention period | 6 years (financial record-keeping obligations) |
| Technical measures | PCI DSS (handled by Creem), no card data stored by Hedge Edge |

### 3. Email Communications

| Field | Detail |
|---|---|
| Purpose | Transactional emails (receipts, guide delivery) and marketing |
| Categories of data subjects | Registered users, leads |
| Categories of personal data | Email address, name, email engagement events (opens, clicks) |
| Lawful basis | Contract (transactional), Consent (marketing) |
| Recipients | Resend Inc. (processor) |
| International transfers | US (Resend) — SCCs required |
| Retention period | Until unsubscribe + 30 days; consent records retained for 3 years |
| Technical measures | TLS, DKIM signing, unsubscribe mechanism |

### 4. Website Analytics

| Field | Detail |
|---|---|
| Purpose | Understand website traffic, conversions, and user behaviour |
| Categories of data subjects | Website visitors |
| Categories of personal data | IP address (anonymised), browser info, page views, UTM parameters |
| Lawful basis | Legitimate interest (Art 6(1)(f)) — with cookie consent |
| Recipients | Vercel Inc. (hosting), analytics tools |
| International transfers | US (Vercel) — SCCs required |
| Retention period | 30 days (server logs), 26 months (analytics) |
| Technical measures | IP anonymisation, cookie consent banner |

### 5. Community Support (Discord)

| Field | Detail |
|---|---|
| Purpose | Provide community support and engagement |
| Categories of data subjects | Discord community members |
| Categories of personal data | Discord username, messages, support conversation logs |
| Lawful basis | Legitimate interest (Art 6(1)(f)) |
| Recipients | Discord Inc. (platform), Supabase (support logs) |
| International transfers | US (Discord, Supabase) — platform's own safeguards |
| Retention period | Indefinite (community content); support logs 2 years |
| Technical measures | Discord's security measures, bot access controls |

### 6. Lead Management

| Field | Detail |
|---|---|
| Purpose | Track and nurture potential customers |
| Categories of data subjects | Leads from website, social media, email |
| Categories of personal data | Email, name, source/UTM, engagement score, phone (optional) |
| Lawful basis | Consent (opt-in forms), Legitimate interest (inquiry follow-up) |
| Recipients | Supabase (storage), Resend (email) |
| International transfers | US (Supabase, Resend) — SCCs required |
| Retention period | 2 years from last engagement, or until consent withdrawn |
| Technical measures | Encryption at rest, access controls |

### 7. IB (Introducing Broker) Referral Tracking

| Field | Detail |
|---|---|
| Purpose | Track broker referrals for commission purposes |
| Categories of data subjects | Users who open broker accounts via Hedge Edge links |
| Categories of personal data | Referral ID, broker account reference (no financial data) |
| Lawful basis | Contract performance (Art 6(1)(b)), Legitimate interest |
| Recipients | Vantage, BlackBull (IB partners) |
| International transfers | Australia (Vantage), NZ (BlackBull) — adequacy / SCCs |
| Retention period | Duration of IB agreement + 2 years |
| Technical measures | Anonymised referral tracking, no direct access to broker account data |
