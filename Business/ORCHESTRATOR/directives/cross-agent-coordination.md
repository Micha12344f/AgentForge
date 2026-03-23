# Cross-Agent Coordination

> Multi-agent workflow patterns for complex requests.

## Workflow Patterns

### Sequential Pipeline
```
Request → Agent A → Agent B → Agent C → Result
```
Example: "Send a revenue report" → Analytics (pull data) → Finance (format report) → Email-marketing (send)

### Parallel Fan-Out
```
Request → Agent A ─┐
        → Agent B ─┼→ Aggregate → Result
        → Agent C ─┘
```
Example: "Status report" → All agents report health simultaneously → Orchestrator aggregates

### Conditional Routing
```
Request → Classify → if (type A) → Agent A
                   → if (type B) → Agent B
                   → if (multi)  → Decompose → route each
```

## Handoff Protocol

1. Orchestrator creates task with unique ID
2. Target agent receives task context + expected output format
3. Agent completes work and returns structured result
4. Orchestrator validates result matches expected format
5. If dependent task exists, passes result to next agent
