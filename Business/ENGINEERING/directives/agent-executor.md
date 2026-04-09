# Agent Executor Design

## Purpose
Define the architecture and behaviour of the single-agent executor — the core building block of every AgentForge workflow.

## Requirements

1. **Task Input**: Accept a structured task (goal, context, available tools, constraints)
2. **Decomposition**: Break the task into ordered steps with dependency awareness
3. **Tool Calling**: Execute tool calls with structured input/output
4. **Trace Logging**: Log every decision, tool call, result, latency, and cost as JSON
5. **Error Recovery**: Implement retry → fallback → escalate chain
6. **Structured Output**: Return results in a predictable schema

## Architecture Decisions

- Trace format: JSON lines, one entry per action
- State management: In-memory for single runs, Supabase for persistence
- Tool interface: Standardised `Tool` class with `name`, `description`, `parameters`, `execute()`
- LLM routing: Use shared `llm_router` for model selection (cost vs capability)

## Acceptance Criteria

- [ ] Can execute a 3-step task using at least 2 real tools
- [ ] Produces a complete trace log for the entire run
- [ ] Recovers from a simulated tool failure without crashing
- [ ] Returns structured output matching the expected schema
