from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_orchestrator


async def main() -> None:
    orchestrator = build_orchestrator()
    result = await orchestrator.run_customer_issue_workflow(
        "Research customer 123 and create a support ticket"
    )
    print(result.output)
    print("\nWorkflow steps:")
    for step in result.steps:
        print(f"- {step.agent_name}: {step.status}")


if __name__ == "__main__":
    asyncio.run(main())

