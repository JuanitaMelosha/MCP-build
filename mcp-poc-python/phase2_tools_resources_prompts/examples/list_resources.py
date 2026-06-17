from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_helpers import connect_to_phase2_server


async def main() -> None:
    async with connect_to_phase2_server() as session:
        resources = await session.list_resources()

    print("MCP resources:")
    for resource in resources.resources:
        print(f"- {resource.name}: {resource.uri}")


if __name__ == "__main__":
    asyncio.run(main())

