from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_gateway, configure_logging


async def main() -> None:
    configure_logging()
    try:
        projects = await build_gateway().call_tool("rovo.discover_projects", {})
    except Exception as exc:
        print(f"Jira project discovery failed: {exc}")
        return

    print("Jira projects:")
    for project in projects:
        print(f"- {project.get('key')}: {project.get('name')} (id={project.get('id')})")


if __name__ == "__main__":
    asyncio.run(main())
