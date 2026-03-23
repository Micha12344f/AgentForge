# Agent Routing

> Routing decision matrix and intent classification rules.

## Intent → Agent Mapping

| Intent Pattern | Target Agent | Priority |
|---------------|-------------|----------|
| Email, campaign, sequence, send | Email-marketing | P1 |
| Revenue, MRR, commission, invoice | Finance | P1 |
| KPI, metrics, analytics, GA4, report | Analytics | P1 |
| Deploy, release, VPS, cron, health | Orchestrator (self) | P0 |
| Roadmap, compliance, legal, strategy | Strategy | P2 |
| Lead, CRM, demo, pipeline, close | Sales | P1 |
| LinkedIn, Twitter, content, SEO | Marketing | P2 |
| Support, chat, ticket, onboarding | Customer Support | P2 |

## Multi-Agent Routing

When a request spans multiple departments:
1. Decompose into atomic sub-tasks via `task_decomposer.py`
2. Route each sub-task to the appropriate agent
3. Coordinate execution via `cross_agent_coordinator.py`
4. Aggregate results and report back

## Escalation Rules

- If agent fails 2× on same task → escalate to Orchestrator
- If Orchestrator can't resolve → alert via Discord + log incident
