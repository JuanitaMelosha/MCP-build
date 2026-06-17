from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_helpers import connect_to_phase2_server, resource_result_to_text


async def main() -> None:
    async with connect_to_phase2_server() as session:
        result = await session.read_resource("company://policy")

    text = resource_result_to_text(result)
    print("company_policy:")
    print(json.dumps(json.loads(text), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

