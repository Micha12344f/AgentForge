# Agent Builder — Engineering Directive

> **Owner**: ENGINEERING  
> **Purpose**: Standard operating procedure for designing and scaffolding new AI agents from the ground up within the AgentForge workspace.  
> **Trigger**: Any request to create a new agent, add agent capabilities, or evaluate whether a workflow should be agentic.

> **Runtime default**: AgentForge builds agents on `smolagents` unless the workflow requires explicit graph control that justifies another runtime.

> **Core principle**: Never assume. Always elicit precise requirements before design begins. Always verify technology choices against current documentation.

---

## 0. Requirements Elicitation — The Never-Assume Protocol

**This is the most important section of this directive.** Before any design work begins, the Engineering agent must cut through vague or incomplete requests and extract precise, actionable requirements.

### Why This Exists

Vague requests produce vague agents. An instruction like "create an agent that does emails" could mean a dozen different things. Without rigorous elicitation, you will build the wrong agent, miss critical safety boundaries, or over-engineer a solution to a problem that doesn't need an agent at all.

### Mandatory Questions

For **every** agent build request, the following questions must be answered before proceeding to design. Use `vscode/askQuestions` to collect answers efficiently.

| # | Question | Why it matters |
|---|----------|---------------|
| 1 | **Who is the end user?** (internal team member, external customer, automated pipeline, other agent) | Determines trust level, UI needs, and error handling strategy |
| 2 | **What is the specific outcome?** (not "does emails" but "drafts onboarding welcome emails from a CRM trigger and queues them for human review") | Forces precision; prevents scope creep during build |
| 3 | **What systems does it touch?** (exact SaaS tools, APIs, databases, file systems) | Drives tool design and MCP integration planning |
| 4 | **What data does it read?** (sources, formats, sensitivity) | Determines auth scopes and data handling requirements |
| 5 | **What data does it write or mutate?** (targets, side effects) | Determines risk tier and approval requirements |
| 6 | **What is the risk if it goes wrong?** (sends wrong email to customer = high; logs an internal note = low) | Maps directly to risk tier and sandboxing needs |
| 7 | **What already exists?** (current workflow, scripts, manual process it replaces) | Avoids rebuilding what works; identifies real gaps |
| 8 | **What does success look like?** (measurable: "95% of drafted emails need zero edits") | Becomes the basis for evaluation cases |
| 9 | **What must it never do?** (explicit refusal boundaries) | Becomes the guardrails in the system prompt |
| 10 | **What is the expected volume/frequency?** (10/day vs 10,000/day) | Determines whether cost caps, rate limits, or batching matter |

### Handling Pushback

If the user pushes back on questions or says "just build it":
1. Explain that each question exists to prevent a specific failure mode
2. Offer your best-guess answer and ask the user to confirm or correct
3. Never silently assume — document every assumption explicitly and flag it as unconfirmed

### Output of Elicitation

A completed **Agent Card**:

```yaml
name: <agent-slug>
department: <ENGINEERING | PRODUCT | DELIVERY | CONTENT | ORCHESTRATOR>
purpose: <one sentence: what this agent does and for whom>
agency_level: <☆☆☆ | ★☆☆ | ★★☆ | ★★★ | ★★★+>
risk_tier: <low | medium | high | critical>
owner: <human or team accountable for this agent>
end_user: <who uses this agent>
systems: <list of external systems>
success_metric: <measurable outcome>
refusal_boundaries: <what it must never do>
unconfirmed_assumptions: <anything the user didn't explicitly confirm>
```

---

## 1. Web Research Mandate — Verify Before You Build

AI agent frameworks, MCP servers, and API surfaces evolve rapidly. Cached knowledge is unreliable for version-specific decisions.

### When to Research

- **Before choosing a framework feature**: verify it still exists in the current version
- **Before recommending an MCP server**: check it is maintained, compatible, and not deprecated
- **Before designing tool auth**: fetch the current API docs for scopes, rate limits, and auth patterns
- **When the user asks about a technology you are uncertain about**: search first, then answer
- **When scaffolding a custom MCP server**: check the current `mcp` Python SDK patterns

### Where to Research

| Source | Use for |
|--------|---------|
| Official framework docs (smolagents, MCP SDK) | Runtime APIs, breaking changes, migration guides |
| GitHub repos (huggingface/smolagents, modelcontextprotocol/python-sdk) | Latest releases, issues, examples |
| MCP registries (glama.ai, smithery.ai) | Discovering pre-built MCP servers |
| modelcontextprotocol/servers | Official reference MCP servers |
| Target SaaS API docs | Auth flows, endpoints, rate limits, data schemas |
| HuggingFace docs | Model availability, inference API changes |

### How to Research

1. Use web search to find the canonical page
2. Fetch the page and extract the specific information needed
3. If the information contradicts your cached knowledge, trust the fetched version
4. Document the source URL in the agent's reference resource file

