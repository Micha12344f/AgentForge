# Multi-Agent Orchestration Directive

## Purpose
Build a system where 3+ agents coordinate on end-to-end workflows using the integrations and approval engine.

## Architecture

### DAG-Based Orchestrator
- Workflows defined as directed acyclic graphs (DAGs)
- Each node: one agent + one tool action + optional approval gate
- Edges: data dependencies between nodes
- Shared state object passed through the DAG

### Target Workflow: New Client Onboarding

```
Deal Closed (HubSpot)
    │
    ▼
Agent A: Read deal → Create project (Asana)
    │
    ├──▶ Agent B: Draft welcome email (Gmail) → [APPROVAL] → Send
    │
    ├──▶ Agent C: Schedule kickoff (Calendar)
    │
    └──▶ Agent D: Post internal summary (Slack)
    │
    ▼
Orchestrator: Verify all complete → Update deal stage (HubSpot)
```

### Failure Handling
- Node failure preserves completed work (no rollback of successful nodes)
- Failed node: retry N times → escalate to human
- Orchestrator logs failure and continues with independent nodes

### State Object
```json
{
  "workflow_id": "uuid",
  "trigger": { "source": "hubspot", "deal_id": "123" },
  "nodes": {
    "create_project": { "status": "completed", "output": {...} },
    "send_email": { "status": "awaiting_approval", "approval_id": "..." },
    "schedule_meeting": { "status": "pending" },
    "post_summary": { "status": "pending" }
  },
  "created_at": "...",
  "updated_at": "..."
}
```

## Acceptance Criteria

- [ ] DAG orchestrator runs the full onboarding workflow
- [ ] Failure at any node doesn't break other independent nodes
- [ ] All runs traced end-to-end through the eval harness
- [ ] Demo runs on real sandbox accounts (not mocks)
