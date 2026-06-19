from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inspector.mcp_inspector import InspectorConfig, MCPInspector, Transport


async def main() -> None:
    """Verify discovery, tools, resources, and prompts on the challenge server."""
    server = Path(__file__).with_name("server.py")
    async with MCPInspector(
        InspectorConfig(
            transport=Transport.STDIO,
            command=sys.executable,
            args=[str(server), "stdio"],
        )
    ) as inspector:
        report = await inspector.inspect()
        declared = await inspector.call_tool(
            "declare_incident",
            {
                "title": "Checkout latency",
                "severity": "SEV-2",
                "service": "checkout",
            },
        )
        resource = await inspector.read_resource("incident://runbook")

    print(
        json.dumps(
            {
                "tools": [tool["name"] for tool in report["tools"]],
                "resources": [item["name"] for item in report["resources"]],
                "prompts": [item["name"] for item in report["prompts"]],
                "declared_incident": inspector._serialize(declared),
                "runbook": inspector._serialize(resource),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

