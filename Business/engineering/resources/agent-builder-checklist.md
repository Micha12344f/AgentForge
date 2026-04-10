# Agent Builder — Quick Reference Checklist

Use this during every agent build to ensure nothing is missed.

---

## Requirements Elicitation (NEVER SKIP)

- [ ] Read `Business/engineering/directives/agent-builder.md` (Section 0)
- [ ] **Who is the end user?** — answered and documented
- [ ] **What is the specific outcome?** — precise, not vague
- [ ] **What systems does it touch?** — exact SaaS tools, APIs, databases listed
- [ ] **What data does it read?** — sources, formats, sensitivity classified
- [ ] **What data does it write or mutate?** — targets and side effects listed
- [ ] **What is the risk if it goes wrong?** — risk scenario described
- [ ] **What already exists?** — current workflow or manual process documented
- [ ] **What does success look like?** — measurable metric defined
- [ ] **What must it never do?** — explicit refusal boundaries listed
- [ ] **What is the expected volume/frequency?** — scale documented
- [ ] All answers collected via `vscode/askQuestions` (not assumed)
- [ ] If any answer was inferred, it is flagged as `unconfirmed_assumption`

## Decision Gate

- [ ] Workflow classified on agency spectrum (☆☆☆ to ★★★+)
- [ ] If ☆☆☆ or ★☆☆: recommend script/router, stop here
- [ ] Decision documented with justification

## Agent Card

- [ ] `name` — slug format, no spaces
- [ ] `department` — one of ENGINEERING / PRODUCT / DELIVERY / CONTENT / ORCHESTRATOR
- [ ] `purpose` — one sentence, includes "for whom"
- [ ] `agency_level` — ★☆☆ through ★★★+
- [ ] `risk_tier` — low / medium / high / critical
- [ ] `owner` — human or team accountable
- [ ] `end_user` — who uses this agent
- [ ] `systems` — list of external systems
- [ ] `success_metric` — measurable outcome
- [ ] `refusal_boundaries` — what it must never do
- [ ] `unconfirmed_assumptions` — anything not explicitly confirmed

## Web Research (Before Design Decisions)

- [ ] Current smolagents version and relevant features verified via web search
- [ ] MCP servers for target systems searched (glama.ai, smithery.ai, modelcontextprotocol/servers)
- [ ] Target system API docs fetched and reviewed for auth, endpoints, rate limits
- [ ] Any version-specific claims verified against official docs
- [ ] Source URLs documented in agent reference resource

## Tool Design

- [ ] Each tool has: name, description, arguments (typed), outputs, side_effects, auth
- [ ] Tool count ≤ 7 (split to multi-agent if exceeded)
- [ ] Descriptions are clear and non-overlapping
- [ ] Side-effect tools are idempotent (or documented as non-idempotent)
- [ ] Auth method specified per tool
- [ ] Rate limits / retry strategy documented where applicable
- [ ] Each capability classified as: native function / pre-built MCP tool / wrapper MCP tool / custom AgentForge MCP tool

## MCP Strategy

- [ ] Each external system has a chosen MCP strategy: pre-built / wrapper / custom / none
- [ ] Pre-built MCP servers verified as maintained and compatible
- [ ] Custom MCP servers justified (reuse, policy, approvals, tenancy)
- [ ] `structured_output=True` set explicitly for all MCP connections
- [ ] Transport chosen: `streamable-http` for deployed, `stdio` for local dev
- [ ] `trust_remote_code=True` used only for vetted MCP servers

## Workflow Pattern

- [ ] Pattern selected: Code Agent / Tool-Calling / Graph / Event-Driven / Multi-Agent
- [ ] `smolagents` `CodeAgent` chosen by default unless graph state or workflow complexity justifies another runtime
- [ ] Framework selected with justification
- [ ] Max-step limit defined
- [ ] Timeout defined
- [ ] Cost cap defined (max tokens or max $ per run)

## System Prompt

- [ ] Identity section
- [ ] Tools block (auto-generated from tool definitions)
- [ ] Workflow instructions (Think → Act → Observe, stop conditions)
- [ ] Guardrails (what NOT to do — from refusal boundaries)
- [ ] Handoff rules (when to escalate)

## Evaluation Cases

- [ ] ≥ 3 happy-path cases
- [ ] ≥ 2 edge cases
- [ ] ≥ 1 refusal case (out-of-scope request correctly refused)
- [ ] ≥ 1 multi-step case (2+ tool calls chained)
- [ ] ≥ 1 failure-recovery case (tool error → agent retries or escalates)
- [ ] Each case has: id, input, expected_behaviour, pass_criteria, tools_expected
- [ ] Evals test agent judgment, not just tool correctness

## Safety & Execution Boundaries

- [ ] Refusal boundaries encoded in system prompt guardrails
- [ ] Max-step limit enforced
- [ ] Timeout enforced
- [ ] Cost cap enforced
- [ ] Code execution classified: dev-only (`LocalPythonExecutor`) or production sandbox (Docker / E2B / Modal)
- [ ] Import allow-list defined (if code agent)
- [ ] Output size limits defined (if code agent)

## Trace & Observability

- [ ] OpenTelemetry-compatible trace schema
- [ ] Fields: trace_id, agent_name, steps[], total_cost, outcome
- [ ] Approval events tracked (if high/critical risk)
- [ ] Logging integration specified (Langfuse, console, or custom)

## Artifact Pack

- [ ] `.github/agents/{name}.agent.md` — created
- [ ] `Business/{DEPT}/directives/{name}.md` — created
- [ ] `Business/{DEPT}/executions/{name}.py` — created (smolagents wiring)
- [ ] `Business/{DEPT}/resources/eval-{name}.yaml` — created
- [ ] `Business/{DEPT}/resources/{name}-reference.md` — created (includes source URLs from research)
- [ ] `Business/engineering/executions/{name}_mcp.py` — created when MCP capability should be shared

## Review Gate

- [ ] Risk tier → correct review process applied
- [ ] Low: self-review
- [ ] Medium: peer review
- [ ] High: Engineering + Orchestrator approval
- [ ] Critical: Engineering + Orchestrator + stakeholder sign-off
- [ ] Orchestrator notified to update `agents.md` and `SKILL.md`

## Post-Launch

- [ ] Initial eval run executed and logged
- [ ] 48-hour monitored trial started
- [ ] Cost and latency within expected bounds
- [ ] No refusal-case violations in trial period
