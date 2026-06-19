from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from agents.shared_memory import SharedMemory

logger = logging.getLogger("phase8.planning_agent")


@dataclass(frozen=True)
class ExecutionTask:
    """One MCP tool call selected by the planning agent."""

    tool_name: str
    arguments: dict[str, Any]
    purpose: str


class PlanningAgent:
    """Turn research into an executable MCP task plan."""

    name = "planning"

    async def run(self, memory: SharedMemory) -> None:
        """Create and validate the execution plan."""
        research = memory.require("research_summary")
        available_tools = set(memory.require("available_tools"))
        required_tool = "ticket.create_ticket"
        if required_tool not in available_tools:
            raise LookupError(f"Required MCP tool was not discovered: {required_tool}")

        task = ExecutionTask(
            tool_name=required_tool,
            arguments={
                "title": (
                    f"Customer issue for {research['customer_name']} "
                    f"({research['customer_id']})"
                ),
                "priority": self._priority_for_plan(research["customer_plan"]),
            },
            purpose="Create a support ticket using the researched customer context.",
        )
        memory.write("execution_plan", [asdict(task)], self.name)
        logger.info("Created execution plan: %s", task)

    def _priority_for_plan(self, customer_plan: str) -> str:
        """Choose ticket priority from the customer's service plan."""
        return "High" if customer_plan.lower() == "premium" else "Medium"

