from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from governance.rbac import Principal, Role


async def main() -> None:
    with temporary_platform() as platform:
        await platform.governed_gateway.request_tool(
            principal=Principal("alice", Role.VIEWER),
            agent_name="research_agent",
            tool_name="weather.get_weather",
            arguments={"city": "Chennai"},
        )
        for record in platform.audit.records():
            print(json.dumps(record.__dict__, default=str, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

