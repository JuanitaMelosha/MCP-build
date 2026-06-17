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
class MCPServerConfig:
    """Configuration for one stdio MCP server."""

    namespace: str
    script_path: Path


@dataclass(frozen=True)
class NamespacedTool:
    """A discovered tool with the gateway namespace added."""

    name: str
    description: str
    server_namespace: str
    original_name: str


class MCPGateway:
    """Beginner-friendly gateway that discovers and routes tools across MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConfig] = {}

    def register_server(self, namespace: str, script_path: Path) -> None:
        """Register one MCP server under a namespace such as customer or weather."""
        if "." in namespace:
            raise ValueError("Namespaces cannot contain dots.")
        if namespace in self._servers:
            raise ValueError(f"Server namespace already registered: {namespace}")
        self._servers[namespace] = MCPServerConfig(namespace=namespace, script_path=script_path)

    def remove_server(self, namespace: str) -> None:
        """Remove a registered MCP server by namespace."""
        self._servers.pop(namespace, None)

    def list_servers(self) -> list[str]:
        """Return registered server namespaces."""
        return sorted(self._servers)

    async def discover_tools(self) -> list[NamespacedTool]:
        """Discover tools from every registered server and prefix them by namespace."""
        discovered: list[NamespacedTool] = []
        for namespace in self.list_servers():
            config = self._servers[namespace]
            async with self._connect(config) as session:
                tools = await session.list_tools()
            for tool in tools.tools:
                discovered.append(
                    NamespacedTool(
                        name=f"{namespace}.{tool.name}",
                        description=tool.description or "",
                        server_namespace=namespace,
                        original_name=tool.name,
                    )
                )
        return discovered

    async def call_tool(self, namespaced_tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a namespaced tool call to the correct MCP server."""
        namespace, tool_name = self._split_tool_name(namespaced_tool_name)
        config = self._servers[namespace]

        async with self._connect(config) as session:
            result = await session.call_tool(tool_name, arguments)

        return self._tool_result_to_json(result)

    @asynccontextmanager
    async def _connect(self, config: MCPServerConfig) -> AsyncIterator[ClientSession]:
        """Start one stdio server and yield an initialized MCP client session."""
        server = StdioServerParameters(command=sys.executable, args=[str(config.script_path)])
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    def _split_tool_name(self, namespaced_tool_name: str) -> tuple[str, str]:
        """Split customer.get_customer into customer and get_customer."""
        try:
            namespace, tool_name = namespaced_tool_name.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Tool name must use namespace.tool_name format.") from exc

        if namespace not in self._servers:
            raise KeyError(f"Unknown server namespace: {namespace}")
        return namespace, tool_name

    def _tool_result_to_json(self, result: Any) -> dict[str, Any]:
        """Convert the first text block in an MCP tool result into a dictionary."""
        return json.loads(result.content[0].text)


def build_default_gateway() -> MCPGateway:
    """Create a gateway with customer, weather, and ticket servers registered."""
    root = Path(__file__).parent
    gateway = MCPGateway()
    gateway.register_server("customer", root / "servers" / "customer_server.py")
    gateway.register_server("weather", root / "servers" / "weather_server.py")
    gateway.register_server("ticket", root / "servers" / "ticket_server.py")
    return gateway

