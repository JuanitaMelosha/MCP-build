from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_agent


async def main() -> None:
    agent = build_agent()
    print(await agent.run("Get customer 123"))


if __name__ == "__main__":
    asyncio.run(main())

