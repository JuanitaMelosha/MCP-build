from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.orchestrator import Orchestrator
from gateway import MCPGateway


async def main() -> None:
    # Empty gateway: Research Agent cannot call customer.get_customer.
    orchestrator = Orchestrator(MCPGateway())
    result = await orchestrator.run_customer_issue_workflow(
        "Research customer 123 and create a support ticket"
    )

    print(result.output)
    print("\nWorkflow steps:")
    for step in result.steps:
        detail = f" - {step.error}" if step.error else ""
        print(f"- {step.agent_name}: {step.status}{detail}")


if __name__ == "__main__":
    asyncio.run(main())

