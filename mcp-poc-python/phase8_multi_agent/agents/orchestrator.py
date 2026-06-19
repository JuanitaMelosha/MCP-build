from __future__ import annotations

import logging

from agents.agent_registry import AgentRegistry
from agents.execution_agent import ExecutionAgent
from agents.planning_agent import PlanningAgent
from agents.reporting_agent import ReportingAgent
from agents.research_agent import ResearchAgent
from agents.shared_memory import SharedMemory
from agents.workflow_engine import WorkflowEngine, WorkflowResult
from gateway import MCPGateway

logger = logging.getLogger("phase8.orchestrator")


class Orchestrator:
    """Register agents, delegate workflow steps, and return the final result."""

    DEFAULT_WORKFLOW = ["research", "planning", "execution", "reporting"]

    def __init__(self, gateway: MCPGateway) -> None:
        self.gateway = gateway
        self.memory = SharedMemory()
        self.registry = AgentRegistry()
        self.registry.register(ResearchAgent(gateway))
        self.registry.register(PlanningAgent())
        self.registry.register(ExecutionAgent(gateway))
        self.registry.register(ReportingAgent())
        self.workflow_engine = WorkflowEngine(self.registry)

    async def run_customer_issue_workflow(self, user_request: str) -> WorkflowResult:
        """Run research, planning, execution, and reporting agents."""
        self.memory.clear()
        self.memory.write("user_request", user_request, "orchestrator")
        self.memory.publish(
            "orchestrator",
            "workflow_delegated",
            {"agents": self.DEFAULT_WORKFLOW},
        )
        logger.info("Delegating workflow to: %s", self.DEFAULT_WORKFLOW)
        return await self.workflow_engine.execute(self.DEFAULT_WORKFLOW, self.memory)

