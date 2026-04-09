---
name: engineering
description: "Engineering Agent — core technical agent for AgentForge. Builds the agent framework, integrations, approval engine, evaluation harness, and multi-agent orchestration system."
---

# ENGINEERING — Skill Command Sheet

> **Adopt this department to gain**: Agent framework development, tool integration building, approval engine design, evaluation and observability systems, and multi-agent orchestration architecture.

> **Governance**: Engineering owns engineering content. Orchestrator alone owns cross-department DOE restructuring.

---

## Skills

### Skill 1 — Agent Executor Framework
| Layer | Path |
|-------|------|
| Directive | `directives/agent-executor.md` |
| Executions | `executions/agent_executor.py` |
| Resources | `resources/architecture-decisions.md` |
| Use for | Building the core single-agent executor: task decomposition, tool calling, structured output, error recovery |

**What this covers**:
- Single-agent executor that takes a task, decomposes into steps, calls tools, returns structured output
- Trace log format (JSON): every decision, tool call, result, latency, cost
- Error recovery: retry, fallback, escalate
- Prompt engineering and reliability patterns

### Skill 2 — Tool Integrations
| Layer | Path |
|-------|------|
| Directive | `directives/integrations.md` |
| Executions | `executions/integrations/` |
| Resources | `resources/integration-specs/` |
| Use for | Building production-grade integration clients for target business tools |

**Target integrations (5 core)**:
1. **HubSpot CRM** — contacts, deals, lifecycle events, webhooks
2. **Slack** — messages, channels, slash commands, interactive messages
3. **Google Workspace** — Gmail send/read, Drive file ops, Calendar CRUD
4. **Asana or Linear** — tasks, projects, status updates, webhooks
5. **Stripe or Xero** — invoices, payments, reconciliation events

**Per integration**:
- Working CRUD + auth + rate-limit handling
- Integration test suite: mock + live sandbox
- Auth flow documentation: OAuth2, API key, service account

### Skill 3 — Approval Engine (Human-in-the-Loop)
| Layer | Path |
|-------|------|
| Directive | `directives/approval-engine.md` |
| Executions | `executions/approval_engine.py` |
| Resources | `resources/approval-patterns.md` |
| Use for | Building trust checkpoints into every agent workflow |

**What this covers**:
- Approval queue service: API + Slack-based approval UI
- Agent SDK function: `await_approval(action, context, urgency)`
- Audit log: timestamps, approver identity, decision, rationale
- Timeout + escalation: no response in X minutes → escalate to next approver

### Skill 4 — Evaluation & Observability
| Layer | Path |
|-------|------|
| Directive | `directives/eval-observability.md` |
| Executions | `executions/eval_harness.py` `executions/tracing_service.py` |
| Resources | `resources/eval-test-cases/` |
| Use for | Measuring agent performance, debugging failures, tracking costs |

**What this covers**:
- Tracing service: every agent action logged (input, output, latency, cost, outcome, approval status)
- Evaluation harness: define expected outcomes per task, run agent, compare, score pass/fail
- Summary reports: pass rate, failure categories, cost per task, latency distribution
- Regression alerting: pass rate drops below threshold → alert

### Skill 5 — Multi-Agent Orchestration
| Layer | Path |
|-------|------|
| Directive | `directives/multi-agent-orchestration.md` |
| Executions | `executions/orchestrator_engine.py` |
| Resources | `resources/dag-patterns.md` |
| Use for | Coordinating multiple agents on end-to-end workflows |

**What this covers**:
- DAG-based multi-agent orchestrator with shared state object
- Failure handling: node failure preserves completed work, retries or escalates
- Agent handoffs: clear ownership, conflict resolution
- End-to-end workflow execution across integrations

---

## Sprint Tasks (14-Day Blitz)

### Day 1–2: Agent Core + First Integrations

**Morning — Agent Executor**:
- [ ] Single-agent executor: takes a task, decomposes into steps, calls tools, returns structured output
- [ ] Trace log format (JSON): every decision, tool call, result, latency, cost
- [ ] Error recovery: retry, fallback, escalate

**Afternoon — Integrations (start 3 of 5)**:
- [ ] HubSpot CRM client: contacts, deals, lifecycle events, webhooks
- [ ] Slack client: messages, channels, slash commands, interactive messages
- [ ] Google Workspace client: Gmail send/read, Drive file ops, Calendar CRUD

**Checkpoint**: Agent can execute a 3-step task using real tools and produce a trace. 3 integrations have working CRUD + auth + rate-limit handling.

### Day 3–4: Remaining Integrations + Approval Engine

**Morning — Integrations (finish)**:
- [ ] Asana or Linear client: tasks, projects, status updates, webhooks
- [ ] Stripe or Xero client: invoices, payments, reconciliation events
- [ ] Integration test suite: mock + live sandbox for all 5
- [ ] Auth flow docs: OAuth2, API key, service account per integration

**Afternoon — Human-in-the-Loop**:
- [ ] Approval queue service: API + Slack-based approval UI
- [ ] Agent SDK function: `await_approval(action, context, urgency)`
- [ ] Audit log: timestamps, approver identity, decision, rationale
- [ ] Timeout + escalation: no response in X minutes → escalate to next approver

**Checkpoint**: 5 production-grade integrations ready. Approval engine working: agent pauses → human approves in Slack → agent resumes → trace logged.

### Day 7–9: Multi-Agent Orchestration

**Build**: Multi-agent system where 3+ agents coordinate on a real end-to-end workflow.

**Target workflow**: New client signed →
1. Agent A reads deal from HubSpot, creates project in Asana
2. Agent B drafts welcome email in Gmail, pauses for approval
3. Agent C schedules kickoff in Google Calendar
4. Agent D posts internal summary in Slack
5. Orchestrator tracks DAG completion, handles failures

**Deliverables**:
- [ ] DAG-based multi-agent orchestrator with shared state object
- [ ] Failure handling: node failure preserves completed work, retries or escalates
- [ ] End-to-end demo running on real sandbox accounts (not mocks)
- [ ] All runs traced and scored through the eval harness

**Checkpoint**: Full pipeline runs: HubSpot → Asana → Gmail (approval) → Calendar → Slack. Every step traced, scored, auditable.
