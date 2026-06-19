from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inspector.mcp_inspector import InspectorConfig, MCPInspector, Transport


async def main() -> None:
    """Inspect and call the Enterprise Project Management server."""
    server = ROOT / "enterprise_pm" / "server.py"
    async with MCPInspector(
        InspectorConfig(
            transport=Transport.STDIO,
            command=sys.executable,
            args=[str(server), "stdio"],
        )
    ) as inspector:
        report = await inspector.inspect()
        status = await inspector.call_tool(
            "project_status_report",
            {"project_id": "P-100"},
        )
        handbook = await inspector.read_resource("pm://handbook")

    print(
        json.dumps(
            {
                "server": report["server_info"],
                "tools": [tool["name"] for tool in report["tools"]],
                "resources": [item["name"] for item in report["resources"]],
                "prompts": [item["name"] for item in report["prompts"]],
                "status": inspector._serialize(status),
                "handbook": inspector._serialize(handbook),
                "timings": report["timings"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

