# Agency Closed-Won to First-Value Orchestrator

Status: Proposed build spec  
Date: 2026-04-10  
Owner: ORCHESTRATOR to PRODUCT to ENGINEERING handoff  
Primary build consumer: Engineering agent

## 1. Product Summary

AgentForge's first commercial product is a multi-tenant B2B SaaS platform for performance and growth agencies. The platform starts working the moment a new client is marked closed-won and coordinates everything required to get that client from signed deal to first visible value without email chaos.

This product is not a generic chat assistant. It is an operational system that watches for onboarding events, launches a structured workflow, coordinates people and software tools, follows up on missing items, and creates a clear operational record of what has been done, what is blocked, and what is still missing.

The product's core promise is:

Turn a signed client into a fully provisioned, kickoff-ready, measurable account in 7-14 days with less manual chasing and less operational risk.

## 2. The Problem

Small and mid-sized agencies usually win clients inside a CRM, but the real work begins across many disconnected systems after the sale. New client onboarding is often slowed down by:

- missing account access
- scattered intake information
- delayed first payment confirmation
- unclear internal ownership
- manual project setup in Asana or ClickUp
- repeated follow-up emails to clients
- slow kickoff scheduling
- weak visibility for agency leadership

The result is operational drag during the most trust-sensitive part of the relationship. The client has already paid, but the agency has not shown progress yet. Internally, account managers and ops people become human glue between CRM, email, project management, Slack, calendars, payment systems, and analytics.

## 3. Ideal Customer Profile

### Primary customer

Performance and growth agencies with:

- 5-50 staff
- 5-30 new client onboardings per month
- recurring retainers or project-based service packages
- a modern SaaS stack rather than a custom internal system

### Common stack

- HubSpot for CRM
- Asana for delivery operations
- Slack for internal communication
- Google Workspace for email and calendar
- Stripe or Xero for invoicing and payment confirmation
- Google Analytics, Google Ads, Meta, LinkedIn, TikTok, or similar platforms for client-side access and reporting

### Buyer

- agency founder
- COO or operations lead
- head of client services

### Daily user

- account manager
- onboarding manager
- operations coordinator

### External participant

- client-side marketing lead or business owner

## 4. Product Definition

The platform is an onboarding orchestration layer that sits above the agency's existing tools.

It does five things:

1. Detects when a new client onboarding should start.
2. Creates and manages the onboarding run as a tracked workflow.
3. Collects what the agency needs from the client.
4. Sets up internal delivery systems and communications.
5. Surfaces blockers, exceptions, and approvals in one place.

The product should feel like an AI onboarding operations manager with strict safety rails, not like a free-form bot with broad system access.

## 5. What the Product Is Not

The first version is not:

- a replacement for HubSpot
- a replacement for Asana
- a full PSA platform
- a general-purpose agency operating system
- a chatbot-first product
- an autonomous agent allowed to delete, archive, or broadly mutate production data

The product should be opinionated, narrow, and operationally reliable.

## 6. Core User Outcomes

### For agency leadership

- Know the status of every onboarding at a glance.
- Reduce time from deal won to kickoff-ready state.
- Reduce dependency on manual follow-up work.
- Standardize onboarding quality across accounts and team members.

### For account and ops teams

- Stop managing onboarding from inboxes and memory.
- Stop manually creating the same projects, tasks, and channels.
- Get clear alerts on what is blocked and who owns the next action.

### For clients

- Receive a clear, professional onboarding experience.
- Know exactly what to provide and by when.
- Avoid long back-and-forth email chains.

## 7. The Core Workflow Boundary

The product starts at closed-won and ends at first-value.

### Start condition

A deal is marked closed-won in the CRM and the agency chooses to start onboarding automatically or manually confirms start.

### End condition for v1

An onboarding run is considered at first-value when all of the following are true:

- contract is complete or explicitly marked not required
- first payment is confirmed or explicitly marked not required
- client intake form is complete
- required account access items are collected or explicitly waived
- internal project is created from template
- internal team ownership is assigned
- kickoff is scheduled
- a 30/60/90-day plan or kickoff plan is attached
- a KPI dashboard placeholder or live dashboard link is available

## 8. Detailed Workflow

### Step 1: Deal trigger

The system detects a qualifying deal in HubSpot. It pulls account, contact, package, service line, deal owner, close date, and agreed start date. It creates a new onboarding run in AgentForge.

Output:

- onboarding run created
- initial status set to active
- workflow template selected based on service type

### Step 2: Commercial readiness check

The system verifies whether contract and first payment conditions are satisfied. For beta customers this can be manual confirmation if direct integrations are not yet live.

