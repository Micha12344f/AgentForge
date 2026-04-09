# Sprint Management Directive

## Purpose
Manage the 14-day blitz sprint cadence. Ensure every day has a clear priority, every checkpoint is validated, and blockers are resolved immediately.

## Sprint Structure

| Days | Phase | Lead Agent | Key Deliverables |
|------|-------|------------|-----------------|
| 1–2 | Agent Core + First Integrations | ENGINEERING | Working agent executor + 3 integrations |
| 3–4 | Remaining Integrations + Approval Engine | ENGINEERING | 5 integrations + approval flow |
| 5–6 | Observability + Evaluation | DELIVERY | Tracing + eval harness + 30 test cases |
| 7–9 | Multi-Agent Orchestration | ENGINEERING + ORCHESTRATOR | DAG orchestrator + full pipeline demo |
| 10–12 | First Real Deployment | DELIVERY + PRODUCT | Live system + monitoring + user feedback |
| 13–14 | Case Study + Public Artefacts | CONTENT + PRODUCT | Public proof + pipeline review |

## Daily Rhythm

| Time | Activity |
|------|----------|
| First 15 min | Review: what shipped yesterday, what is blocked, what is the single most important thing today |
| Morning block | Build: hardest or most uncertain task |
| Afternoon block | Build: integrations, tests, deployment |
| Last 30 min | Log: 1 observation for pipeline + 1 content note |
| Evening (optional) | Explore: 1 source/video/teardown, cap 30 min |

## Checkpoint Validation

At the end of each phase, validate the checkpoint criteria listed in the lead agent's SKILL.md. If a checkpoint is not met, the Orchestrator must decide: extend or move forward with known gaps.

## Blocker Resolution

1. Identify the blocker clearly (technical? credential? design decision?)
2. If solvable in <30 min → solve immediately
3. If longer → log it, work around it, revisit in evening block
4. If critical path → escalate and pause dependent work