---

## 2. Why Smolagents Is the Default

AgentForge defaults to **smolagents** for first-build agents because it gives us the shortest path from design to working runtime without hiding too much.

**Benefits**:
- **Code-first actions**: `CodeAgent` writes Python actions directly, which reduces tool-call overhead and performs better than JSON-only tool routing on many multi-step tasks
- **Small enough to inspect**: the framework stays intentionally small, so the team can read the core abstractions instead of debugging through deep framework layers
- **MCP-native tool loading**: `MCPClient` and `ToolCollection.from_mcp()` let us pull tools from local or remote MCP servers with minimal glue code
- **Model-agnostic**: we are not locked into one inference provider or one model family
- **Easy escalation path**: start with a single `CodeAgent`, move to managed multi-agent only when the task actually needs specialist delegation
- **Explicit security model**: sandboxing is a first-class concern; code execution is powerful, but it is not treated as safe by default

**Operational stance**:
- Default to `CodeAgent`
- Use `ToolCallingAgent` only when code execution is unnecessary or prohibited
- Treat `LocalPythonExecutor` as non-production and non-boundary security
- Prefer real sandboxes such as Docker, E2B, Modal, Blaxel, or Pyodide+Deno for untrusted code execution

---

## 3. When to Use This Directive

Use this directive when:
- A new business workflow is proposed that may benefit from an AI agent
- An existing department needs a new specialised agent
- You need to decide whether a task even warrants an agent (vs. a deterministic script)

Do **not** use this directive to modify cross-department DOE structure or rewrite SKILL.md files — that requires Orchestrator approval.

---

## 4. The Decision Gate: Does This Need an Agent?

Before building anything, classify the workflow on the agency spectrum (adapted from Hugging Face / smolagents):

| Level | Pattern | Example | Build as |
|-------|---------|---------|----------|
| ☆☆☆ | Fixed pipeline, no LLM decisions | ETL job, cron task | Script or workflow |
| ★☆☆ | LLM picks one of N predefined paths | Intent router, classifier | Router function |
| ★★☆ | LLM selects tools + arguments dynamically | Single-shot tool call | Tool-calling agent |
| ★★★ | LLM iterates until objective met | Multi-step research, complex reasoning | Multi-step agent (ReAct) |
| ★★★+ | One agent delegates to other agents | Cross-department workflows | Multi-agent system |

**Rule**: Only build an agent (★★☆ or higher) when the task genuinely requires dynamic tool selection or iterative reasoning. If a deterministic chain of prompts solves it, use that.

---

## 5. Agent Design Process

### Step 1 — Define the Agent Card

Every new agent starts with a structured card:

```yaml
name: <agent-slug>
department: <ENGINEERING | PRODUCT | DELIVERY | CONTENT | ORCHESTRATOR>
purpose: <one sentence: what this agent does and for whom>
agency_level: <☆☆☆ | ★☆☆ | ★★☆ | ★★★ | ★★★+>
risk_tier: <low | medium | high | critical>
owner: <human or team accountable for this agent>
```

**Risk tier definitions**:
| Tier | Criteria | Approval requirement |
|------|----------|---------------------|
| Low | Read-only, no external side effects | Self-serve |
| Medium | Writes to internal systems (Notion, Slack) | Peer review |
| High | Writes to customer-facing systems, moves money, sends emails | Human-in-the-loop per action |
| Critical | Modifies infrastructure, deletes data, production deploys | Orchestrator + human approval gate |

### Step 2 — Design the Tool Set

For each tool the agent needs:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Snake_case function name |
| `description` | Yes | What it does — this is what the LLM reads to decide when to use it |
| `arguments` | Yes | Typed inputs with descriptions |
| `outputs` | Yes | Return type and shape |
| `side_effects` | Yes | What it changes in the world (or "none" for read-only) |
| `auth` | Yes | How it authenticates (API key, OAuth2, service account) |
| `rate_limits` | If applicable | Throttle or retry strategy |

**Tool design principles** (from HF course + production experience):
1. Tools must have clear, non-overlapping descriptions — the LLM uses the description to pick tools
2. Fewer, well-scoped tools beat many vague ones
3. Every tool with side effects must be idempotent or explicitly documented as non-idempotent
4. Tool outputs should be concise — large payloads fill the context window and degrade planning
5. Consider MCP (Model Context Protocol) for tools that may be shared across frameworks
6. For MCP-backed tools, prefer servers that expose strong descriptions and `inputSchema`; enable structured output when available

### Step 3 — Choose the Workflow Pattern

