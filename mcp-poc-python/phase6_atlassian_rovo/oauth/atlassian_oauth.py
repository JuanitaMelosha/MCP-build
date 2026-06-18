from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from oauth.token_store import OAuthToken

logger = logging.getLogger("phase6.oauth")


@dataclass(frozen=True)
class AtlassianOAuthConfig:
    """Atlassian OAuth 2.0 (3LO) application configuration."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    authorize_url: str = "https://auth.atlassian.com/authorize"
    token_url: str = "https://auth.atlassian.com/oauth/token"
    accessible_resources_url: str = (
        "https://api.atlassian.com/oauth/token/accessible-resources"
    )

    @classmethod
    def from_env(cls) -> "AtlassianOAuthConfig":
        """Load OAuth configuration from environment variables."""
        client_id = os.getenv("ATLASSIAN_CLIENT_ID", "")
        client_secret = os.getenv("ATLASSIAN_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            raise ValueError(
                "Set ATLASSIAN_CLIENT_ID and ATLASSIAN_CLIENT_SECRET in Phase 6 .env."
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv(
                "ATLASSIAN_REDIRECT_URI",
                "http://127.0.0.1:8767/callback",
            ),
            scopes=os.getenv(
                "ATLASSIAN_SCOPES",
                "read:jira-work write:jira-work read:jira-user "
                "read:confluence-content.all search:confluence offline_access",
            ).split(),
        )

    def authorization_url(self, state: str) -> str:
        """Build Atlassian's authorization URL."""
        query = urlencode(
            {
                "audience": "api.atlassian.com",
                "client_id": self.client_id,
                "scope": " ".join(self.scopes),
                "redirect_uri": self.redirect_uri,
                "state": state,
                "response_type": "code",
                "prompt": "consent",
            }
        )
        return f"{self.authorize_url}?{query}"


class AtlassianOAuthClient:
    """HTTP client for Atlassian OAuth code exchange and token refresh."""

    def __init__(self, config: AtlassianOAuthConfig) -> None:
        self.config = config

    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange an authorization code for access and refresh tokens."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }
        logger.info("atlassian_authorization_code_exchange")
        return await self._request_token(payload)

    async def refresh(self, refresh_token: str) -> OAuthToken:
        """Refresh an access token using Atlassian's rotating refresh token."""
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }
        logger.info("atlassian_access_token_refresh")
        return await self._request_token(payload, previous_refresh_token=refresh_token)

    async def _request_token(
        self,
        payload: dict[str, str],
        previous_refresh_token: str | None = None,
    ) -> OAuthToken:
        """POST a token request and normalize the response."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.config.token_url,
                json=payload,
                headers={"Accept": "application/json"},
            )
        if response.status_code >= 400:
            logger.warning(
                "atlassian_token_request_failed",
                extra={"status_code": response.status_code},
            )
            raise RuntimeError(self._error_message(response))

        data: dict[str, Any] = response.json()
        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token") or previous_refresh_token,
            expires_at=time.time() + int(data.get("expires_in", 3600)),
            scope=data.get("scope", " ".join(self.config.scopes)),
            token_type=data.get("token_type", "Bearer"),
        )

    def _error_message(self, response: httpx.Response) -> str:
        """Create a readable OAuth error message."""
        try:
            data = response.json()
            detail = data.get("error_description") or data.get("error") or response.text
        except ValueError:
            detail = response.text
        return f"Atlassian OAuth request failed with HTTP {response.status_code}: {detail}"

