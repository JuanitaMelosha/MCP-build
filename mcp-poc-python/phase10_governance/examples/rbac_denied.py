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
                principal=Principal("viewer-1", Role.VIEWER),
                agent_name="execution_agent",
                tool_name="ticket.create_ticket",
                arguments={"title": "Login Issue", "priority": "High"},
            )
        except PolicyDenied as exc:
            print(f"Denied as expected: {exc}")


if __name__ == "__main__":
    asyncio.run(main())

