from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from oauth.github_provider import GitHubOAuthProvider
from oauth.oauth_client import OAuthClient
from oauth.token_store import OAuthToken, TokenStore

logger = logging.getLogger("phase5.vendor_adapter")


class VendorAdapter(ABC):
    """Abstract adapter for vendor-hosted remote MCP ecosystems."""

    name: str

    @abstractmethod
    async def get_access_token(self) -> str:
        """Return a valid access token for this vendor."""

    @abstractmethod
    def mcp_url(self) -> str:
        """Return the vendor MCP endpoint URL."""

    async def list_tools(self) -> list[Any]:
        """Connect to the vendor MCP server and list tools."""
        async with self._session() as session:
            result = await session.list_tools()
        return list(result.tools)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Connect to the vendor MCP server and call a tool."""
        async with self._session() as session:
            return await session.call_tool(tool_name, arguments)

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[ClientSession]:
        """Create an MCP ClientSession using the vendor access token."""
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with streamablehttp_client(self.mcp_url(), headers=headers) as streams:
            read_stream, write_stream = streams[0], streams[1]
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session


class GitHubMCPAdapter(VendorAdapter):
    """GitHub remote MCP adapter backed by OAuth tokens."""

    name = "github"

    def __init__(self, provider: GitHubOAuthProvider, token_store: TokenStore) -> None:
        self.provider = provider
        self.token_store = token_store
        self.oauth_client = OAuthClient(provider)

    def mcp_url(self) -> str:
        """Return the GitHub MCP endpoint."""
        return self.provider.mcp_url

    async def get_access_token(self) -> str:
        """Load a valid GitHub access token, refreshing it when possible."""
        token = self.token_store.load("github")
        if token is None:
            raise RuntimeError("No GitHub token found. Run examples/login.py first.")

        if token.is_expired():
            if token.refresh_token is None:
                raise RuntimeError(
                    "GitHub token is expired and no refresh token is available. Run login again."
                )
            logger.info("github_token_expired_refreshing")
            token = await self.oauth_client.refresh(token.refresh_token)
            self.token_store.save("github", token)

        return token.access_token

    async def refresh_token(self) -> OAuthToken:
        """Force refresh the stored GitHub token."""
        token = self.token_store.load("github")
        if token is None:
            raise RuntimeError("No GitHub token found. Run examples/login.py first.")
        if token.refresh_token is None:
            raise RuntimeError(
                "Stored GitHub token has no refresh token. GitHub OAuth Apps only return "
                "refresh tokens when expiring user tokens are enabled."
            )
        refreshed = await self.oauth_client.refresh(token.refresh_token)
        self.token_store.save("github", refreshed)
        return refreshed
