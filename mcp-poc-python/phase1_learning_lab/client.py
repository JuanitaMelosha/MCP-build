from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def extract_text(result: Any) -> str:
    """Extract the first text payload from an MCP tool result."""
    if result.content and hasattr(result.content[0], "text"):
        return result.content[0].text
    return str(result)


async def main() -> None:
    """Connect to the MCP server, discover tools, and call hello_world."""
    server_path = Path(__file__).with_name("server.py")
    server = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Discovered tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            result = await session.call_tool("hello_world", {"name": "Joshua"})
            text = extract_text(result)

            print("\nTool execution result:")
            print(json.dumps(json.loads(text), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

