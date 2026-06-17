from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.example_helpers import running_remote_server
from gateway import api_key_headers, build_remote_gateway


async def main() -> None:
    with running_remote_server():
        gateway = build_remote_gateway(api_key_headers("wrong-api-key"))
        try:
            await gateway.discover_tools()
        except ConnectionError as exc:
            print("Invalid credentials failed as expected.")
            print(str(exc))


if __name__ == "__main__":
    asyncio.run(main())

