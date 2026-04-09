from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
import os
from typing import Any, Literal

from mcp import StdioServerParameters
from smolagents import CodeAgent, InferenceClientModel, ToolCollection


Transport = Literal["stdio", "streamable-http", "sse"]


@dataclass(slots=True)
class McpServerConfig:
    name: str
    transport: Transport
    trust_remote_code: bool = False
    structured_output: bool = True
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None

    def to_connection_params(self) -> StdioServerParameters | dict[str, Any]:
        if self.transport == "stdio":
            if not self.command:
                raise ValueError(f"MCP server '{self.name}' requires a command for stdio transport")
            server_env = dict(os.environ)
            server_env.update(self.env)
            return StdioServerParameters(command=self.command, args=self.args, env=server_env)

        if not self.url:
            raise ValueError(f"MCP server '{self.name}' requires a URL for {self.transport} transport")

        return {"url": self.url, "transport": self.transport}


@dataclass(slots=True)
class AgentBuildSpec:
    name: str
    model_id: str | None = None
    add_base_tools: bool = False
    max_steps: int | None = 12
    mcp_servers: list[McpServerConfig] = field(default_factory=list)


def build_model(model_id: str | None = None) -> InferenceClientModel:
    resolved_model_id = model_id or os.getenv("AGENTFORGE_MODEL_ID")
    if resolved_model_id:
        return InferenceClientModel(model_id=resolved_model_id)
    return InferenceClientModel()


class SmolAgentRuntime:
    def __init__(self, spec: AgentBuildSpec):
        self.spec = spec
        self._stack = ExitStack()
        self._tools_loaded = False
        self._tools: list[Any] = []

    def load_mcp_tools(self) -> list[Any]:
        if self._tools_loaded:
            return self._tools

        tools: list[Any] = []
        for server in self.spec.mcp_servers:
            collection = self._stack.enter_context(
                ToolCollection.from_mcp(
                    server.to_connection_params(),
                    trust_remote_code=server.trust_remote_code,
                    structured_output=server.structured_output,
                )
            )
            tools.extend(collection.tools)

        self._tools = tools
        self._tools_loaded = True
        return tools

    def build_agent(self) -> CodeAgent:
        agent_kwargs: dict[str, Any] = {
            "tools": self.load_mcp_tools(),
            "model": build_model(self.spec.model_id),
            "add_base_tools": self.spec.add_base_tools,
        }
        if self.spec.max_steps is not None:
            agent_kwargs["max_steps"] = self.spec.max_steps
        return CodeAgent(**agent_kwargs)

    def run(self, task: str) -> Any:
        agent = self.build_agent()
        return agent.run(task)

    def close(self) -> None:
        self._stack.close()

    def __enter__(self) -> SmolAgentRuntime:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.close()


def example_spec() -> AgentBuildSpec:
    return AgentBuildSpec(
        name="client-onboarding",
        model_id=os.getenv("AGENTFORGE_MODEL_ID"),
        add_base_tools=False,
        max_steps=12,
        mcp_servers=[
            McpServerConfig(
                name="hubspot",
                transport="streamable-http",
                url=os.getenv("HUBSPOT_MCP_URL"),
                trust_remote_code=True,
                structured_output=True,
            ),
            McpServerConfig(
                name="linear",
                transport="streamable-http",
                url=os.getenv("LINEAR_MCP_URL"),
                trust_remote_code=True,
                structured_output=True,
            ),
        ],
    )


def main() -> None:
    spec = example_spec()
    with SmolAgentRuntime(spec) as runtime:
        result = runtime.run(
            "Inspect the available MCP-backed tools and outline the artifact pack for a client onboarding agent."
        )
        print(result)


if __name__ == "__main__":
    main()