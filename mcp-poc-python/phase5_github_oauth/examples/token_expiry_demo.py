from __future__ import annotations

import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import ROOT, build_github_gateway, configure_logging
from oauth.token_store import TokenStore


async def main() -> None:
    configure_logging()
    store = TokenStore(token_path=ROOT / ".tokens.json", key_path=ROOT / ".token_key")
    token = store.load("github")
    if token is None:
        print("No GitHub token found. Run examples/login.py first.")
        return

    token.expires_at = time.time() - 10
    store.save("github", token)
    print("Stored token has been marked expired for the demo.")

    _, adapter = build_github_gateway()
    try:
        await adapter.get_access_token()
        print("Expired token was refreshed successfully.")
    except RuntimeError as exc:
        print("Expired token could not be refreshed.")
        print(str(exc))


if __name__ == "__main__":
    asyncio.run(main())

