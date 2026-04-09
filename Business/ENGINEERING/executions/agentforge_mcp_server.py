from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = WORKSPACE_ROOT / ".github" / "agents"

mcp = FastMCP(
    "AgentForge MCP",
    host=os.getenv("AGENTFORGE_MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("AGENTFORGE_MCP_PORT", "8000")),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return basic server health information."""
    return {"service": "agentforge-mcp", "status": "ok"}


@mcp.tool()
def list_registered_agents() -> list[str]:
    """List the registered VS Code agents in this workspace."""
    if not AGENTS_DIR.exists():
        return []
    return sorted(path.name for path in AGENTS_DIR.glob("*.agent.md"))


@mcp.tool()
def read_agent_definition(agent_file: str) -> str:
    """Read a specific agent definition from .github/agents/."""
    candidate = (AGENTS_DIR / agent_file).resolve()
    if AGENTS_DIR not in candidate.parents or not candidate.is_file():
        raise ValueError("Agent file must exist inside .github/agents")
    return candidate.read_text(encoding="utf-8")


@mcp.resource("agentforge://workspace/summary")
def workspace_summary() -> str:
    """Return a short summary of the AgentForge workspace."""
    return (
        "AgentForge uses a DOE structure inside Business/. "
        "Custom agent definitions live in .github/agents/, shared code lives in shared/, "
        "and Engineering owns the Agent Builder scaffolding workflow."
    )


@mcp.prompt()
def scaffold_agent_prompt(name: str, department: str, purpose: str) -> str:
    """Generate a reusable prompt template for scaffolding a new agent."""
    return (
        f"Design an AgentForge agent named {name} for the {department} department. "
        f"Its purpose is: {purpose}. "
        "Return an Agent Card, tool plan, eval outline, trace requirements, and review gate."
    )


if __name__ == "__main__":
    transport = os.getenv("AGENTFORGE_MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)