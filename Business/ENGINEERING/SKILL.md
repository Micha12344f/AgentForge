---
name: engineering
description: "Engineering Agent — builds AI agents from scratch inside the AgentForge workspace. Uses smolagents as the default runtime, plans MCP integrations, designs evals, enforces safety boundaries, and researches current AI engineering standards."
---

# ENGINEERING — Skill Command Sheet

> **Adopt this department to gain**: Agent design and scaffolding, requirements elicitation, smolagents runtime wiring, MCP integration planning, API documentation research, evaluation design, safety and sandboxing, and web-based technology research.

> **Governance**: Engineering owns agent-building content. Orchestrator alone owns cross-department DOE restructuring and `agents.md` / `SKILL.md` registration.

---

## Skills

### Skill 1 — Requirements Elicitation
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Section: Requirements) |
| Resources | `resources/agent-builder-checklist.md` |
| Use for | Cutting through vague requests to extract precise agent requirements before any design work begins |

**What this covers**:
- Mandatory question protocol: who, what outcome, what systems, what data, what risk, what exists, what success looks like, what it must never do
- Agent Card completion: name, department, purpose, agency level, risk tier, owner
- Decision Gate: determining whether the workflow actually needs an agent or should be a script/router
- Never-assume policy: the agent always asks before building

### Skill 2 — Agent Design (smolagents-first)
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Sections: Design Process, Workflow Patterns, System Prompt) |
| Resources | `resources/agent-builder-checklist.md` |
| Use for | Designing agents using smolagents as the default runtime, selecting workflow patterns, and writing system prompts |

**What this covers**:
- `CodeAgent` as default runtime; `ToolCallingAgent` only when code execution is unnecessary
- Tool set design: ≤ 7 tools, non-overlapping descriptions, typed I/O, auth, rate limits
- Workflow pattern selection: code agent → tool-calling → graph → event-driven → multi-agent
- System prompt skeleton: identity, tools block, workflow instructions, guardrails, handoff rules
- Artifact pack generation: `.agent.md`, directive, execution stub, eval cases, reference docs

### Skill 3 — MCP Integration Planning
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Section: MCP Strategy) |
| Executions | `executions/agentforge_mcp_server.py` |
| Resources | `resources/agent-builder-checklist.md` |
| Use for | Planning and building MCP integrations for agent tools: pre-built servers, wrappers, or custom FastMCP servers |

**What this covers**:
- MCP strategy decision matrix: pre-built official → pre-built aggregator → custom AgentForge → hybrid wrapper
- Searching MCP registries (glama.ai, smithery.ai, modelcontextprotocol/servers) for existing servers
- Scaffolding custom MCP servers with `FastMCP` from the Python MCP SDK
- smolagents integration: `MCPClient` and `ToolCollection.from_mcp()` with `structured_output=True`
- Transport selection: `streamable-http` for deployed, `stdio` for local development

### Skill 4 — API Documentation Research & Scraping
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Section: MCP Strategy) |
| Use for | Researching API documentation for target systems to design tools or scaffold MCP servers |

**What this covers**:
- Web-searching official API docs for target SaaS/services
- Fetching and analyzing API references: endpoints, auth patterns, rate limits, data schemas
- Extracting the minimum viable API surface an agent needs
- Documenting auth flows, required scopes, and rate limit strategies in agent reference resources

### Skill 5 — Evaluation Design
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Section: Evaluation Cases) |
| Resources | `resources/agent-builder-checklist.md` |
| Use for | Designing evaluation test suites that ship with every agent |

**What this covers**:
- Minimum 8 eval cases per agent: 3 happy-path, 2 edge, 1 refusal, 1 multi-step, 1 failure-recovery
- Structured case format: id, input, expected_behaviour, pass_criteria, tools_expected
- Evals test agent judgment, not just tool correctness
- Trace-based evaluation: verify trace schema compliance, cost tracking, latency bounds

### Skill 6 — Safety & Execution Boundaries
| Layer | Path |
|-------|------|
| Directive | `directives/agent-builder.md` (Section: Anti-Patterns, Course-to-Production Gap) |
| Resources | `resources/agent-builder-checklist.md` |
| Use for | Defining what agents must never do, sandboxing code execution, and mapping risk tiers to approval flows |

**What this covers**:
- Explicit refusal boundaries per agent
- Max-step limits, timeouts, and cost caps
- Code execution risk classification: `LocalPythonExecutor` = dev-only; production = Docker, E2B, Modal, Blaxel, Pyodide+Deno
- Risk tier → approval mapping: low=self-serve, medium=peer review, high=human-in-the-loop, critical=multi-party sign-off
- Import allow-lists, output size limits, and execution timeouts for code agents

### Skill 7 — Web Research (Current Standards)
| Layer | Path |
|-------|------|
| Directive | (no dedicated directive — this is an operational stance applied to all other skills) |
| Use for | Verifying framework versions, MCP server availability, and AI engineering best practices before making design decisions |

**What this covers**:
- Searching official docs, GitHub repos, HuggingFace docs, and ModelContextProtocol spec before framework decisions
- Verifying MCP server maintenance status and compatibility before recommending
- Staying current with smolagents releases, MCP SDK updates, and AI engineering standards
- Preferring reputable sources over cached knowledge for rapidly evolving technologies

---

## File Map

| Path | Purpose |
|------|---------|
| `directives/agent-builder.md` | Master SOP for designing and scaffolding agents |
| `executions/agent_builder.py` | smolagents runtime scaffold with MCP client wiring |
| `executions/agentforge_mcp_server.py` | Custom FastMCP server skeleton for shared capabilities |
| `resources/agent-builder-checklist.md` | Quick-reference checklist for every agent build |

---

## Agent Build Workflow (Summary)

```
Request → Elicit Requirements → Decision Gate → Design → Build Artifacts → Validate → Hand Off
         (Skill 1)             (Skill 1)       (Skills 2-6)  (Skill 2)     (Skill 5-6)  (Orchestrator)
```

Every step uses **Skill 7 (Web Research)** as needed to verify current standards.
