from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_gateway, configure_logging, required_env


async def main() -> None:
    configure_logging()
    try:
        page_id = required_env("ATLASSIAN_CONFLUENCE_PAGE_ID")
        page = await build_gateway().call_tool(
            "rovo.read_page",
            {"page_id": page_id},
        )
    except Exception as exc:
        print(f"Confluence page read failed: {exc}")
        return

    print("Confluence page:")
    print(json.dumps(page, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