Output:

- commercial status marked ready, pending, or blocked
- blockers shown in dashboard

### Step 3: Client kickoff packet

The system sends the client a branded onboarding link. This is the client's single place to complete intake, upload assets, review open requests, and track onboarding progress.

Output:

- client portal access created
- intake request sent
- due date set

### Step 4: Intake completion

The client fills in structured onboarding fields. Example fields include business description, target audience, current channels, existing assets, brand files, billing contact, main stakeholders, and reporting expectations.

Output:

- intake data saved to onboarding run
- missing fields flagged
- internal summary generated for agency team

### Step 5: Access collection

The system requests the exact platform access needed for the purchased service. The platform should track each access item as an object with a status such as not requested, requested, partially complete, complete, blocked, or waived.

Examples:

- Google Ads access
- Meta Business Manager access
- Google Analytics access
- website CMS access
- tag manager access
- LinkedIn page or ad account access

Output:

- access checklist created from service template
- each access item tracked individually
- incomplete access highlighted automatically

### Step 6: Internal team assignment

The system assigns the onboarding owner and delivery participants according to agency rules or via manual confirmation. At minimum, the platform should support assigning an account lead, an operator, and a specialist owner.

Output:

- roles assigned to onboarding run
- responsibility visible in dashboard
- internal notifications sent

### Step 7: Internal workspace provisioning

The system creates the operational project structure for the agency. In v1 this should include Asana project creation from template, standard tasks, dates, and owners. Slack channel creation is optional in the earliest beta if implementation speed requires deferral.

Output:

- Asana project created from correct template
- standard tasks assigned
- key dates populated
- internal reference links stored in onboarding run

### Step 8: Kickoff scheduling

The system proposes or books kickoff windows based on agency-side rules and available calendars. In beta, scheduling can begin with meeting suggestion generation and human approval before send.

Output:

- kickoff draft prepared or booked
- agenda attached
- attendees recorded

### Step 9: Plan generation

The system prepares a first 30/60/90-day plan or equivalent kickoff plan using package type, intake data, and service template inputs. The final plan may be AI-drafted but must be human-editable.

Output:

- plan attached to onboarding run
- approval status tracked

### Step 10: Dashboard readiness

The system stores the location of the reporting dashboard or creates a dashboard placeholder record that confirms reporting setup is underway. The first version does not need full analytics provisioning if that slows the wedge.

Output:

- dashboard link or placeholder captured
- onboarding marked first-value complete

## 9. Product Experience

### Experience 1: Agency admin setup

The agency connects core systems, chooses templates, defines required onboarding items by service type, sets reminder rules, and configures branding.

### Experience 2: Operations dashboard

The agency sees every onboarding run in a clear status board. Each run should show:

- client name
- service type
- start date
- current status
- blockers
- overdue items
- next required action
- owner

### Experience 3: Client portal

The client sees:

- welcome message
- checklist of required items
- upload and form completion steps
- access request steps
- current progress
- contact path if stuck

### Experience 4: Exception handling

If the client replies with incomplete, messy, or ambiguous information, the system should classify the issue, propose the next action, and either send a safe follow-up automatically or route the case to a human.

## 10. Product Principles

1. Reliability over novelty.
2. Workflow state matters more than chat.
3. The system should narrow chaos, not create new operational ambiguity.
4. Most automation should be deterministic.
5. AI should be used where language understanding or judgment is genuinely needed.
6. High-risk writes must be constrained and reviewable.

## 11. Agentic Design Stance

This product should not be built as one unrestricted autonomous agent.

The correct shape is:

- event-driven workflow engine for long-running state
- deterministic orchestration for known steps
- bounded AI tasks for language-heavy exception handling
- restricted MCP tools for all external system writes

### Deterministic responsibilities

- state transitions
- checklist generation
- reminder timing
- project template selection from explicit rules
- due date calculation
- audit logging
- approval gate enforcement

### AI-assisted responsibilities

- summarizing intake responses
- classifying client replies
- drafting follow-up messages
- identifying likely blockers from incomplete information
- suggesting next best action for ops users
- drafting kickoff plan from structured inputs

### AI must not directly control

- destructive platform actions
- broad administrative settings
- payment movement
- irreversible record deletion
- unreviewed high-risk client communications in early versions

## 12. Trust and Safety Model

Trust is a core product requirement, not a later enhancement.

### Safety rule

The model must never have raw, unrestricted API power against external systems.

### Required implementation pattern

All external writes must flow through custom or wrapped MCP services with explicit tool allowlists.

Examples of allowed v1 tools:

