from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from gateway import MCPGateway
from oauth.atlassian_oauth import AtlassianOAuthConfig
from oauth.token_store import TokenStore
from providers.rovo_adapter import RovoAdapter

ROOT = Path(__file__).resolve().parents[1]


def configure_logging() -> None:
    """Configure readable logs without printing credentials."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_environment() -> None:
    """Load the Phase 6 .env file."""
    load_dotenv(ROOT / ".env")


def build_rovo_adapter() -> RovoAdapter:
    """Build the REST-backed Atlassian/Rovo adapter."""
    load_environment()
    config = AtlassianOAuthConfig.from_env()
    store = TokenStore(
        token_path=ROOT / ".tokens.json",
        key_path=ROOT / ".token_key",
    )
    return RovoAdapter(
        config=config,
        token_store=store,
        default_cloud_id=os.getenv("ATLASSIAN_CLOUD_ID") or None,
    )


def build_gateway() -> MCPGateway:
    """Create the shared gateway with the Rovo adapter registered."""
    gateway = MCPGateway()
    gateway.register_provider(build_rovo_adapter())
    return gateway


def required_env(name: str) -> str:
    """Return one required environment value or raise a readable error."""
    load_environment()
    value = os.getenv(name, "")
    if not value:
        raise ValueError(f"Set {name} in Phase 6 .env.")
    return value
