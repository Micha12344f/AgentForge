# Hedge Edge — smolagents Autonomous Business OS on VPS

## Implementation Plan

> **Framework**: Hugging Face `smolagents` with MCP tool servers
> **Runtime**: hedge-vps (WSL Ubuntu via Cloudflare tunnel)
> **LLM Backend**: Existing `llm_router.py` providers (Gemini, Groq, OpenRouter)
> **Self-Healing**: Agent feedback loops with error capture → auto-retry → escalation

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [MCP Server Design](#2-mcp-server-design)
3. [Agent Definitions](#3-agent-definitions)
4. [Self-Annealing System](#4-self-annealing-system)
5. [Cron Schedule](#5-cron-schedule)
6. [VPS Directory Layout](#6-vps-directory-layout)
7. [Implementation Phases](#7-implementation-phases)
8. [File Manifest](#8-file-manifest)

---

## 1. Architecture Overview

### Current State (DOE + Python scripts)
```
User/Cron → run.py dispatcher → subprocess → individual script → shared/ clients → APIs
```
- Scripts are statically wired
- No intelligence layer — scripts do exactly one thing
- Failures require manual intervention
- No cross-department reasoning

### Target State (smolagents + MCP)
```
                    ┌─────────────────────────────────────────┐
                    │         ORCHESTRATOR AGENT               │
                    │   (smolagents CodeAgent + scheduler)     │
                    │   Listens: cron / webhooks / Discord     │
                    └──────┬────┬────┬────┬────┬──────────────┘
                           │    │    │    │    │
              ┌────────────┘    │    │    │    └────────────┐
              ▼                 ▼    │    ▼                 ▼
        ┌──────────┐   ┌──────────┐ │ ┌──────────┐  ┌──────────┐
        │ GROWTH   │   │ANALYTICS │ │ │ FINANCE  │  │ STRATEGY │
        │  Agent   │   │  Agent   │ │ │  Agent   │  │  Agent   │
        └────┬─────┘   └────┬─────┘ │ └────┬─────┘  └────┬─────┘
             │               │       │      │              │
             └───────────────┴───────┼──────┴──────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │      MCP TOOL SERVERS    │
                        ├──────────────────────────┤
                        │ mcp-notion    (R/W)      │
                        │ mcp-supabase  (R/W)      │
                        │ mcp-discord   (send/read)│
                        │ mcp-resend    (send)     │
                        │ mcp-analytics (GA4/Short)│
                        │ mcp-finance   (Creem/IB) │
                        │ mcp-filesystem (R/W)     │
                        │ mcp-shell     (execute)  │
                        └──────────────────────────┘
```

### Why smolagents, not raw Copilot CLI

| Factor | smolagents | gh copilot CLI |
|--------|-----------|----------------|
| LLM choice | Any (Gemini, Groq, OpenRouter, local) | GitHub-hosted only |
| Tool system | Native MCP + custom Python tools | MCP via config flag |
| Agent loop control | Full Python control, custom stopping, retry | Black box |
| Cost | Your own LLM keys (Groq free tier, Gemini free tier) | Copilot subscription |
| Observability | Full Python logging, custom traces | stdout only |
| Self-healing | Custom error handlers in Python | Limited |
| Offline/air-gapped | Works with local models | Requires GitHub auth |

**Recommendation**: Use `smolagents` as the primary framework. Keep `gh copilot` as a secondary escape hatch for ad-hoc VPS debugging via SSH.

---

## 2. MCP Server Design

### 2.1 Server Inventory

Each MCP server wraps one `shared/` client into a standard MCP interface. Servers run as persistent processes (systemd) or on-demand (stdio).

#### Server A: `mcp-notion` (wraps `shared/notion_client.py`)
```
Tools exposed:
  - query_database(db_name, filters) → rows
  - add_row(db_name, properties) → page_id
  - update_row(page_id, properties) → ok
  - log_task(agent, action, details) → page_id
  - get_schema(db_name) → property definitions
```
**Transport**: stdio (spawned per-agent session)

#### Server B: `mcp-supabase` (wraps `shared/supabase_client.py`)
```
Tools exposed:
  - query_table(table, filters, select, limit) → rows
  - insert_row(table, data) → row
  - update_row(table, match, data) → row
  - rpc(function_name, params) → result
  - get_user_by_email(email) → profile
```
**Transport**: stdio

#### Server C: `mcp-discord` (wraps `shared/discord_client.py` + `shared/alerting.py`)
```
Tools exposed:
  - send_alert(title, description, level) → ok
  - send_channel_message(channel_id, content) → message_id
  - read_recent_messages(channel_id, limit) → messages
  - send_daily_brief() → ok
  - send_signup_alert(email, source) → ok
```
**Transport**: stdio

#### Server D: `mcp-resend` (wraps `shared/resend_client.py`)
```
Tools exposed:
  - send_email(to, subject, html, from_name) → message_id
  - list_contacts(audience_id) → contacts
  - add_contact(audience_id, email, first_name) → contact_id
  - get_send_stats(date_range) → stats
```
**Transport**: stdio

#### Server E: `mcp-analytics` (wraps `shared/google_analytics_client.py` + `shared/shortio_client.py`)
```
Tools exposed:
  - ga4_report(dimensions, metrics, date_range) → report
  - ga4_realtime(metrics) → snapshot
  - shortio_list_links(domain) → links
  - shortio_click_stats(link_id, date_range) → stats
```
**Transport**: stdio

#### Server F: `mcp-finance` (wraps `shared/creem_client.py`)
```
Tools exposed:
  - list_subscriptions(status, date_range) → subscriptions
  - get_subscription(id) → subscription
  - calculate_mrr() → mrr_data
  - list_transactions(date_range) → transactions
```
**Transport**: stdio

#### Server G: `mcp-filesystem`
```
Use the official MCP filesystem server:
  npx @modelcontextprotocol/server-filesystem /home/hedgebot/hedge-edge
```
**Transport**: stdio

#### Server H: `mcp-shell` (restricted)
```
Tools exposed:
  - run_command(command, cwd, timeout) → stdout+stderr
  Allowlist: python, git, curl, cat, ls, grep, wc
  Blocklist: rm -rf, dd, shutdown, reboot, sudo
```
**Transport**: stdio

### 2.2 MCP Config File

All servers are declared in a single `mcp_servers.json` loaded by every agent:

```json
{
  "mcpServers": {
    "notion":     { "command": "python", "args": ["mcp_servers/mcp_notion.py"] },
    "supabase":   { "command": "python", "args": ["mcp_servers/mcp_supabase.py"] },
    "discord":    { "command": "python", "args": ["mcp_servers/mcp_discord.py"] },
    "resend":     { "command": "python", "args": ["mcp_servers/mcp_resend.py"] },
    "analytics":  { "command": "python", "args": ["mcp_servers/mcp_analytics.py"] },
    "finance":    { "command": "python", "args": ["mcp_servers/mcp_finance.py"] },
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/hedgebot/hedge-edge"] },
    "shell":      { "command": "python", "args": ["mcp_servers/mcp_shell.py"] }
  }
}
```

---

## 3. Agent Definitions

Each department agent is a `smolagents.CodeAgent` instance with:
- A **system prompt** loaded from its `SKILL.md`
- A **tool set** from specific MCP servers (principle of least privilege)
- A **model** from the existing `llm_router.py` provider registry

### 3.1 Orchestrator Agent (Master)

```
File:    agents/orchestrator_agent.py
Model:   Gemini 2.5 Flash (via litellm or direct)
Tools:   ALL MCP servers + agent spawning
Role:    Reads incoming task → classifies intent → spawns department sub-agent
         OR handles infrastructure tasks itself (deploy, VPS, cron)
```

**System prompt core:**
> You are the Orchestrator for Hedge Edge. You route tasks to department agents.
> You have access to all MCP tools but you should only use infrastructure tools directly.
> For domain work, spawn the appropriate department agent.
> Read Business/ORCHESTRATOR/SKILL.md for your full capabilities.

**Unique capabilities:**
- `spawn_agent(department, prompt)` — creates and runs a sub-CodeAgent
- Direct access to mcp-shell for VPS maintenance
- Webhook listener for Discord commands, Supabase edge function triggers

### 3.2 Analytics Agent

```
File:    agents/analytics_agent.py
Model:   Gemini 2.5 Flash (primary) → OpenRouter Gemini (fallback)
Tools:   mcp-notion, mcp-supabase, mcp-analytics, mcp-discord (alerts only)
```

**System prompt loaded from:** `Business/ANALYTICS/SKILL.md`

**Scheduled tasks:**
| Task | What it does | Replaces |
|------|-------------|----------|
| `daily_kpi_snapshot` | Query GA4 + Supabase + Notion → compute KPIs → write Notion dashboard → alert Discord | `daily_analytics.py` |
| `hourly_metrics_sync` | Pull hourly metrics from all sources → sync to Notion | `hourly_metrics_sync.py` |
| `attribution_audit` | Verify UTM chain integrity across Short.io → GA4 → Supabase | `attribution_audit.py` |
| `funnel_report` | Calculate full-funnel conversion rates | `funnel_calculator.py` |
| `license_health` | Check license status, activation rates | `license_tracking_report.py` |

### 3.3 Growth Agent (Marketing + Sales)

```
File:    agents/growth_agent.py
Model:   Groq Llama 3.3 70B (fast, free tier)
Tools:   mcp-notion, mcp-supabase, mcp-resend, mcp-discord, mcp-filesystem
```

**System prompt loaded from:** `Business/GROWTH/SKILL.md`

**Scheduled tasks:**
| Task | What it does | Replaces |
|------|-------------|----------|
| `email_send_morning` | Query sequences due → send via Resend → log | `email_system.py` |
| `email_send_evening` | Same, evening batch | `email_system.py` |
| `beta_key_check` | Check new signups → provision keys → trigger welcome email | `beta_lead_register.py` + `check_new_beta_users.py` |
| `revoke_expired` | Cleanup expired beta claims | `revoke_expired_claims.py` |
| `auto_tweet` | Pull next tweet from library → post → update state | `auto_tweet.py` |
| `twitter_reply_scan` | Search for prop trading pain points → draft replies | `tw_search_reply.py` |
| `discord_community_pulse` | Read recent messages → summarise sentiment → alert | `chat_analytics.py` |
| `hourly_marketing_sync` | Sync marketing metrics to Notion | `hourly_metrics_sync.py` |

### 3.4 Finance Agent

```
File:    agents/finance_agent.py
Model:   Groq Llama 3.3 70B
Tools:   mcp-notion, mcp-supabase, mcp-finance, mcp-discord (alerts only)
```

**System prompt loaded from:** `Business/FINANCE/SKILL.md`

**Scheduled tasks:**
| Task | What it does | Replaces |
|------|-------------|----------|
| `daily_revenue_sync` | Pull Creem.io transactions → compute MRR → write Notion | `revenue_tracker.py` |
| `weekly_ib_scrape` | Scrape Vantage + BlackBull portals → reconcile | `scrape_vantage_ib.py` + `scrape_blackbull_ib.py` + `ib_report_aggregator.py` |
| `monthly_pnl` | Generate P&L and cash flow statement | `financial_reporter.py` |
| `expense_audit` | Flag anomalous expenses | `expense_manager.py` |

### 3.5 Strategy Agent

```
File:    agents/strategy_agent.py
Model:   Gemini 2.5 Flash (needs long context for research)
Tools:   mcp-notion, mcp-supabase, mcp-filesystem, mcp-shell (read-only)
```

**System prompt loaded from:** `Business/STRATEGY/SKILL.md`

**Scheduled tasks:**
| Task | What it does | Replaces |
|------|-------------|----------|
| `weekly_competitor_scan` | Scrape PropFirmMatch → update challenge DB | `propmatch_scraper.py` |
| `weekly_trend_report` | Scan industry trends → write digest | `trend_scanner.py` |
| `monthly_consolidated` | Run all 7 hedge models → generate PDF report | `consolidated_report.py` |

---

## 4. Self-Annealing System

The self-annealing system makes agents improve over time through structured feedback loops.

### 4.1 Three-Layer Error Recovery

```
Layer 1 — IMMEDIATE RETRY (automatic)
  Agent task fails → smolagents catches exception →
  re-prompts the agent with the error traceback →
  "Your previous attempt failed with: {error}. Diagnose the root cause and try a different approach."
  Max retries: 2

Layer 2 — SELF-DIAGNOSIS (automatic)
  If Layer 1 exhausted → Orchestrator spawns a DIAGNOSTIC sub-agent:
    Prompt: "Read the error log at {path}. Read the source code of the failing tool.
             Determine if this is a code bug, an API outage, a data issue, or a config problem.
             Write a fix if it's a code bug. Write a workaround if it's an API outage.
             Log your diagnosis to Notion incident-log."
  The diagnostic agent has mcp-filesystem + mcp-shell (read-only) + mcp-notion

Layer 3 — HUMAN ESCALATION (alert)
  If Layer 2 fails → send Discord critical alert + email to founder
  Include: original task, all retry attempts, diagnostic agent's analysis
  Agent marks task as "blocked" in Notion and moves on
```

### 4.2 Performance Annealing Loop

Every agent run produces a structured result logged to a `agent_runs` Supabase table:

```sql
CREATE TABLE agent_runs (
  id           uuid DEFAULT gen_random_uuid(),
  agent        text NOT NULL,           -- 'analytics', 'growth', etc.
  task         text NOT NULL,           -- 'daily_kpi_snapshot'
  started_at   timestamptz NOT NULL,
  finished_at  timestamptz,
  status       text NOT NULL,           -- 'success', 'retry_success', 'failed', 'escalated'
  retries      int DEFAULT 0,
  tokens_used  int,
  model        text,
  error_msg    text,
  output_hash  text,                    -- hash of output to detect drift
  duration_ms  int
);
```

**Weekly annealing job** (run by Orchestrator):
1. Query `agent_runs` for the past 7 days
2. Identify:
   - Tasks with >20% failure rate → flag for code review
   - Tasks with increasing token usage → prompt may be bloating
   - Tasks where retry_success > 30% → the first attempt's prompt needs tuning
   - Tasks with output_hash drift → data schema may have changed
3. For each flagged task, spawn a **tuning sub-agent**:
   - "Read the last 5 failure logs for {task}. Identify the common root cause.
     Suggest a prompt modification or tool change. Write the suggestion to
     Business/{DEPT}/resources/annealing-notes.md"
4. Orchestrator reviews suggestions and applies safe ones automatically
5. Unsafe suggestions (code changes) are pushed as a git branch for human review

### 4.3 Prompt Evolution

Each agent's system prompt has a `## Learned Patterns` section that the annealing system appends to:

```markdown
## Learned Patterns
<!-- Auto-maintained by annealing system. Do not edit manually. -->
- [2026-04-01] Notion API returns 429 after 3 rapid queries. Add 200ms delay between batch reads.
- [2026-04-08] Resend webhook sometimes sends duplicate events. Deduplicate by message_id before counting.
- [2026-04-15] GA4 Data API returns empty for queries <4 hours after midnight UTC. Delay morning sync to 04:15.
```

This section is capped at 20 entries. Oldest entries are archived to `resources/annealing-archive.md`.

---

## 5. Cron Schedule

All times UTC. The Orchestrator is the single scheduler — it wakes up, decides what to run, and spawns the appropriate agent.

### 5.1 Orchestrator Heartbeat

The Orchestrator runs as a **persistent systemd service** with an APScheduler loop (same pattern as the current `cron_scheduler.py`, but spawning agents instead of importing scripts).

### 5.2 Full Schedule

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TIME (UTC)   │ AGENT       │ TASK                    │ FREQUENCY            │
├──────────────┼─────────────┼─────────────────────────┼──────────────────────┤
│ Every 60min  │ ORCHESTRATOR│ heartbeat_check         │ Hourly               │
│ :10 past hr  │ ANALYTICS   │ hourly_metrics_sync     │ Hourly               │
│ :10 past hr  │ GROWTH      │ hourly_marketing_sync   │ Hourly               │
├──────────────┼─────────────┼─────────────────────────┼──────────────────────┤
│ 04:15        │ ANALYTICS   │ daily_kpi_snapshot      │ Daily                │
│ 04:30        │ FINANCE     │ daily_revenue_sync      │ Daily                │
│ 05:00        │ GROWTH      │ beta_key_check          │ Daily                │
│ 05:15        │ GROWTH      │ revoke_expired_claims   │ Daily                │
│ 06:00        │ GROWTH      │ discord_community_pulse │ Daily                │
│ 09:00        │ GROWTH      │ email_send_morning      │ Daily                │
│ 09:05        │ ANALYTICS   │ daily_analytics_report  │ Daily (after email)  │
│ 12:00        │ GROWTH      │ auto_tweet              │ Daily                │
│ 14:00        │ GROWTH      │ twitter_reply_scan      │ Daily                │
│ 18:00        │ GROWTH      │ auto_tweet              │ Daily (2nd post)     │
│ 21:00        │ GROWTH      │ email_send_evening      │ Daily                │
│ 23:00        │ ORCHESTRATOR│ daily_summary           │ Daily                │
│ 23:30        │ ORCHESTRATOR│ self_anneal_check       │ Daily (lightweight)  │
├──────────────┼─────────────┼─────────────────────────┼──────────────────────┤
│ Mon 03:00    │ ANALYTICS   │ attribution_audit       │ Weekly               │
│ Mon 06:00    │ STRATEGY    │ weekly_competitor_scan   │ Weekly               │
│ Mon 08:00    │ STRATEGY    │ weekly_trend_report     │ Weekly               │
│ Mon 10:00    │ FINANCE     │ weekly_ib_scrape        │ Weekly               │
│ Fri 16:00    │ ORCHESTRATOR│ weekly_anneal_full      │ Weekly               │
│ Fri 17:00    │ ANALYTICS   │ funnel_report           │ Weekly               │
│ Fri 18:00    │ ORCHESTRATOR│ weekly_status_report    │ Weekly               │
├──────────────┼─────────────┼─────────────────────────┼──────────────────────┤
│ 1st Mon 02:00│ FINANCE     │ monthly_pnl             │ Monthly              │
│ 1st Mon 03:00│ FINANCE     │ expense_audit           │ Monthly              │
│ 1st Mon 06:00│ STRATEGY    │ monthly_consolidated    │ Monthly              │
│ 1st Mon 08:00│ ANALYTICS   │ license_health          │ Monthly              │
└──────────────┴─────────────┴─────────────────────────┴──────────────────────┘
```

### 5.3 Concurrency Rules

- **Max 2 agents running simultaneously** (VPS RAM constraint ~4GB)
- Orchestrator itself is always resident (~200MB)
- Each department agent spins up, executes, then exits (~500MB peak)
- If two agents are scheduled at the same minute, the lower-priority one waits
- Priority order: FINANCE > ANALYTICS > GROWTH > STRATEGY

### 5.4 Event-Driven Triggers (non-cron)

Beyond scheduled cron, certain events trigger immediate agent spawns:

| Event Source | Trigger | Agent | Task |
|-------------|---------|-------|------|
| Supabase webhook | New user signup | GROWTH | `beta_key_check` (immediate) |
| Creem.io webhook | New subscription | FINANCE | `revenue_event_process` |
| Discord command | `!status` in #ops | ORCHESTRATOR | `status_report` |
| Discord command | `!deploy` in #ops | ORCHESTRATOR | `app_deploy` |
| Supabase webhook | Support ticket | GROWTH | `ticket_triage` |
| GitHub webhook | New release tag | ORCHESTRATOR | `release_notify` |

These are handled by a lightweight FastAPI webhook receiver running alongside the Orchestrator.

---

## 6. VPS Directory Layout

```
/home/hedgebot/hedge-edge/                  ← git clone of this workspace
├── Business/                               ← existing DOE structure (unchanged)
├── shared/                                 ← existing API clients (unchanged)
├── agents/                                 ← NEW: smolagents agent definitions
│   ├── __init__.py
│   ├── base_agent.py                       ← shared agent factory + error recovery
│   ├── orchestrator_agent.py
│   ├── analytics_agent.py
│   ├── growth_agent.py
│   ├── finance_agent.py
│   └── strategy_agent.py
├── mcp_servers/                            ← NEW: MCP tool servers
│   ├── __init__.py
│   ├── mcp_notion.py
│   ├── mcp_supabase.py
│   ├── mcp_discord.py
│   ├── mcp_resend.py
│   ├── mcp_analytics.py
│   ├── mcp_finance.py
│   └── mcp_shell.py
├── mcp_servers.json                        ← MCP server registry
├── scheduler/                              ← NEW: persistent scheduler
│   ├── main.py                             ← APScheduler + FastAPI (replaces cron_scheduler.py)
│   ├── webhook_receiver.py                 ← event-driven triggers
│   └── agent_runner.py                     ← spawn + monitor + log agent runs
├── annealing/                              ← NEW: self-improvement system
│   ├── analyzer.py                         ← weekly performance analysis
│   ├── prompt_tuner.py                     ← auto-suggest prompt improvements
│   └── archive/                            ← historical annealing reports
├── logs/                                   ← agent run logs (gitignored)
│   ├── orchestrator/
│   ├── analytics/
│   ├── growth/
│   ├── finance/
│   └── strategy/
├── .env                                    ← master env (existing)
└── requirements-agents.txt                 ← NEW: smolagents + mcp dependencies
```

### 6.1 Systemd Services on VPS

```
/etc/systemd/system/
├── hedge-orchestrator.service      ← main scheduler (always-on)
├── hedge-webhook.service           ← FastAPI webhook receiver (always-on)
```

`hedge-orchestrator.service`:
```ini
[Unit]
Description=Hedge Edge Orchestrator Agent Scheduler
After=network.target

[Service]
Type=simple
User=hedgebot
WorkingDirectory=/home/hedgebot/hedge-edge
ExecStart=/home/hedgebot/hedge-edge/.venv/bin/python scheduler/main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/hedgebot/hedge-edge

[Install]
WantedBy=multi-user.target
```

---

## 7. Implementation Phases

### Phase 1 — Foundation (Week 1)
**Goal**: Get one agent running on VPS via smolagents + one MCP server

1. SSH into hedge-vps, create Python venv with `smolagents[mcp]` + `mcp` SDK
2. Build `mcp_servers/mcp_notion.py` — wrap `shared/notion_client.py` as stdio MCP server
3. Build `agents/base_agent.py` — factory that creates a CodeAgent with MCP tools + error recovery
4. Build `agents/analytics_agent.py` — loads ANALYTICS/SKILL.md as system prompt, connects to mcp-notion
5. Test: `python agents/analytics_agent.py "What are today's KPIs?"` → verify it queries Notion via MCP
6. Build `mcp_servers.json` with just the Notion server

**Deliverables**: One working agent + one MCP server, manual invocation only

### Phase 2 — Full MCP Layer (Week 2)
**Goal**: All 8 MCP servers operational

1. Build remaining MCP servers: supabase, discord, resend, analytics, finance, filesystem, shell
2. Test each server independently: `python mcp_servers/mcp_supabase.py` → verify tool listing
3. Build `agents/growth_agent.py` with mcp-notion + mcp-supabase + mcp-resend + mcp-discord
4. Build `agents/finance_agent.py` with mcp-notion + mcp-supabase + mcp-finance
5. Build `agents/strategy_agent.py` with mcp-notion + mcp-supabase + mcp-filesystem
6. Test each agent end-to-end with a simple task

**Deliverables**: All 5 agents + all 8 MCP servers, manual invocation only

### Phase 3 — Scheduler (Week 3)
**Goal**: Automated cron-based execution

1. Build `scheduler/main.py` — APScheduler with the full schedule from Section 5
2. Build `scheduler/agent_runner.py` — spawns agent, captures output, logs to Supabase `agent_runs`
3. Build `scheduler/webhook_receiver.py` — FastAPI endpoint for Supabase/Creem/Discord webhooks
4. Deploy `hedge-orchestrator.service` systemd unit
5. Deploy `hedge-webhook.service` systemd unit
6. Run for 48 hours in "shadow mode" — agents run but only log, don't write to production
7. Review shadow logs, fix issues
8. Enable production writes

**Deliverables**: Fully autonomous scheduled execution on VPS

### Phase 4 — Self-Annealing (Week 4)
**Goal**: Agents improve over time

1. Create `agent_runs` Supabase table
2. Build `annealing/analyzer.py` — weekly performance analysis against `agent_runs`
3. Build `annealing/prompt_tuner.py` — reads failure patterns → suggests prompt changes
4. Add `## Learned Patterns` section to each agent's system prompt template
5. Wire the Friday 16:00 `weekly_anneal_full` job into the scheduler
6. Wire the nightly 23:30 `self_anneal_check` lightweight job
7. Add git auto-branch for unsafe changes (code modifications)

**Deliverables**: Self-improving agent loop

### Phase 5 — Orchestrator Intelligence (Week 5)
**Goal**: Orchestrator can decompose and route arbitrary natural language requests

1. Build `agents/orchestrator_agent.py` with `spawn_agent()` capability
2. Wire Discord `!ask` command → webhook → orchestrator agent → department agent → response
3. Add multi-agent coordination: orchestrator can chain agents (e.g., "scrape competitors then update hedge model then generate report")
4. Add dependency DAG support: orchestrator parses complex requests into ordered sub-tasks
5. Stress test with 20 diverse natural language business requests

**Deliverables**: Fully intelligent orchestrator that can handle arbitrary business requests

---

## 8. File Manifest

Complete list of NEW files to create:

```
# Agent definitions
agents/__init__.py
agents/base_agent.py                    ← Agent factory, LLM config, error recovery, logging
agents/orchestrator_agent.py            ← Master router + sub-agent spawner
agents/analytics_agent.py               ← KPI, attribution, funnel, license tasks
agents/growth_agent.py                  ← Email, social, beta, community, CRM tasks
agents/finance_agent.py                 ← Revenue, IB, expense, P&L tasks
agents/strategy_agent.py                ← Research, competitor, hedge model tasks

# MCP tool servers
mcp_servers/__init__.py
mcp_servers/mcp_notion.py              ← Wraps shared/notion_client.py
mcp_servers/mcp_supabase.py            ← Wraps shared/supabase_client.py
mcp_servers/mcp_discord.py             ← Wraps shared/discord_client.py + alerting.py
mcp_servers/mcp_resend.py              ← Wraps shared/resend_client.py
mcp_servers/mcp_analytics.py           ← Wraps shared/google_analytics_client.py + shortio_client.py
mcp_servers/mcp_finance.py             ← Wraps shared/creem_client.py
mcp_servers/mcp_shell.py               ← Restricted shell execution
mcp_servers.json                        ← Server registry

# Scheduler
scheduler/main.py                       ← APScheduler + FastAPI health check
scheduler/agent_runner.py               ← Agent spawn/monitor/log wrapper
scheduler/webhook_receiver.py           ← Event-driven trigger endpoint

# Self-annealing
annealing/__init__.py
annealing/analyzer.py                   ← Performance analysis from agent_runs
annealing/prompt_tuner.py              ← Auto-suggest prompt improvements

# Infrastructure
requirements-agents.txt                 ← smolagents[mcp], mcp, apscheduler, fastapi, uvicorn
```

### Files UNCHANGED (still used as-is)
```
shared/*                                ← All API clients remain. MCP servers wrap them, not replace them.
Business/*/SKILL.md                     ← Used as system prompts for agents
Business/*/directives/*                 ← Reference material agents can read via mcp-filesystem
Business/*/executions/*                 ← Legacy scripts. Agents replace their scheduling, not their logic.
Business/*/resources/*                  ← Data, configs, notebooks — agents read via mcp-filesystem
.env                                    ← Master env vars, loaded by MCP servers
```

### Key Principle: Wrap, Don't Rewrite

The existing `shared/` clients and `executions/` scripts are battle-tested. The MCP servers are thin wrappers that expose them via the standard protocol. The agents are the new intelligence layer on top. Nothing existing is deleted — it gains an AI brain.

---

## Cost Estimate (Monthly)

| Resource | Cost |
|----------|------|
| Gemini 2.5 Flash (Analytics + Strategy) | ~$5–15 (free tier covers most) |
| Groq Llama 3.3 (Growth + Finance) | $0 (free tier: 30 req/min) |
| OpenRouter fallback | ~$2–5 |
| VPS (already running) | $0 incremental |
| **Total** | **~$7–20/month** |

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Agent hallucinates a wrong API call | MCP servers validate inputs; each tool has strict parameter schemas |
| Agent enters infinite retry loop | Max 2 retries per layer, hard 5-minute timeout per agent run |
| LLM provider goes down | `llm_router.py` fallback chain: Gemini → OpenRouter → Groq |
| Agent writes bad data to Notion/Supabase | Shadow mode (Phase 3) validates before production writes |
| VPS runs out of RAM | Max 2 concurrent agents; each exits after task completion |
| MCP server crashes mid-task | Agent catches `ConnectionError` → restarts MCP server → retries |
| Token cost spikes | Per-agent daily token budget in `agent_runner.py`; alert at 80% |
| Self-annealing makes things worse | All auto-changes go to git branch; production prompt changes require human merge |
