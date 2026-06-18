from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_github_gateway, configure_logging


async def main() -> None:
    configure_logging()
    try:
        gateway, _ = build_github_gateway()
        tools = await gateway.discover_tools()
    except Exception as exc:
        print(f"GitHub MCP tool discovery failed: {exc}")
        return

    print("GitHub MCP tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())
