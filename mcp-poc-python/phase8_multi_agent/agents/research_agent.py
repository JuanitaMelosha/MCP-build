from __future__ import annotations

import logging
import re

from agents.shared_memory import SharedMemory
from gateway import MCPGateway

logger = logging.getLogger("phase8.research_agent")


class ResearchAgent:
    """Research customer context and available MCP capabilities."""

    name = "research"

    def __init__(self, gateway: MCPGateway) -> None:
        self.gateway = gateway

    async def run(self, memory: SharedMemory) -> None:
        """Discover tools and collect customer information."""
        request = memory.require("user_request")
        tools = await self.gateway.discover_tools()
        tool_names = [tool.name for tool in tools]
        memory.write("available_tools", tool_names, self.name)
        logger.info("Discovered MCP tools: %s", tool_names)

        customer_id = self._extract_customer_id(request)
        customer = await self.gateway.call_tool(
            "customer.get_customer",
            {"customer_id": customer_id},
        )
        memory.write("customer", customer, self.name)
        memory.write(
            "research_summary",
            {
                "customer_id": customer_id,
                "customer_name": customer["name"],
                "customer_plan": customer["plan"],
                "request": request,
            },
            self.name,
        )
        logger.info("Researched customer %s", customer_id)

    def _extract_customer_id(self, request: str) -> str:
        """Extract a customer id from the workflow request."""
        match = re.search(r"customer\s+(?:id\s+)?([A-Za-z0-9_-]+)", request, re.IGNORECASE)
        return match.group(1) if match else "123"

