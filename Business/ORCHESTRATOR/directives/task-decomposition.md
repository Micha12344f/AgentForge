# Task Decomposition

> How to break complex requests into dependency DAGs.

## Decomposition Rules

1. **Atomic tasks**: Each sub-task should be completable by a single agent
2. **Dependencies**: Identify which tasks depend on outputs of others
3. **Parallelism**: Independent tasks can run simultaneously
4. **Ordering**: Build a DAG (Directed Acyclic Graph) of task dependencies

## Example: "Generate and send the monthly board report"

```
[1] Analytics: Pull monthly KPIs          ──┐
[2] Finance: Calculate MRR + P&L           ──┼→ [4] Strategy: Compile board deck
[3] Growth: Summarize pipeline metrics     ──┘   → [5] Email-marketing: Send to board
```

Tasks 1, 2, 3 are independent (parallel). Task 4 depends on all three. Task 5 depends on 4.

## Task Schema

```python
{
    "id": "task-001",
    "agent": "analytics",
    "action": "pull_monthly_kpis",
    "depends_on": [],
    "status": "pending",
    "result": None
}
```
