from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


class Transport(StrEnum):
    """Supported server transport types."""

    LOCAL_STDIO = "local_stdio"
    REMOTE_HTTP = "remote_http"


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for one local or remote MCP server."""

    namespace: str
    transport: Transport
    script_path: Path | None = None
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NamespacedTool:
    """A discovered tool with a gateway namespace."""

    name: str
    description: str
    namespace: str
    original_name: str


class MCPGateway:
    """Gateway that can route to both local stdio and remote HTTP MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[str, ServerConfig] = {}

    def register_server(self, config: ServerConfig) -> None:
        """Register one local or remote MCP server."""
        if "." in config.namespace:
            raise ValueError("Namespace cannot contain dots.")
        if config.namespace in self._servers:
            raise ValueError(f"Server already registered: {config.namespace}")
        self._servers[config.namespace] = config

    def remove_server(self, namespace: str) -> None:
        """Remove one server by namespace."""
        self._servers.pop(namespace, None)

    def list_servers(self) -> list[str]:
        """Return registered namespaces."""
        return sorted(self._servers)

    async def discover_tools(self) -> list[NamespacedTool]:
        """Discover tools from all registered servers."""
        tools: list[NamespacedTool] = []
        for namespace in self.list_servers():
            config = self._servers[namespace]
            try:
                async with self._connect(config) as session:
                    response = await session.list_tools()
            except Exception as exc:
                raise self._clean_remote_error(exc) from exc
            for tool in response.tools:
                tools.append(
                    NamespacedTool(
                        name=f"{namespace}.{tool.name}",
                        description=tool.description or "",
                        namespace=namespace,
                        original_name=tool.name,
                    )
                )
        return tools

    async def call_tool(self, namespaced_tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a namespaced tool call to the correct local or remote MCP server."""
        namespace, tool_name = self._split_tool_name(namespaced_tool_name)
        config = self._servers[namespace]

        try:
            async with self._connect(config) as session:
                result = await session.call_tool(tool_name, arguments)
        except Exception as exc:
            raise self._clean_remote_error(exc) from exc

        if getattr(result, "isError", False):
            message = result.content[0].text if result.content else "MCP tool call failed."
            raise PermissionError(message)

        return json.loads(result.content[0].text)

    @asynccontextmanager
    async def _connect(self, config: ServerConfig) -> AsyncIterator[ClientSession]:
        """Open an MCP client session for local stdio or remote HTTP."""
        if config.transport == Transport.LOCAL_STDIO:
            if config.script_path is None:
                raise ValueError("Local stdio servers require script_path.")
            server = StdioServerParameters(command=sys.executable, args=[str(config.script_path)])
            async with stdio_client(server) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
            return

        if config.transport == Transport.REMOTE_HTTP:
            if config.url is None:
                raise ValueError("Remote HTTP servers require url.")
            async with streamablehttp_client(config.url, headers=config.headers) as streams:
                read_stream, write_stream = streams[0], streams[1]
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
            return

        raise ValueError(f"Unsupported transport: {config.transport}")

    def _split_tool_name(self, namespaced_tool_name: str) -> tuple[str, str]:
        """Split secure_customer.get_customer into namespace and tool name."""
        try:
            namespace, tool_name = namespaced_tool_name.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Tool name must use namespace.tool_name format.") from exc
        if namespace not in self._servers:
            raise KeyError(f"Unknown server namespace: {namespace}")
        return namespace, tool_name

    def _clean_remote_error(self, exc: Exception) -> Exception:
        """Convert nested HTTP errors from the MCP client into beginner-friendly errors."""
        http_error = self._find_http_status_error(exc)
        if http_error is None:
            return exc

        response = http_error.response
        detail = response.reason_phrase
        if response.status_code == 401:
            detail = "Missing or invalid credentials."
        return ConnectionError(f"Remote MCP request failed with HTTP {response.status_code}: {detail}")

    def _find_http_status_error(self, exc: BaseException) -> httpx.HTTPStatusError | None:
        """Find an HTTPStatusError inside a normal exception or ExceptionGroup."""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc
        if isinstance(exc, BaseExceptionGroup):
            for child in exc.exceptions:
                found = self._find_http_status_error(child)
                if found is not None:
                    return found
        return None


def api_key_headers(api_key: str) -> dict[str, str]:
    """Build HTTP headers for API key authentication."""
    return {"X-API-Key": api_key}


def bearer_headers(token: str) -> dict[str, str]:
    """Build HTTP headers for bearer token authentication."""
    return {"Authorization": f"Bearer {token}"}


def build_remote_gateway(headers: dict[str, str], url: str = "http://127.0.0.1:8765/mcp") -> MCPGateway:
    """Create a gateway with the remote SecureCustomerMCP server registered."""
    gateway = MCPGateway()
    gateway.register_server(
        ServerConfig(
            namespace="secure_customer",
            transport=Transport.REMOTE_HTTP,
            url=url,
            headers=headers,
        )
    )
    return gateway