| Pattern | When to use | Framework affinity |
|---------|-------------|-------------------|
| **Code Agent** | Expressive multi-step tasks, composable tool calls, data processing | smolagents `CodeAgent` |
| **Tool-Calling Agent** | Simple tool dispatch, function-calling LLMs available | smolagents `ToolCallingAgent`, LlamaIndex `FunctionAgent` |
| **Explicit Graph** | Predictable branching, human-in-the-loop checkpoints, compliance workflows | LangGraph `StateGraph` |
| **Event-Driven Workflow** | Async steps, clear stage transitions, RAG pipelines | LlamaIndex `Workflow` / `AgentWorkflow` |
| **Multi-Agent Hierarchy** | Task requires distinct specialisations with separate context windows | smolagents managed agents, LlamaIndex `AgentWorkflow`, LangGraph sub-graphs |

**Default recommendation**: Start with `smolagents` `CodeAgent`. Upgrade to multi-agent only when context-window pressure or specialisation demands it.

### Step 3A — Choose the MCP Strategy

MCP is the standard interface we use to make tools portable across agents and clients. It is not the same thing as DOE.

| Strategy | When to use | AgentForge stance |
|----------|-------------|-------------------|
| **Pre-built official MCP server** | The target SaaS already has a maintained MCP server and its default tool surface is good enough | First choice |
| **Pre-built aggregator MCP server** | You need broad SaaS coverage fast across many apps | Good for prototyping; review auth, quotas, and audit story before production |
| **Custom AgentForge MCP server** | We need normalized schemas, tenant boundaries, approval hooks, trace IDs, or business-specific prompts/resources | Build when the capability will be reused by multiple agents or clients |
| **Hybrid wrapper MCP** | A third-party MCP server exists but needs policy, logging, or output normalization in front of it | Preferred production pattern when governance matters |

**Selection rules**:
1. Use a pre-built official MCP server if it already exposes the capability cleanly
2. Build a custom MCP server when the value is not just API access, but **AgentForge policy**: approvals, auditability, tenancy, or domain normalization
3. Wrap external MCP servers when we need to keep their coverage but enforce our own trace schema and approval logic
4. Prefer `streamable-http` for deployed MCP servers and `stdio` for local development
5. In `smolagents`, explicitly set `structured_output=True` for MCP connections instead of relying on a changing default

**Smolagents integration standard**:
- Use `ToolCollection.from_mcp(..., trust_remote_code=True, structured_output=True)` for scoped tool bundles
- Use `MCPClient(..., structured_output=True)` when the application owns the connection lifecycle
- Allow multiple MCP servers only when the tool namespaces stay clear and non-overlapping

### Step 4 — Write the System Prompt Skeleton

Every agent needs a system prompt that includes:

1. **Identity**: Who the agent is and its boundaries
2. **Tools block**: Auto-generated from tool definitions (name, description, arguments, outputs)
3. **Workflow instructions**: The Think → Act → Observe cycle, output format (JSON / code / function-call), and stop conditions
4. **Guardrails**: What the agent must NOT do (e.g., no financial advice, no data deletion without approval)
5. **Handoff rules**: When and how to escalate to a human or another agent

Template structure:
```
You are {name}, a {purpose} agent for AgentForge.

## Tools Available
{auto-generated tool descriptions}

## Workflow
You operate in a Think → Act → Observe loop.
- Think: reason about what to do next
- Act: call exactly one tool with the correct arguments, then STOP generating
- Observe: read the tool result and decide your next step
- When the objective is met, call final_answer with your result

## Rules
- {risk-tier-specific rules}
- {department-specific guardrails}
- If uncertain, ask the user rather than guessing
```

### Step 5 — Define Evaluation Cases

Every agent ships with a minimum eval set:

| Case type | Minimum count | Purpose |
|-----------|--------------|---------|
| Happy path | 3 | Core use cases work correctly |
| Edge case | 2 | Boundary inputs, missing data, ambiguous requests |
| Refusal | 1 | Agent correctly refuses out-of-scope requests |
| Multi-step | 1 | Agent chains 2+ tools in sequence |
| Failure recovery | 1 | Tool returns error; agent retries or escalates |

Each case is a structured entry:
```yaml
- id: eval-001
  input: "What is the weather in Paris?"
  expected_behaviour: "Agent calls weather_tool with location='Paris' and returns a natural language summary"
  pass_criteria: "Response contains temperature and condition"
  tools_expected: [weather_tool]
```

### Step 6 — Define Trace and Observability Requirements

Every agent must produce traces compatible with OpenTelemetry:

| Field | Required | Description |
|-------|----------|-------------|
| `trace_id` | Yes | Unique run identifier |
| `agent_name` | Yes | Which agent executed |
| `steps[]` | Yes | Array of {thought, action, tool_name, tool_args, observation, latency_ms, token_count} |
| `total_cost` | Yes | Estimated LLM cost for the run |
| `outcome` | Yes | success / failure / escalated / timeout |
| `approval_events[]` | If applicable | Human approval decisions with timestamps |

