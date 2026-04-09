# Agent Routing Directive

## Purpose
Classify incoming requests and route them to the correct department agent.

## Routing Matrix

| Intent Keywords | Route To |
|----------------|----------|
| build, code, implement, integrate, framework, agent, executor, tool, API, SDK, approval, eval, test, orchestrate | ENGINEERING |
| customer, interview, discovery, requirement, spec, roadmap, feedback, idea, pipeline, use case | PRODUCT |
| deploy, ship, monitor, alert, infrastructure, trace, observe, Railway, Docker, health check | DELIVERY |
| blog, post, case study, content, social, LinkedIn, Twitter, open source, publish | CONTENT |
| sprint, status, coordinate, route, decompose, blocker, progress, checkpoint | ORCHESTRATOR |

## Ambiguous Requests

If a request spans multiple departments:
1. Identify the primary intent
2. Route to the primary department
3. Note secondary departments that may need to contribute
4. Orchestrator coordinates the handoff

## Rules

- Never route a request to a department that doesn't own the domain
- If unsure, ask for clarification rather than guessing
- Cross-department work always goes through Orchestrator
