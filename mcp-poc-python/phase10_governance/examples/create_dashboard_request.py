from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governed_gateway import ApprovalRequired
from governance.rbac import Principal, Role
from governance_platform import build_platform

DATA_DIR = Path(__file__).resolve().parents[1] / "runtime_data"


async def main() -> None:
    platform = build_platform(DATA_DIR)
    try:
        await platform.governed_gateway.request_tool(
            principal=Principal("operator-1", Role.OPERATOR),
            agent_name="execution_agent",
            tool_name="ticket.create_ticket",
            arguments={"title": "Dashboard Approval Demo", "priority": "High"},
        )
    except ApprovalRequired as exc:
        print(exc.request_id)


if __name__ == "__main__":
    asyncio.run(main())

