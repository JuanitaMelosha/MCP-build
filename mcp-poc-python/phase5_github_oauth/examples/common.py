from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

from gateway import MCPGateway
from oauth.github_provider import GitHubOAuthProvider
from oauth.token_store import TokenStore
from vendor_adapter import GitHubMCPAdapter

ROOT = Path(__file__).resolve().parents[1]


def configure_logging() -> None:
    """Configure simple structured-ish logging for examples."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_environment() -> None:
    """Load Phase 5 .env values."""
    load_dotenv(ROOT / ".env")


def build_github_gateway() -> tuple[MCPGateway, GitHubMCPAdapter]:
    """Create a gateway with the GitHub MCP adapter registered."""
    load_environment()
    provider = GitHubOAuthProvider.from_env()
    store = TokenStore(token_path=ROOT / ".tokens.json", key_path=ROOT / ".token_key")
    adapter = GitHubMCPAdapter(provider=provider, token_store=store)
    gateway = MCPGateway()
    gateway.register_vendor(adapter)
    return gateway, adapter

