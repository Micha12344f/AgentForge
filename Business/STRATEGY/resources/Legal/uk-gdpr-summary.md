# UK GDPR Summary for SaaS Businesses
> Reference guide for Hedge Edge Ltd — a UK-registered SaaS company processing personal data
> Based on: UK General Data Protection Regulation (UK GDPR) + Data Protection Act 2018

---

## 1. Overview

The UK GDPR applies to Hedge Edge Ltd as a UK company that processes personal data of individuals. The company is a **data controller** — it determines the purposes and means of processing personal data.

Key legislation:
- **UK GDPR** (retained EU law, tailored by the Data Protection, Privacy and Electronic Communications (Amendments etc) (EU Exit) Regulations 2019)
- **Data Protection Act 2018** (UK implementing legislation)
- **Privacy and Electronic Communications Regulations 2003 (PECR)** (cookies, marketing emails)

Supervisory authority: **Information Commissioner's Office (ICO)**

---

## 2. Lawful Bases for Processing (Article 6)

Hedge Edge processes data under these lawful bases:

| Processing Activity | Lawful Basis | Article |
|---|---|---|
| User registration & authentication | Contract performance | 6(1)(b) |
| Subscription management | Contract performance | 6(1)(b) |
| Payment processing (via Creem) | Contract performance | 6(1)(b) |
| Email notifications (transactional) | Contract performance | 6(1)(b) |
| Marketing emails & newsletters | Consent | 6(1)(a) |
| Website analytics | Legitimate interest | 6(1)(f) |
| Discord community support | Legitimate interest | 6(1)(f) |
| Fraud prevention | Legitimate interest | 6(1)(f) |
| Legal compliance (tax records) | Legal obligation | 6(1)(c) |

---

## 3. Data Subject Rights

Under Articles 15-22, individuals have:

| Right | Article | Response Time | Notes |
|---|---|---|---|
| Right of access (DSAR) | 15 | 30 days | Free of charge; 1 month extension for complex requests |
| Right to rectification | 16 | 30 days | Must correct inaccurate data |
| Right to erasure | 17 | 30 days | "Right to be forgotten" — exceptions for legal obligations |
| Right to restrict processing | 18 | 30 days | Must stop processing but can store |
| Right to data portability | 20 | 30 days | Machine-readable format (JSON/CSV) |
| Right to object | 21 | 30 days | Must stop processing for direct marketing immediately |
| Rights related to automated decision-making | 22 | 30 days | Hedge Edge does not make solely automated decisions |

---

## 4. International Transfers (Chapter V)

Hedge Edge uses US-based processors. Since the UK is no longer in the EU, transfers must comply with:

- **UK Adequacy Decisions** — The US does not have a blanket adequacy decision from the UK
- **UK International Data Transfer Agreement (IDTA)** or **UK Addendum to EU SCCs** — Required for each US processor
- **Transfer Impact Assessment (TIA)** — Must assess whether US law provides adequate protection

### Required Actions:
1. Execute UK SCCs/IDTA with Supabase, Vercel, Creem, and Resend
2. Document Transfer Impact Assessment for each processor
3. Review US processor's compliance with UK GDPR equivalence

---

## 5. Data Protection Impact Assessment (DPIA)

Article 35 requires a DPIA when processing is likely to result in high risk. Assessment for Hedge Edge:

| Processing | High Risk? | DPIA Required? |
|---|---|---|
| Standard SaaS user management | No | No |
| Payment processing | No (Creem handles) | No |
| Trading data (MT5 account numbers) | Possibly | Review needed |
| Automated email marketing | No | No |
| Community support via Discord | No | No |

**Recommendation**: Conduct a DPIA if Hedge Edge begins processing trading performance data or financial information beyond what's needed for the hedging service.

---

## 6. Data Breach Notification (Articles 33-34)

| Action | Timeline | Recipient |
|---|---|---|
| Assess breach severity | Immediately | Internal |
| Notify ICO (if risk to individuals) | 72 hours | ICO breach reporting portal |
| Notify affected individuals (if high risk) | Without undue delay | Data subjects |
| Document breach in internal register | Ongoing | Internal records |

### Breach Response Template:
1. Contain the breach
2. Assess: What data? How many individuals? What's the risk?
3. If reportable → notify ICO within 72 hours
4. If high risk to individuals → notify them directly
5. Document everything in breach register

---

## 7. ICO Registration

All organisations processing personal data must be registered with the ICO unless exempt.

- **Hedge Edge status**: Must register
- **Fee tier**: Tier 1 (£40/year) — turnover under £632K, fewer than 10 staff
- **Registration URL**: https://ico.org.uk/registration/
- **Exemptions**: None apply (Hedge Edge is a commercial data controller)

---

## 8. Cookies & PECR

The Privacy and Electronic Communications Regulations (PECR) require:

- **Strictly necessary cookies**: No consent needed (e.g., auth tokens)
- **Analytics cookies**: Consent required (opt-in)
- **Marketing cookies**: Consent required (opt-in)

**Action**: Implement a cookie consent banner on hedgedge.info that:
1. Blocks non-essential cookies until consent is given
2. Allows granular consent (analytics vs. marketing)
3. Provides a way to withdraw consent
4. Records consent for audit purposes

---

## 9. Direct Marketing (PECR + UK GDPR)

For email marketing:
- **Existing customers**: Can use "soft opt-in" (similar products, easy unsubscribe)
- **New leads**: Must have explicit consent (opt-in checkbox, not pre-ticked)
- **Every email**: Must include unsubscribe link
- **Records**: Must keep consent records (when, how, what they consented to)

---

## 10. Key Contacts

| Role | Contact |
|---|---|
| ICO Helpline | 0303 123 1113 |
| ICO Breach Reporting | https://ico.org.uk/make-a-complaint/data-protection-complaints/data-protection-complaints/ |
| Hedge Edge DPO (if appointed) | hedgeedgebusiness@gmail.com |
