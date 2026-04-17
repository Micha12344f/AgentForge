# Meeseks MVP Scope

**Status**: Drafted  
**Date**: April 15, 2026  
**Owner**: PRODUCT  
**Working definition**: If a feature does not help Meeseks check a launch-ready campaign, explain what is wrong, route a human decision, or store the decision history, it is not MVP.

---

## 1. MVP Objective

Ship the smallest functional version of Meeseks that proves a paid media team will use and pay for **read-only campaign launch assurance** before spend goes live.

The MVP is not a general AI marketing platform. It is a narrow control layer that:

- checks launch-ready campaigns before activation
- catches common high-cost configuration errors
- delivers a clear pass, warn, or fail summary
- routes approval through Slack
- stores an audit record of what was checked and who approved it

---

## 2. Target Customer

### Primary segment

- Performance marketing agencies managing repeated launches across multiple client accounts
- Mid-market in-house paid media teams running campaigns across multiple platforms

### Customer profile threshold

- spends more than USD 50K per year on paid media
- launches campaigns across at least 2 platforms
- already uses a manual checklist, QA sheet, or approval process
- feels real pain from launch mistakes, tracking issues, or review delays

### Explicitly not for MVP

- solo consultants
- advertisers with very low spend
- enterprise accounts requiring SSO, procurement reviews, or custom security controls before pilot

---

## 3. Core Job To Be Done

"Before we launch this campaign, tell us whether anything important is wrong, show us exactly what failed, and give us a clean approval trail before money is spent."

---

## 4. Exact MVP Scope

### 4.1 Supported platforms

- Meta Ads
- Google Ads
- LinkedIn Campaign Manager

These integrations are **read-only** in the MVP.

### 4.2 Trigger for a validation run

The MVP supports one trigger only:

- a user selects a campaign and clicks `Validate` from a lightweight web interface

No automatic launch triggers are included in the MVP.

### 4.3 Validation categories included

The MVP checks the highest-value, easiest-to-trust failure modes first.

| Category | MVP checks |
|----------|------------|
| Budget | Missing budget, budget outside allowed range, obvious mismatch with team rule |
| Scheduling | Missing start date, missing end date where required, launch date in past, end date before start date |
| Geography | Geo targets missing or outside allowed market list |
| Naming | Campaign name does not match required naming pattern |
| UTM hygiene | Required UTM fields missing, malformed, or inconsistent with workspace convention |
| Destination | Landing page URL missing, non-200 response, redirect loop, or timeout |

### 4.4 Validation categories excluded from MVP

- auto-fixing campaign settings
- write-back to any ad platform
- GA4 event validation
- CRM audience matching
- creative policy prediction
- pixel or conversion-tag debugging beyond basic URL and UTM checks
- benchmark scoring or predictive risk scoring

### 4.5 Rule configuration model

Each customer workspace gets a manually configured rule set that includes:

- allowed markets or geos
- naming convention pattern
- required UTM parameters
- budget floor and ceiling rules
- required schedule fields

Rule setup is done by the Meeseks team during onboarding. There is **no self-serve rule builder** in the MVP.

### 4.6 Output of a validation run

Every validation run must produce:

- overall verdict: `Pass`, `Warn`, or `Fail`
- list of findings with severity: `Critical`, `High`, `Medium`, `Low`
- plain-language explanation for each finding
- recommended next action for each failed rule
- timestamped audit record

### 4.7 Approval workflow

After validation completes, Meeseks sends a Slack message to a configured channel with:

- campaign name
- platform
- overall verdict
- top issues
- `Approve` or `Block` decision buttons

The approval decision is recorded in the audit log.

Important: `Approve` or `Block` changes only the Meeseks record. It does **not** publish, pause, or edit the campaign in-platform.

### 4.8 User-facing surfaces

The MVP has only two customer-facing surfaces:

1. A lightweight web interface for:
   - selecting a workspace and campaign
   - launching validation
   - viewing the latest report
   - viewing validation history
2. Slack for:
   - alerts
   - approval or block decisions

No polished multi-page dashboard is required.

---

## 5. Minimal User Workflow

1. Customer connects Meta, Google, or LinkedIn accounts with read-only access.
2. Meeseks configures the customer's rule set during onboarding.
3. User opens the Meeseks web interface and selects a launch-ready campaign.
4. User clicks `Validate`.
5. Meeseks fetches campaign settings and destination URL data.
6. Rules run against the campaign.
7. Meeseks generates a report with findings and overall verdict.
8. Meeseks posts the summary into Slack.
9. A human clicks `Approve` or `Block`.
10. Meeseks stores the run, findings, and decision in the audit history.

---

## 6. Out Of Scope

The following are explicitly not part of the MVP:

- self-serve onboarding
- self-serve rule authoring
- billing and subscription management
- role-based permissions beyond one basic workspace access model
- SSO
- GA4, HubSpot, Salesforce, Asana, Monday, or any non-Slack integration
- automatic campaign discovery from project-management events
- autonomous launching
- auto-remediation or write access to ad platforms
- cross-customer benchmarking
- community rule templates or marketplace
- enterprise reporting exports
- mobile app

---

## 7. MVP Success Criteria

The MVP is successful if it proves all of the following:

### Product proof

- A user can run validation on a supported campaign and receive a usable result in under 2 minutes.
- The system catches real launch issues in live or near-live design-partner workflows.
- The Slack approval flow works end-to-end and the decision is stored.

### Commercial proof

- At least 3 design partners onboard to the MVP.
- At least 2 of those design partners are willing to pay for the pilot or commit to a paid continuation.
- At least 1 customer reports that Meeseks saved meaningful QA time or prevented a real mistake.

### Trust proof

- Users understand why a rule failed without requiring manual translation from the Meeseks team.
- False positives stay low enough that customers continue using the workflow.

---

## 8. Acceptance Criteria For Build Completion

The MVP build is complete when all of the following are true:

- A workspace can be created with customer-specific validation rules.
- Meta, Google, and LinkedIn can each be connected in read-only mode.
- A user can select a supported campaign and run validation manually.
- The system evaluates the 6 included validation categories.
- The report shows verdict, findings, severity, and recommended next action.
- Slack receives an alert for each completed run.
- A user can record `Approve` or `Block` from Slack.
- The audit log stores campaign, platform, findings, timestamps, and final decision.
- No feature in the MVP requires write access to ad platform APIs.

---

## 9. Recommended Build Order

Build in this sequence:

1. Workspace and rule schema
2. Validation engine with the 6 core rule categories
3. Destination URL checker
4. Meta read-only integration
5. Google Ads read-only integration
6. LinkedIn read-only integration
7. Slack notification and decision flow
8. Lightweight run history page

If time pressure is severe, ship to the first design partner as soon as steps 1 through 7 work reliably.

---

## 10. MVP Positioning Sentence

**Meeseks prevents paid media teams from shipping broken campaigns by validating launch settings before spend goes live and recording who approved the launch.**

---

## 11. One-Sentence Guardrail

Do not add any feature unless it clearly improves one of these four outcomes:

- spend protection
- manual QA time reduction
- attribution hygiene
- approval accountability