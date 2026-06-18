from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import ROOT, configure_logging, load_environment
from oauth.auth_flow import AuthorizationCodeFlow
from oauth.github_provider import GitHubOAuthProvider
from oauth.token_store import TokenStore


async def main() -> None:
    configure_logging()
    load_environment()

    try:
        provider = GitHubOAuthProvider.from_env()
        token = await AuthorizationCodeFlow(provider).login()
    except Exception as exc:
        print(f"OAuth login failed: {exc}")
        return

    store = TokenStore(token_path=ROOT / ".tokens.json", key_path=ROOT / ".token_key")
    store.save("github", token)

    print("GitHub OAuth login succeeded.")
    print(f"Token scope: {token.scope}")
    print("Encrypted token saved to .tokens.json")


if __name__ == "__main__":
    asyncio.run(main())
