from __future__ import annotations

import logging
from typing import Any

from agents.shared_memory import SharedMemory
from gateway import MCPGateway

logger = logging.getLogger("phase8.execution_agent")


class ExecutionAgent:
    """Execute planned MCP tool calls through the gateway."""

    name = "execution"

    def __init__(self, gateway: MCPGateway) -> None:
        self.gateway = gateway

    async def run(self, memory: SharedMemory) -> None:
        """Execute every planned task and store results."""
        plan: list[dict[str, Any]] = memory.require("execution_plan")
        results: list[dict[str, Any]] = []

        for index, task in enumerate(plan, start=1):
            logger.info(
                "Executing task %s: tool=%s arguments=%s",
                index,
                task["tool_name"],
                task["arguments"],
            )
            result = await self.gateway.call_tool(task["tool_name"], task["arguments"])
            results.append(
                {
                    "tool_name": task["tool_name"],
                    "arguments": task["arguments"],
                    "purpose": task["purpose"],
                    "result": result,
                }
            )
            memory.publish(
                self.name,
                "tool_executed",
                {"tool": task["tool_name"], "result": result},
            )

        memory.write("execution_results", results, self.name)

