from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_agent


async def main() -> None:
    agent = build_agent()
    request = input("User request: ").strip()
    if not request:
        print("Enter a customer, weather, or ticket request.")
        return

    try:
        print(await agent.run(request))
    except Exception as exc:
        print(f"Agent failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())

