from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass(frozen=True)
class ToolInfo:
    """Metadata for a dynamically discovered MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for one local stdio MCP server."""

    namespace: str
    script_path: Path


class MCPGateway:
    """Discover and route tools across multiple MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[str, ServerConfig] = {}

    def register_server(self, namespace: str, script_path: Path) -> None:
        """Register an MCP server."""
        if namespace in self._servers:
            raise ValueError(f"Server already registered: {namespace}")
        self._servers[namespace] = ServerConfig(namespace, script_path)

    async def discover_tools(self) -> list[ToolInfo]:
        """Discover namespaced tools from all servers."""
        tools: list[ToolInfo] = []
        for namespace in sorted(self._servers):
            async with self._session(self._servers[namespace]) as session:
                response = await session.list_tools()
            tools.extend(
                ToolInfo(
                    name=f"{namespace}.{tool.name}",
                    description=tool.description or "",
                    input_schema=tool.inputSchema,
                )
                for tool in response.tools
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a namespaced MCP tool call."""
        namespace, tool_name = self._split_name(name)
        async with self._session(self._servers[namespace]) as session:
            result = await session.call_tool(tool_name, arguments)
        if getattr(result, "isError", False):
            detail = result.content[0].text if result.content else "MCP tool failed."
            raise RuntimeError(detail)
        return json.loads(result.content[0].text)

    @asynccontextmanager
    async def _session(self, config: ServerConfig) -> AsyncIterator[ClientSession]:
        """Start one server and yield an initialized MCP session."""
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(config.script_path)],
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    def _split_name(self, name: str) -> tuple[str, str]:
        """Split namespace.tool into its routing parts."""
        try:
            namespace, tool_name = name.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Tool names must use namespace.tool format.") from exc
        if namespace not in self._servers:
            raise KeyError(f"Unknown MCP server namespace: {namespace}")
        return namespace, tool_name


def build_gateway() -> MCPGateway:
    """Register Phase 3 customer, weather, and ticket MCP servers."""
    phase3 = Path(__file__).resolve().parents[1] / "phase3_mcp_gateway" / "servers"
    gateway = MCPGateway()
    gateway.register_server("customer", phase3 / "customer_server.py")
    gateway.register_server("weather", phase3 / "weather_server.py")
    gateway.register_server("ticket", phase3 / "ticket_server.py")
    return gateway