### Step 7 — Generate the Artifact Pack

The builder produces these files:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Agent definition | `.github/agents/{name}.agent.md` | VS Code agent config with tools, handoffs, description |
| Directive | `Business/{DEPT}/directives/{name}.md` | SOP for what the agent does |
| Execution stub | `Business/{DEPT}/executions/{name}.py` | Starter `smolagents` code with tool definitions and agent setup |
| Eval cases | `Business/{DEPT}/resources/eval-{name}.yaml` | Test cases for the eval harness |
| Resource docs | `Business/{DEPT}/resources/{name}-reference.md` | API docs, auth flows, integration notes |
| Optional MCP server | `Business/ENGINEERING/executions/{name}_mcp.py` | Shared MCP surface when the capability should be reused by multiple agents or external MCP clients |

### Step 8 — Review and Activate

| Risk tier | Review process |
|-----------|---------------|
| Low | Engineering self-review, merge |
| Medium | Engineering peer review → merge |
| High | Engineering review + Orchestrator approval → merge |
| Critical | Engineering review + Orchestrator approval + stakeholder sign-off → merge |

After review:
1. Orchestrator updates `Business/agents.md` and relevant `SKILL.md` files
2. Agent is added to the VS Code agent roster
3. Initial eval run is executed and logged
4. Agent enters a 48-hour monitored trial before full activation

---

## 6. Anti-Patterns

| Trap | Why it fails |
|------|-------------|
| **Assuming requirements instead of asking** | Produces the wrong agent. A vague prompt like "build an email agent" has 12+ interpretations. Elicit first, always. |
| Building the agent framework before building one agent | Premature abstraction. Build the first agent end-to-end, extract patterns second. |
| Giving an agent 15+ tools | Context window bloat degrades planning. Cap at 7 tools; split into multi-agent if more needed. |
| Skipping the "does this need an agent?" gate | Most workflows are deterministic. Don't use an LLM where an if-statement works. |
| No eval cases at launch | You cannot improve what you cannot measure. Ship evals with the agent. |
| Trusting code agents without sandboxing | LLM-generated code can be harmful. Use framework sandboxes (smolagents) or explicit allow-lists. |
| Hardcoding the LLM provider | Agents should work across providers. Use model-agnostic interfaces. |
| Treating MCP as business architecture | MCP standardises tool and context exchange, but it does not replace workflow ownership, directives, governance, or review gates |
| **Using cached knowledge for version-specific decisions** | Frameworks and APIs change. Search current docs before recommending a feature, MCP server, or auth pattern. |

---

## 7. Framework Selection Quick Reference

Based on the full Hugging Face Agents Course analysis:

| Framework | Strengths | Weaknesses | Best for |
|-----------|-----------|------------|----------|
| **smolagents** | Lightweight (~1k LOC), code-first, MCP-native, model-agnostic, fast prototyping | Less explicit flow control, newer ecosystem | Default AgentForge runtime, rapid iteration, code-heavy tasks, internal tools |
| **LangGraph** | Explicit state graphs, persistence, human-in-the-loop, production-ready | More boilerplate, requires LangChain familiarity | Compliance workflows, branching logic, customer-facing agents |
| **LlamaIndex** | Best RAG tooling, event-driven workflows, strong component ecosystem | Heavier setup, async-first learning curve | Data-intensive agents, document analysis, retrieval-heavy workflows |

**AgentForge default**: Start with `smolagents` for v1 agents. Move to LangGraph only when the workflow needs explicit graph state, pause/resume checkpoints, or complex branching. Use LlamaIndex when the agent is primarily a RAG system over business data.

---

## 8. Course-to-Production Gap Checklist

These are areas where the HF Agents Course methodology must be extended for production use:

| HF Course Teaches | Production Requires (AgentForge Adds) |
|-------------------|--------------------------------------|
| ReAct loop basics | Configurable max-step limits, timeout handling, cost caps |
| Tool definitions via decorators | Auth, rate-limiting, idempotency, error codes per tool |
| System prompt design | Versioned prompts, A/B testing, guardrail injection |
| Traces via OpenTelemetry + Langfuse | Mandatory trace schema, retention policy, cost alerting |
| Offline eval with datasets | CI/CD eval gates, regression detection, eval-before-deploy |
| Multi-agent via managed agents | Ownership boundaries per department, shared state contracts, failure recovery |
| Code agent sandboxing | Import allow-lists, execution timeouts, output size limits |
| Hub-based sharing | Internal artifact registry, access control, version pinning |
| Single-user notebook flow | Multi-tenant runtime, auth context propagation, audit trails |
| Function-calling fine-tuning (bonus) | Model selection criteria, fallback chains, provider-agnostic interfaces |
| MCP connectivity | Trusted server registry, transport choice, structured output, auth rotation, wrapper layers for policy enforcement |
