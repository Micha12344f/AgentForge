---
name: delivery
description: "Delivery Agent — deployment, monitoring, observability, production operations, and infrastructure management for AgentForge."
---

# DELIVERY — Skill Command Sheet

> **Adopt this department to gain**: Deployment automation, production monitoring, tracing and observability, alerting, infrastructure management, and operational reliability.

> **Governance**: Delivery owns delivery content. Orchestrator alone owns cross-department DOE restructuring.

---

## Skills

### Skill 1 — Deployment Automation
| Layer | Path |
|-------|------|
| Directive | `directives/deployment.md` |
| Executions | `executions/deploy.py` |
| Resources | `resources/deployment-checklist.md` |
| Use for | Shipping agent systems to production — containers, services, DNS, health checks |

**What this covers**:
- Container builds and deployment (Railway, Docker)
- Service configuration and environment management
- Health check and readiness probes
- Rollback procedures

### Skill 2 — Monitoring & Alerting
| Layer | Path |
|-------|------|
| Directive | `directives/monitoring.md` |
| Executions | `executions/monitor.py` |
| Resources | `resources/alert-rules.md` |
| Use for | Knowing when agents fail before users do |

**What this covers**:
- Agent health monitoring: is it running, is it succeeding?
- Alert routing: Discord + email alerts on failure
- Usage dashboards: runs per day, cost per run, success rate, avg latency
- Incident response procedure

### Skill 3 — Tracing & Observability
| Layer | Path |
|-------|------|
| Directive | `directives/tracing.md` |
| Executions | `executions/trace_viewer.py` |
| Resources | `resources/trace-format.md` |
| Use for | Understanding what agents did, why they failed, and how much it cost |

**What this covers**:
- Trace storage and querying
- Cost tracking per agent run
- Failure analysis and categorisation
- Performance trending over time

### Skill 4 — Infrastructure Management
| Layer | Path |
|-------|------|
| Directive | `directives/infrastructure.md` |
| Resources | `resources/infra-inventory.md` |
| Use for | Managing the underlying infrastructure: Railway, VPS, Cloudflare, DNS |

---

## Sprint Tasks (14-Day Blitz)

### Day 5–6: Observability + Evaluation

- [ ] Build tracing service: every agent action logged (input, output, latency, cost, outcome, approval status)
- [ ] Build evaluation harness: define expected outcomes per task, run agent, compare, score pass/fail
- [ ] Create at least 30 test cases across 3+ workflow types
- [ ] Build summary report: pass rate, failure categories, cost per task, latency distribution
- [ ] Set up regression alerting: pass rate drops below threshold → Discord/Slack alert

**Checkpoint**: Can run any agent workflow and get a scored trace with cost and failure analysis. First batch of eval results showing where agents succeed and where they break.

### Day 10–12: First Real Deployment — Delivery Role

- [ ] Deploy one complete agentic workflow for a real use case
- [ ] Set up monitoring: know when it fails before the user does (Discord + email alerts)
- [ ] Build usage dashboard: runs per day, cost per run, success rate, avg latency
- [ ] Verify system runs on real data with real users or real triggers
- [ ] Confirm at least 1 real user besides yourself

**Checkpoint**: One agentic system running in production with monitoring. At least 1 real user.