- create_asana_project
- create_asana_task
- update_asana_task_due_date
- create_slack_channel
- post_slack_message
- send_gmail_template
- create_calendar_event
- update_hubspot_deal_property

Examples of deliberately absent v1 tools:

- delete_asana_project
- archive_asana_workspace
- delete_slack_channel
- delete_hubspot_record
- refund_payment
- remove_user_permissions

### Additional safety requirements

- idempotency on all write operations where possible
- explicit tenant scoping on every tool call
- approval gates for high-risk actions
- dry-run mode for onboarding templates during setup
- immutable audit log of every external write
- human override for blocked runs

## 13. Recommended MCP Strategy

### Principle

The MCP layer is the control surface, not just an integration convenience.

### Recommended v1 MCP services

1. CRM MCP service
Purpose: read closed-won events, contact data, company data, service package, and update onboarding status fields.

2. Project management MCP service
Purpose: create projects and tasks from templates and update safe fields only.

3. Messaging MCP service
Purpose: send templated emails and internal Slack notifications with strict action boundaries.

4. Calendar MCP service
Purpose: create kickoff scheduling options and confirmed events.

5. Billing status MCP service
Purpose: read invoice and payment status only.

### MCP requirements

- each service must expose typed, narrow, documented tools
- no destructive tools in v1
- every response must return audit-friendly metadata
- tenant context must be explicit, never inferred
- production transport should support Dockerized streamable HTTP MCP

## 14. Integration Scope

### V1 required integrations

1. HubSpot
Scope:
- read deal, company, and primary contact data
- optionally update onboarding status field or note

2. Asana
Scope:
- create project from template
- create and assign tasks
- update selected task metadata

3. Slack
Scope:
- send internal notifications
- optionally create client-specific channels

4. Google Workspace
Scope:
- send onboarding emails
- create calendar events

5. Stripe or Xero
Scope:
- read payment or invoice status only

### V1.5 optional integrations

- PandaDoc or DocuSign for contract state
- Leadsie-style access handling or direct access request flows
- Databox or Looker Studio link registration
- ClickUp as secondary PM system

### Beta fallback strategy

Where public OAuth approval is slow, the platform must support pilot customers through private app credentials, manual status confirmation, or narrower integration modes until public app review is complete.

## 15. Functional Requirements

### FR-1 Multi-tenant workspaces

The platform must isolate agencies as separate tenants with separate users, integrations, templates, branding, and data.

### FR-2 Workflow templates

The platform must support reusable onboarding templates by service type.

### FR-3 Onboarding run creation

The platform must create a tracked onboarding run from a CRM trigger or manual start.

### FR-4 Checklist engine

The platform must store onboarding steps and child requirements as stateful items with due dates, owners, and statuses.

### FR-5 Client portal

The platform must provide a client-facing portal for form completion, uploads, and status visibility.

### FR-6 Reminder engine

The platform must send follow-ups based on rules, deadlines, and missing inputs.

### FR-7 Internal provisioning

The platform must create internal work objects such as projects, tasks, and internal notifications.

### FR-8 Approval gates

The platform must support human review before selected high-risk actions.

### FR-9 Audit log

The platform must record every major state change and every external write.

### FR-10 Exception queue

The platform must surface blocked or ambiguous cases to internal users with recommended next actions.

### FR-11 Reporting dashboard

The platform must provide summary and per-run visibility for status, overdue items, blockers, completion times, and conversion to first-value.

### FR-12 White-label basics

The platform must support customer branding on email and portal surfaces at least at a basic logo, color, and sender-name level.

## 16. Non-Functional Requirements

1. The platform must be safe by default.
2. The platform must support long-running workflows that can span days or weeks.
3. The platform must tolerate external API retries and partial failures.
4. The platform must provide traceability for every automation step.
5. The platform must be implementable as a cloud SaaS product with Dockerized MCP services.
6. The platform must support human recovery from any failed step.

## 17. Recommended System Architecture

This section is guidance for Engineering, not a hard framework mandate.

### Core components

1. Web application
Purpose: agency admin UI, ops dashboard, client portal.

2. Core API service
Purpose: tenant management, onboarding runs, templates, permissions, audit access.

3. Workflow engine
Purpose: long-running state, reminders, retries, scheduled checks, approval waits.

4. Agent service
Purpose: bounded AI tasks such as summarization, message drafting, classification, and next-action suggestions.

5. MCP integration layer
Purpose: safe, narrow access to external systems.

6. Postgres database
Purpose: source of truth for tenants, runs, steps, statuses, logs, templates, approvals.

