from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.example_helpers import running_remote_server
from gateway import bearer_headers, build_remote_gateway


async def main() -> None:
    with running_remote_server():
        gateway = build_remote_gateway(bearer_headers("admin-bearer-token-456"))
        result = await gateway.call_tool(
            "secure_customer.create_customer",
            {"name": "Joshua", "plan": "Premium"},
        )

    print("Bearer token authentication succeeded.")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

