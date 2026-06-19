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
class ServerConfig:
    """Configuration for one MCP server."""

    namespace: str
    script_path: Path


class MCPGateway:
    """Raw MCP gateway used behind the governance layer."""

    def __init__(self) -> None:
        self._servers: dict[str, ServerConfig] = {}

    def register_server(self, namespace: str, script_path: Path) -> None:
        """Register one local MCP server."""
        self._servers[namespace] = ServerConfig(namespace, script_path)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute one namespaced MCP tool."""
        namespace, tool_name = name.split(".", maxsplit=1)
        if namespace not in self._servers:
            raise KeyError(f"Unknown MCP server namespace: {namespace}")
        async with self._session(self._servers[namespace]) as session:
            result = await session.call_tool(tool_name, arguments)
        if getattr(result, "isError", False):
            detail = result.content[0].text if result.content else "MCP tool failed."
            raise RuntimeError(detail)
        return json.loads(result.content[0].text)

    @asynccontextmanager
    async def _session(self, config: ServerConfig) -> AsyncIterator[ClientSession]:
        """Start one stdio server and yield an initialized session."""
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(config.script_path)],
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session


def build_gateway() -> MCPGateway:
    """Register Phase 3 customer, weather, and ticket MCP servers."""
    phase3 = Path(__file__).resolve().parents[1] / "phase3_mcp_gateway" / "servers"
    gateway = MCPGateway()
    gateway.register_server("customer", phase3 / "customer_server.py")
    gateway.register_server("weather", phase3 / "weather_server.py")
    gateway.register_server("ticket", phase3 / "ticket_server.py")
    return gateway

