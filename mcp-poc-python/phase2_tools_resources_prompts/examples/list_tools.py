from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_helpers import connect_to_phase2_server


async def main() -> None:
    async with connect_to_phase2_server() as session:
        tools = await session.list_tools()

    print("MCP tools:")
    for tool in tools.tools:
        print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())

