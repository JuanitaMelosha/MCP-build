from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from agents.agent_registry import AgentRegistry
from agents.shared_memory import SharedMemory

logger = logging.getLogger("phase8.workflow")


class StepStatus(StrEnum):
    """Lifecycle states for a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """One delegated agent step."""

    agent_name: str
    status: StepStatus = StepStatus.PENDING
    error: str | None = None


@dataclass
class WorkflowResult:
    """Final workflow status and shared-memory snapshot."""

    succeeded: bool
    steps: list[WorkflowStep]
    output: str


class WorkflowEngine:
    """Execute registered agents sequentially with failure handling."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    async def execute(
        self,
        agent_names: list[str],
        memory: SharedMemory,
    ) -> WorkflowResult:
        """Delegate each workflow step and stop cleanly on failure."""
        steps = [WorkflowStep(agent_name=name) for name in agent_names]
        for index, step in enumerate(steps, start=1):
            step.status = StepStatus.RUNNING
            memory.publish("workflow_engine", "agent_started", {"agent": step.agent_name})
            logger.info("Starting step %s with %s", index, step.agent_name)
            try:
                await self.registry.get(step.agent_name).run(memory)
            except Exception as exc:
                step.status = StepStatus.FAILED
                step.error = str(exc)
                memory.write(
                    "workflow_error",
                    {"agent": step.agent_name, "message": str(exc)},
                    "workflow_engine",
                )
                logger.error("Agent %s failed: %s", step.agent_name, exc)
                return WorkflowResult(
                    succeeded=False,
                    steps=steps,
                    output=f"Workflow failed in {step.agent_name}: {exc}",
                )

            step.status = StepStatus.COMPLETED
            memory.publish("workflow_engine", "agent_completed", {"agent": step.agent_name})
            logger.info("Completed step %s with %s", index, step.agent_name)

        return WorkflowResult(
            succeeded=True,
            steps=steps,
            output=memory.require("final_report"),
        )
