from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_github_gateway, configure_logging


async def main() -> None:
    configure_logging()
    try:
        _, adapter = build_github_gateway()
        token = await adapter.refresh_token()
    except Exception as exc:
        print(f"Token refresh failed: {exc}")
        return
    print("GitHub token refreshed and saved.")
    print(f"Scope: {token.scope}")


if __name__ == "__main__":
    asyncio.run(main())
