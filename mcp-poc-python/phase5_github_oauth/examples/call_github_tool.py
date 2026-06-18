from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_github_gateway, configure_logging, load_environment


async def main() -> None:
    configure_logging()
    load_environment()

    tool_name = os.getenv("GITHUB_MCP_TOOL", "")
    tool_args = json.loads(os.getenv("GITHUB_MCP_TOOL_ARGS", "{}"))

    try:
        gateway, _ = build_github_gateway()
        if not tool_name:
            tools = await gateway.discover_tools()
            print("Set GITHUB_MCP_TOOL to one of these names, then run this example again:")
            for tool in tools:
                print(f"- {tool.name}")
            return

        if not tool_name.startswith("github."):
            tool_name = f"github.{tool_name}"

        result = await gateway.call_tool(tool_name, tool_args)
    except Exception as exc:
        print(f"GitHub MCP tool call failed: {exc}")
        return

    print(f"{tool_name} result:")
    print(json.dumps(result, indent=2) if not isinstance(result, str) else result)


if __name__ == "__main__":
    asyncio.run(main())
