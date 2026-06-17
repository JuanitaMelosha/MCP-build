from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_helpers import connect_to_phase2_server, tool_result_to_json


async def main() -> None:
    async with connect_to_phase2_server() as session:
        result = await session.call_tool("get_customer", {"customer_id": "123"})

    print("get_customer result:")
    print(json.dumps(tool_result_to_json(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

