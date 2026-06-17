from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.example_helpers import running_remote_server
from gateway import api_key_headers, build_remote_gateway


async def main() -> None:
    with running_remote_server():
        gateway = build_remote_gateway(api_key_headers("viewer-api-key-123"))
        result = await gateway.call_tool(
            "secure_customer.get_customer",
            {"customer_id": "123"},
        )

    print("Remote tool result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