7. Object storage
Purpose: uploaded files and portal assets.

8. Observability stack
Purpose: traces, logs, task history, cost visibility.

### Architectural rule

The workflow engine owns process state. The agent service does not own long-term memory or orchestration state.

## 18. Suggested Data Model

Minimum core entities:

- Agency
- AgencyUser
- ClientCompany
- ClientContact
- IntegrationConnection
- WorkflowTemplate
- TemplateStep
- OnboardingRun
- OnboardingStep
- AccessRequest
- IntakeResponse
- InternalAssignment
- ApprovalRequest
- ExternalActionLog
- NotificationEvent
- KickoffEvent
- DashboardRecord

## 19. Permissions Model

### Agency roles

- Admin: manage billing, templates, integrations, users
- Ops Manager: manage runs, approve actions, edit templates
- Account Manager: operate assigned runs, send approved follow-ups, view status
- Read-only leadership: dashboard visibility only

### Client access

- portal guest or authenticated contact
- restricted to their own onboarding items and uploads

## 20. Success Metrics

### Product metrics

- median time from closed-won to kickoff-ready
- median time from closed-won to first-value
- percentage of runs completed without manual ops setup
- percentage of runs blocked by missing client access
- follow-up reduction per onboarding run
- project setup time saved per run

### Business metrics

- activation rate for connected tenants
- onboarding template usage rate
- retention after 90 days
- paid pilot to subscription conversion rate

## 21. V1 Build Sequence

### Phase 1: Pilot foundation

Goal: support white-glove pilot customers with safe automation.

Scope:

- tenant model
- onboarding run model
- HubSpot intake or manual trigger
- Asana project creation
- Gmail notifications
- dashboard with statuses and blockers
- audit log
- human approval gates for risky actions

### Phase 2: Client portal and richer workflow

Goal: reduce manual chasing and centralize client inputs.

Scope:

- branded client portal
- intake forms
- upload handling
- reminder engine
- access request tracking
- kickoff scheduling support

### Phase 3: AI exception handling and plan drafting

Goal: improve operational leverage without sacrificing trust.

Scope:

- classify ambiguous client replies
- generate follow-up drafts
- summarize intake into internal brief
- draft kickoff or 30/60/90 plan

## 22. Explicit Out-of-Scope for V1

- full analytics pipeline provisioning
- cross-agency benchmarking marketplace
- broad multi-department agency operations platform
- support for every PM and CRM tool on day one
- destructive write actions to third-party systems
- fully autonomous client communications with no review path

## 23. Risks

### Product risk

If the product becomes too broad, it will lose the wedge and collapse into generic work management software.

### Trust risk

If the system appears able to delete or corrupt agency systems, adoption will slow sharply.

### Integration risk

Public OAuth approvals for Google, Meta, LinkedIn, and some others may slow launch.

### Operational risk

If workflow state is buried inside free-form agent memory instead of an explicit workflow engine, reliability will break.

## 24. Unconfirmed Assumptions

These assumptions are reasonable enough for a first engineering pass but should be validated before hardening the build plan.

- HubSpot is the first CRM, not Salesforce.
- Asana is the first PM system, not ClickUp.
- Gmail and Google Calendar are more urgent than Outlook support.
- White-label branding is needed early, but full custom domains are not required in v1.
- First-value should be defined operationally, not by campaign performance outcome.
- Billing integration can begin as read-only.
- Destructive or archive actions should remain completely unavailable in v1.

## 25. Engineering Handoff Direction

Engineering should treat this as a workflow product with an agent layer, not an agent product that happens to touch workflows.

That means the initial build should optimize for:

- explicit state machines
- safe MCP-controlled actions
- auditability
- tenant isolation
- fast pilot deployment
- narrow but reliable integrations

The correct first build is a constrained, trustworthy onboarding operations system for agencies. Generalized agent autonomy is not the goal of v1.

## 26. Requested Engineering Deliverables

Engineering should treat this document as the source description for the initial build and produce the following deliverables next:

1. Architecture proposal for a multi-tenant SaaS with workflow engine, agent service, and Dockerized MCP services.
2. Agent Card and risk classification for each bounded AI component used in the platform.
3. MVP data model and database schema draft.
4. Workflow state machine definition for onboarding runs and step transitions.
5. MCP tool specs for HubSpot, Asana, Google Workspace, Slack, and billing-status integrations.
6. UI plan for agency setup, ops dashboard, and client portal.
7. Evaluation plan for AI-assisted tasks such as reply classification, summary generation, and follow-up drafting.
8. Safe pilot rollout plan with approval gates, dry-run behavior, and audit logging.
