from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import ROOT, configure_logging, load_environment
from oauth.atlassian_oauth import AtlassianOAuthConfig
from oauth.auth_flow import AtlassianAuthorizationCodeFlow
from oauth.token_store import TokenStore
from providers.rovo_adapter import RovoAdapter


async def main() -> None:
    configure_logging()
    load_environment()
    try:
        config = AtlassianOAuthConfig.from_env()
        token = await AtlassianAuthorizationCodeFlow(config).login()
        store = TokenStore(
            token_path=ROOT / ".tokens.json",
            key_path=ROOT / ".token_key",
        )
        store.save(token)
        adapter = RovoAdapter(config=config, token_store=store)
        workspaces = await adapter.discover_workspaces()
    except Exception as exc:
        print(f"Atlassian OAuth login failed: {exc}")
        return

    print("Atlassian OAuth login succeeded.")
    print("Authorized workspaces/sites:")
    for workspace in workspaces:
        print(f"- {workspace.name}: cloud_id={workspace.id}, url={workspace.url}")
    print("Copy the selected cloud_id into ATLASSIAN_CLOUD_ID in .env.")


if __name__ == "__main__":
    asyncio.run(main())

