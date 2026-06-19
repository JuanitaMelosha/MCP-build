from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import seed_organizational_memory, temporary_platform


async def main() -> None:
    with temporary_platform() as platform:
        seed_organizational_memory(platform)

        first = await platform.agent.handle(
            "Get customer 123 and create a ticket for a login issue"
        )
        print(first.response)

        print("\n--- Second request uses accumulated memory ---\n")
        second = await platform.agent.handle(
            "What do we remember about customer 123?"
        )
        print(second.response)


if __name__ == "__main__":
    asyncio.run(main())

