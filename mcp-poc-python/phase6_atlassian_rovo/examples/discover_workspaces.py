from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_gateway, configure_logging


async def main() -> None:
    configure_logging()
    try:
        workspaces = await build_gateway().call_tool("rovo.discover_workspaces", {})
    except Exception as exc:
        print(f"Workspace discovery failed: {exc}")
        return

    print("Atlassian workspaces/sites:")
    for workspace in workspaces:
        print(f"- {workspace.name}: cloud_id={workspace.id}, url={workspace.url}")


if __name__ == "__main__":
    asyncio.run(main())
