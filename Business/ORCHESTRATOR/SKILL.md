---
name: orchestrator
description: "Orchestrator Agent — master coordinator for the AgentForge 14-day blitz sprint. Routes tasks across departments, manages sprint cadence, decomposes multi-domain requests, and tracks progress."
---

# ORCHESTRATOR — Skill Command Sheet

> **Adopt this department to gain**: Sprint management, task routing, cross-department coordination, task decomposition, progress tracking, daily rhythm enforcement, and VPS access coordination.

> **Governance**:
> - **DOE owner**: Orchestrator is the only department allowed to reorganise files across `Business/` so the DOE pattern stays coherent.
> - **SKILL.md owner**: Orchestrator is the only department allowed to rewrite department `SKILL.md` files when structure changes.
> - **Department boundary**: Other agents may update domain content inside their lane, but they do not own cross-department structure.

---

## Skills

### Skill 1 — Sprint Management
| Layer | Path |
|-------|------|
| Directive | `directives/sprint-management.md` |
| Resources | `resources/sprint-plan.md` |
| Use for | Managing the 14-day blitz cadence: daily planning, checkpoint validation, blocker resolution |

### Skill 2 — Agent Routing & Intent Classification
| Layer | Path |
|-------|------|
| Directive | `directives/agent-routing.md` |
| Use for | Classifying user intent and routing to the correct department |

**Routing Matrix**:

| Intent | Route To |
|--------|----------|
| Build an agent, agent design, scaffolding, MCP integration, agent eval | ENGINEERING |
| Customer discovery, requirements, roadmap, feedback | PRODUCT |
| Deployment, monitoring, infrastructure, tracing | DELIVERY |
| Blog post, case study, social content, open source | CONTENT |
| Sprint status, coordination, routing, structure | ORCHESTRATOR (self) |

### Skill 3 — Task Decomposition
| Layer | Path |
|-------|------|
| Directive | `directives/task-decomposition.md` |
| Use for | Breaking complex requests into atomic sub-tasks with dependency DAGs |

### Skill 4 — Status Reporting
| Layer | Path |
|-------|------|
| Directive | `directives/status-reporting.md` |
| Resources | `resources/daily-log.md` |
| Use for | Cross-department status aggregation and progress reporting |

### Skill 5 — Error Handling & Blockers
| Layer | Path |
|-------|------|
| Directive | `directives/blocker-resolution.md` |
| Use for | Detecting, triaging, and resolving blockers that threaten sprint progress |

### Skill 6 — VPS Connectivity & Remote Operations
| Layer | Path |
|-------|------|
| Directive | `directives/vps-connectivity.md` |
| Resources | `resources/connection-reference.md`, `resources/.env.example` |
| Use for | Establishing SSH access from this workspace, validating remote reachability, and coordinating safe diagnostics or VPS deploy steps |

**What this covers**:
- SSH access based on the root `.env` values
- Connection probing before interactive login
- Safe remote inspection and log checks
- Coordinated production changes with DELIVERY when required

---

## Sprint Tasks (14-Day Blitz)

### Every Day — Daily Rhythm

| Time | Activity |
|------|----------|
| First 15 min | Review: what shipped yesterday, what is blocked, what is the single most important thing today |
| Morning block | Build. The hardest or most uncertain task of the day goes here. |
| Afternoon block | Build. Integrations, tests, or deployment work. |
| Last 30 min | Log: 1 observation for the idea pipeline + 1 short-form post or note about what you built today |
| Evening (optional) | Explore: 1 high-quality source, video, or competitor teardown. Cap at 30 min. |

### Ongoing: Idea Pipeline

| Day | Pipeline Activity |
|-----|-------------------|
| Every day | Log at least 1 observation: "I noticed X is painful / broken / manual in Y context" |
| Day 6 | Review observations. Do any pass the 5 entry criteria? If yes, create Gate 0 entries. |
| Day 12 | Review all Gate 0 entries. Run Gate 1 quick-kill on the best 2–3. |
| Day 14 | Pick the strongest idea and decide: Gate 2 deep research or second build cycle. |

---

## Anti-Patterns to Avoid

| Trap | Why It Feels Productive | Why It Is Not |
|------|------------------------|---------------|
| Watching AI YouTube all day | Feels like learning | You absorb opinions, not skills. Cap at 30 min/day. |
| Building a framework before building a product | Feels like infrastructure | Premature abstraction. Build the thing, extract the pattern later. |
| Chasing every new model release | Feels like staying current | Model upgrades rarely change what you should build. Check monthly, not daily. |
| Perfecting Sprint 1 before moving on | Feels like quality | 80% working is enough. Move forward, come back later. |
| Selling before you have a demo | Feels like validation | You need proof, not promises. Build first, sell from evidence. |
| Building in private | Feels safe | Nobody knows you exist. Ship publicly from day one. |

---

## Success Metrics at Day 14

| Metric | Minimum | Strong |
|--------|---------|--------|
| Working integrations | 5 | 7+ |
| Agent runs logged with traces | 100 | 500+ |
| Real users of at least one deployed system | 1 | 3+ |
| Public posts / artefacts | 3 | 8+ |
| Gate 0 ideas generated from building | 2 | 5+ |
| Gate 1 survivors | 1 | 2+ |
| Inbound conversations from public content | 1 | 5+ |

---

## Cross-Department Links

| Department | Orchestrator Provides | Orchestrator Needs |
|------------|----------------------|-------------------|
| ALL | Task routing, status aggregation, blocker resolution | Task status updates |
| ENGINEERING | Sprint priorities, integration sequence | Build progress, technical blockers |
| PRODUCT | Customer interview scheduling, pipeline reviews | Discovery insights, feedback data |
| DELIVERY | Deployment go/no-go decisions, remote-access coordination | Health metrics, incident reports |
| CONTENT | Content scheduling, publish decisions | Content drafts, artefact readiness |
