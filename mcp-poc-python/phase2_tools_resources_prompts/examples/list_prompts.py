from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_helpers import connect_to_phase2_server


async def main() -> None:
    async with connect_to_phase2_server() as session:
        prompts = await session.list_prompts()

    print("MCP prompts:")
    for prompt in prompts.prompts:
        print(f"- {prompt.name}: {prompt.description}")


if __name__ == "__main__":
    asyncio.run(main())

