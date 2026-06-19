from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from governed_gateway import ApprovalRequired
from governance.rbac import Principal, Role


async def main() -> None:
    with temporary_platform() as platform:
        try:
            await platform.governed_gateway.request_tool(
                principal=Principal("operator-1", Role.OPERATOR),
                agent_name="execution_agent",
                tool_name="ops.deploy_production",
                arguments={"service": "payments"},
            )
        except ApprovalRequired as exc:
            print("Critical action escalated.")
            print(exc.decision.explanation())
            print(f"Approval request: {exc.request_id}")


if __name__ == "__main__":
    asyncio.run(main())

