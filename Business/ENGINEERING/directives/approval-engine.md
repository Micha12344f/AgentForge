# Approval Engine Directive

## Purpose
Build a human-in-the-loop approval system that lets agents pause execution, request human review, and resume after approval. Trust is the product — every production agent needs approval checkpoints.

## Core Components

### 1. Approval Queue Service
- REST API for creating, listing, and resolving approval requests
- Each request: action description, context, urgency level, requesting agent ID
- States: pending → approved / rejected / escalated / timed_out

### 2. Slack Approval UI
- Post approval requests as interactive Slack messages
- Buttons: Approve / Reject / Request More Info
- Thread for discussion before decision

### 3. Agent SDK Function
```python
result = await agent.await_approval(
    action="Send welcome email to client@example.com",
    context={"deal_id": "123", "template": "onboarding-welcome"},
    urgency="normal",  # normal | high | critical
    timeout_minutes=30
)
```

### 4. Audit Log
- Every approval decision logged: timestamp, approver identity, decision, rationale
- Queryable for compliance and review

### 5. Timeout & Escalation
- No response in X minutes → escalate to next approver
- Configurable escalation chains per workflow type

## Acceptance Criteria

- [ ] Agent can pause execution and post an approval request to Slack
- [ ] Human can approve/reject via Slack button
- [ ] Agent resumes with the decision and continues workflow
- [ ] Full audit trail in trace log
- [ ] Timeout escalation works
