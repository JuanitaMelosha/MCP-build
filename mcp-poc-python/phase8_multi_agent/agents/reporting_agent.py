from __future__ import annotations

import json
import logging

from agents.shared_memory import SharedMemory

logger = logging.getLogger("phase8.reporting_agent")


class ReportingAgent:
    """Build the final user-facing workflow report."""

    name = "reporting"

    async def run(self, memory: SharedMemory) -> None:
        """Combine research, planning, and execution results."""
        customer = memory.require("customer")
        plan = memory.require("execution_plan")
        results = memory.require("execution_results")

        report = (
            "Customer issue workflow completed.\n\n"
            "Research:\n"
            f"{json.dumps(customer, indent=2)}\n\n"
            "Plan:\n"
            f"{json.dumps(plan, indent=2)}\n\n"
            "Execution:\n"
            f"{json.dumps(results, indent=2)}"
        )
        memory.write("final_report", report, self.name)
        logger.info("Final report created")

