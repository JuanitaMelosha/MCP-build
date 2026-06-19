from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from governed_gateway import ApprovalRequired
from governance.rbac import Principal, Role


async def main() -> None:
    requester = Principal("operator-1", Role.OPERATOR)
    approver = Principal("approver-1", Role.APPROVER)

    with temporary_platform() as platform:
        try:
            await platform.governed_gateway.request_tool(
                principal=requester,
                agent_name="execution_agent",
                tool_name="ticket.create_ticket",
                arguments={"title": "Login Issue", "priority": "High"},
            )
        except ApprovalRequired as exc:
            print(exc)
            platform.approvals.approve(
                exc.request_id,
                approver,
                "Customer-impacting ticket creation is justified.",
            )
            result = await platform.governed_gateway.execute_approved(
                exc.request_id,
                executor=approver,
            )
            print(json.dumps(result.result, indent=2))
            print(f"Approval status: {platform.approvals.get(exc.request_id).status}")


if __name__ == "__main__":
    asyncio.run(main())

