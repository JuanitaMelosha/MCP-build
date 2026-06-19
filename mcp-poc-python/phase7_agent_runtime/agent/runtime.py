from __future__ import annotations

import json
import logging

from agent.executor import ToolExecutor
from agent.memory import AgentMemory, Observation
from agent.planner import Planner
from agent.tool_selector import ToolSelector
from gateway import MCPGateway

logger = logging.getLogger("phase7.runtime")


class AgentRuntime:
    """Coordinate discovery, planning, execution, memory, and response formatting."""

    def __init__(self, gateway: MCPGateway) -> None:
        self.gateway = gateway
        self.memory = AgentMemory()
        self.tool_selector = ToolSelector()
        self.planner = Planner(self.tool_selector)
        self.executor = ToolExecutor(gateway, self.planner)

    async def run(self, user_request: str) -> str:
        """Handle one user request from discovery through final response."""
        self.memory.add_user_message(user_request)

        logger.info("Discovering tools from the MCP Gateway")
        tools = await self.gateway.discover_tools()
        logger.info("Discovered %s tools: %s", len(tools), [tool.name for tool in tools])

        plan = self.planner.create_plan(user_request, tools)
        logger.info(
            "Created plan: %s",
            [
                {"tool": step.tool_name, "arguments": step.arguments}
                for step in plan.steps
            ],
        )

        observations = await self.executor.execute(plan, self.memory)
        response = self._format_response(observations)
        self.memory.add_assistant_message(response)
        return response

    def _format_response(self, observations: list[Observation]) -> str:
        """Format one or more tool results for the user."""
        if len(observations) == 1:
            observation = observations[0]
            return (
                f"{observation.tool_name} result:\n"
                f"{json.dumps(observation.result, indent=2)}"
            )

        sections = ["Workflow completed:"]
        for index, observation in enumerate(observations, start=1):
            sections.append(
                f"\nStep {index} - {observation.tool_name}\n"
                f"{json.dumps(observation.result, indent=2)}"
            )
        return "\n".join(sections)
