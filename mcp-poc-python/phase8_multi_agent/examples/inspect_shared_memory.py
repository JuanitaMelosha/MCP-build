from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_orchestrator


async def main() -> None:
    orchestrator = build_orchestrator()
    await orchestrator.run_customer_issue_workflow(
        "Research customer 123 and create a support ticket"
    )

    print("Registered agents:")
    for name in orchestrator.registry.list_agents():
        print(f"- {name}")

    print("\nShared memory snapshot:")
    print(json.dumps(orchestrator.memory.snapshot(), indent=2))

    print("\nCommunication events:")
    for event in orchestrator.memory.events:
        print(f"- {event.created_at} {event.agent} {event.event_type}")


if __name__ == "__main__":
    asyncio.run(main())

