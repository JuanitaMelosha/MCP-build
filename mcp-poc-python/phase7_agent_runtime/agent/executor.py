from __future__ import annotations

import logging

from agent.memory import AgentMemory, Observation
from agent.planner import AgentPlan, PlanStep, Planner
from gateway import MCPGateway

logger = logging.getLogger("phase7.executor")


class ToolExecutor:
    """Execute planned tools through the MCP Gateway."""

    def __init__(self, gateway: MCPGateway, planner: Planner) -> None:
        self.gateway = gateway
        self.planner = planner

    async def execute(self, plan: AgentPlan, memory: AgentMemory) -> list[Observation]:
        """Execute all plan steps in order and record observations."""
        observations: list[Observation] = []
        for index, original_step in enumerate(plan.steps, start=1):
            step = self.planner.resolve_step(original_step, memory)
            self._log_step(index, step)
            result = await self.gateway.call_tool(step.tool_name, step.arguments)
            observation = Observation(step.tool_name, step.arguments, result)
            memory.add_observation(observation)
            observations.append(observation)
            logger.info("Step %s succeeded: %s", index, step.tool_name)
        return observations

    def _log_step(self, index: int, step: PlanStep) -> None:
        """Log the observable execution decision for one step."""
        logger.info(
            "Executing step %s: intent=%s tool=%s arguments=%s",
            index,
            step.intent,
            step.tool_name,
            step.arguments,
        )
