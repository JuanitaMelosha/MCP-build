from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from vendor_adapter import VendorAdapter

logger = logging.getLogger("phase5.gateway")


@dataclass(frozen=True)
class NamespacedVendorTool:
    """A vendor MCP tool exposed through the gateway namespace."""

    name: str
    description: str
    vendor: str
    original_name: str


class MCPGateway:
    """Gateway that supports vendor adapters such as GitHub MCP."""

    def __init__(self) -> None:
        self._vendors: dict[str, VendorAdapter] = {}

    def register_vendor(self, adapter: VendorAdapter) -> None:
        """Register one vendor MCP adapter."""
        if adapter.name in self._vendors:
            raise ValueError(f"Vendor already registered: {adapter.name}")
        self._vendors[adapter.name] = adapter
        logger.info("vendor_registered", extra={"vendor": adapter.name})

    def remove_vendor(self, name: str) -> None:
        """Remove one registered vendor adapter."""
        self._vendors.pop(name, None)
        logger.info("vendor_removed", extra={"vendor": name})

    def list_vendors(self) -> list[str]:
        """Return registered vendor namespaces."""
        return sorted(self._vendors)

    async def discover_tools(self) -> list[NamespacedVendorTool]:
        """Discover tools from every registered vendor MCP adapter."""
        tools: list[NamespacedVendorTool] = []
        for name in self.list_vendors():
            adapter = self._vendors[name]
            for tool in await adapter.list_tools():
                tools.append(
                    NamespacedVendorTool(
                        name=f"{name}.{tool.name}",
                        description=tool.description or "",
                        vendor=name,
                        original_name=tool.name,
                    )
                )
        return tools

    async def call_tool(self, namespaced_tool_name: str, arguments: dict[str, Any]) -> Any:
        """Route a namespaced vendor tool call."""
        vendor_name, tool_name = self._split_tool_name(namespaced_tool_name)
        result = await self._vendors[vendor_name].call_tool(tool_name, arguments)
        if getattr(result, "isError", False):
            text = result.content[0].text if result.content else "Vendor MCP tool failed."
            raise RuntimeError(text)
        if result.content and hasattr(result.content[0], "text"):
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return result

    def _split_tool_name(self, namespaced_tool_name: str) -> tuple[str, str]:
        """Split github.some_tool into github and some_tool."""
        try:
            vendor, tool = namespaced_tool_name.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Tool name must use vendor.tool_name format.") from exc
        if vendor not in self._vendors:
            raise KeyError(f"Unknown vendor: {vendor}")
        return vendor, tool

