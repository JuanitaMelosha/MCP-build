from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from governed_gateway import PolicyDenied
from governance.rbac import Principal, Role


async def main() -> None:
    with temporary_platform() as platform:
        try:
            await platform.governed_gateway.request_tool(
                principal=Principal("admin-1", Role.ADMIN),
                agent_name="reporting_agent",
                tool_name="ticket.create_ticket",
                arguments={"title": "Unauthorized Agent Action", "priority": "High"},
            )
        except PolicyDenied as exc:
            print(f"Agent denied as expected: {exc}")


if __name__ == "__main__":
    asyncio.run(main())

