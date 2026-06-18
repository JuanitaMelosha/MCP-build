from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from oauth.github_provider import GitHubOAuthProvider
from oauth.token_store import OAuthToken

logger = logging.getLogger("phase5.oauth_client")


class OAuthClient:
    """Small OAuth 2.0 client for GitHub authorization-code token operations."""

    def __init__(self, provider: GitHubOAuthProvider) -> None:
        self.provider = provider

    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange an authorization code for an access token."""
        payload = {
            "client_id": self.provider.client_id,
            "client_secret": self.provider.client_secret,
            "code": code,
            "redirect_uri": self.provider.redirect_uri,
        }
        logger.info("exchanging_authorization_code")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.provider.token_url,
                data=payload,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def refresh(self, refresh_token: str) -> OAuthToken:
        """Refresh an expired access token when GitHub issued a refresh token."""
        payload = {
            "client_id": self.provider.client_id,
            "client_secret": self.provider.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        logger.info("refreshing_access_token")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.provider.token_url,
                data=payload,
                headers={"Accept": "application/json"},
            )
        if response.status_code >= 400:
            logger.warning("token_refresh_failed", extra={"status_code": response.status_code})
        response.raise_for_status()
        return self._parse_token(response.json(), fallback_refresh_token=refresh_token)

    def _parse_token(
        self,
        data: dict[str, Any],
        fallback_refresh_token: str | None = None,
    ) -> OAuthToken:
        """Convert a GitHub token response into OAuthToken."""
        if "error" in data:
            raise RuntimeError(f"OAuth token error: {data.get('error_description', data['error'])}")

        expires_at = None
        if data.get("expires_in") is not None:
            expires_at = time.time() + int(data["expires_in"])

        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            scope=data.get("scope", ""),
            refresh_token=data.get("refresh_token") or fallback_refresh_token,
            expires_at=expires_at,
        )

