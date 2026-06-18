from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GatewayProvider(Protocol):
    """Structural interface implemented by GitHub and Rovo vendor adapters."""

    name: str

    async def list_tools(self) -> list[Any]:
        """List provider tools."""

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call one provider tool."""


@dataclass(frozen=True)
class NamespacedTool:
    """One tool exposed through the gateway."""

    name: str
    description: str
    provider: str
    original_name: str


@dataclass(frozen=True)
class LocalMCPConfig:
    """Configuration for one local stdio MCP server."""

    namespace: str
    script_path: Path


class LocalMCPAdapter:
    """Adapt a local stdio MCP server to the gateway provider interface."""

    def __init__(self, config: LocalMCPConfig) -> None:
        self.config = config
        self.name = config.namespace

    async def list_tools(self) -> list[Any]:
        """Discover tools from the local MCP server."""
        async with self._session() as session:
            result = await session.list_tools()
        return list(result.tools)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the local MCP server."""
        async with self._session() as session:
            result = await session.call_tool(tool_name, arguments)
        if getattr(result, "isError", False):
            detail = result.content[0].text if result.content else "Local MCP tool failed."
            raise RuntimeError(detail)
        if result.content and hasattr(result.content[0], "text"):
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return result

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[ClientSession]:
        """Start and connect to the local stdio MCP server."""
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(self.config.script_path)],
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session


class MCPGateway:
    """Gateway for GitHub, Rovo/Atlassian, and local MCP providers."""

    def __init__(self) -> None:
        self._providers: dict[str, GatewayProvider] = {}

    def register_provider(self, provider: GatewayProvider) -> None:
        """Register a vendor adapter such as GitHub or Rovo."""
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def register_local_server(self, namespace: str, script_path: Path) -> None:
        """Register a local stdio MCP server."""
        self.register_provider(
            LocalMCPAdapter(
                LocalMCPConfig(namespace=namespace, script_path=script_path)
            )
        )

    def remove_provider(self, name: str) -> None:
        """Remove one provider."""
        self._providers.pop(name, None)

    def list_providers(self) -> list[str]:
        """Return all registered provider namespaces."""
        return sorted(self._providers)

    async def discover_tools(self) -> list[NamespacedTool]:
        """Discover and namespace tools from every provider."""
        discovered: list[NamespacedTool] = []
        for provider_name in self.list_providers():
            provider = self._providers[provider_name]
            for tool in await provider.list_tools():
                discovered.append(
                    NamespacedTool(
                        name=f"{provider_name}.{tool.name}",
                        description=getattr(tool, "description", "") or "",
                        provider=provider_name,
                        original_name=tool.name,
                    )
                )
        return discovered

    async def call_tool(
        self,
        namespaced_tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Route provider.tool_name to the correct adapter or local MCP server."""
        provider_name, tool_name = self._split_name(namespaced_tool_name)
        return await self._providers[provider_name].call_tool(tool_name, arguments)

    def _split_name(self, namespaced_tool_name: str) -> tuple[str, str]:
        """Split a namespaced tool into provider and original tool name."""
        try:
            provider, tool = namespaced_tool_name.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Tool name must use provider.tool_name format.") from exc
        if provider not in self._providers:
            raise KeyError(f"Unknown gateway provider: {provider}")
        return provider, tool

