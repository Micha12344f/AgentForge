---
name: product
description: "Product Agent — customer discovery, use case mapping, requirements definition, roadmap management, and feedback loop operations for AgentForge."
---

# PRODUCT — Skill Command Sheet

> **Adopt this department to gain**: Customer discovery, use case decomposition, requirements writing, product roadmap management, user feedback collection, and idea pipeline operations.

> **Governance**: Product owns product content. Orchestrator alone owns cross-department DOE restructuring.

---

## Skills

### Skill 1 — Customer Discovery
| Layer | Path |
|-------|------|
| Directive | `directives/customer-discovery.md` |
| Executions | `executions/interview_tracker.py` |
| Resources | `resources/interview-templates/` |
| Use for | Running customer interviews, logging pain points, validating assumptions |

**What this covers**:
- Interview script templates for different personas (COO, Ops Manager, Finance Lead)
- Pain point logging and pattern extraction
- Assumption tracking: what we believe vs what we've verified
- Competitive intelligence from customer conversations

### Skill 2 — Use Case Mapping
| Layer | Path |
|-------|------|
| Directive | `directives/use-case-mapping.md` |
| Executions | `executions/workflow_decomposer.py` |
| Resources | `resources/use-case-library/` |
| Use for | Breaking real business processes into agent-suitable workflows |

**What this covers**:
- Department-by-department workflow decomposition
- Identifying which steps are agent-automatable vs human-required
- Approval checkpoint placement
- Integration dependency mapping per use case

### Skill 3 — Requirements & Specs
| Layer | Path |
|-------|------|
| Directive | `directives/requirements.md` |
| Resources | `resources/specs/` |
| Use for | Writing clear product requirements from discovery insights |

### Skill 4 — Roadmap Management
| Layer | Path |
|-------|------|
| Directive | `directives/roadmap.md` |
| Resources | `resources/roadmap.md` |
| Use for | Prioritising features, managing the build sequence, tracking progress |

### Skill 5 — Feedback Loops
| Layer | Path |
|-------|------|
| Directive | `directives/feedback-loops.md` |
| Executions | `executions/feedback_collector.py` |
| Resources | `resources/feedback-log.md` |
| Use for | Collecting and acting on user feedback from deployments |

### Skill 6 — Idea Pipeline Operations
| Layer | Path |
|-------|------|
| Directive | `directives/idea-pipeline.md` |
| Resources | `resources/pipeline/` |
| Use for | Running Gate 0–4 evaluations on new ideas that emerge from building |

---

## Sprint Tasks (14-Day Blitz)

### Day 10–12: First Real Deployment — Product Role

- [ ] Define the deployment use case: which workflow, which tools, which user
- [ ] Write the user-facing workflow documentation
- [ ] Collect first round of user feedback
- [ ] Log pain points and opportunities discovered during deployment
- [ ] Run idea pipeline check: any new Gate 0 entries from deployment learnings?

### Day 13–14: Pipeline Review — Product Role

- [ ] Log all observations and pain points from the 14 days
- [ ] Run Gate 0 entry check on any ideas that emerged
- [ ] Re-evaluate idea-002 (Departmental Agentic OS): still valid? Better wedge discovered?
- [ ] Decide: push to next sprint, pivot, or run a second 14-day cycle

**Checkpoint**: Clear view of what to build next. Idea pipeline grounded in building, not theory.
