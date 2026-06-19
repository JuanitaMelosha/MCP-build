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
        result = await platform.governed_gateway.request_tool(
            principal=Principal("alice", Role.VIEWER),
            agent_name="research_agent",
            tool_name="customer.get_customer",
            arguments={"customer_id": "123"},
        )
        print(result.decision.explanation())
        print(json.dumps(result.result, indent=2))
        print(f"Audit records: {len(platform.audit.records())}")


if __name__ == "__main__":
    asyncio.run(main())

