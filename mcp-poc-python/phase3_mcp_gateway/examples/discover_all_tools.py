from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gateway import build_default_gateway


async def main() -> None:
    gateway = build_default_gateway()
    tools = await gateway.discover_tools()

    print("Namespaced MCP tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())

