# Evaluation & Observability Directive

## Purpose
Build systems to measure agent performance, debug failures, and track costs. You cannot improve what you cannot measure.

## Components

### 1. Tracing Service
- Log every agent action: input, output, latency, cost, outcome, approval status
- Storage: Supabase table (`agent_traces`)
- Query interface for filtering by agent, workflow, date, outcome

### 2. Evaluation Harness
- Define expected outcomes per task type
- Run agent on test cases, compare actual vs expected
- Score: pass/fail per step, overall pass rate
- At least 30 test cases across 3+ workflow types by Day 6

### 3. Summary Reports
- Pass rate by workflow type
- Failure category breakdown (tool error, LLM hallucination, timeout, approval rejected)
- Cost per task (LLM tokens + API calls)
- Latency distribution (p50, p90, p99)

### 4. Regression Alerting
- Automated runs on test suite (daily or on-commit)
- Pass rate drops below threshold → Discord/Slack alert
- Cost exceeds budget per run → alert

## Acceptance Criteria

- [ ] Can run any agent workflow and get a scored trace
- [ ] Cost tracking works per run
- [ ] Failure analysis categorises errors correctly
- [ ] Regression alerts fire on threshold breach
