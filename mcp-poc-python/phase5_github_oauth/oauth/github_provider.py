from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class GitHubOAuthProvider:
    """GitHub OAuth endpoint and scope configuration."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    authorize_url: str = "https://github.com/login/oauth/authorize"
    token_url: str = "https://github.com/login/oauth/access_token"
    mcp_url: str = "https://api.githubcopilot.com/mcp/"

    @classmethod
    def from_env(cls) -> "GitHubOAuthProvider":
        """Create provider configuration from environment variables."""
        scopes = os.getenv("GITHUB_OAUTH_SCOPES", "repo read:user read:org").split()
        client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
        client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
        redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "http://127.0.0.1:8766/callback")
        mcp_url = os.getenv("GITHUB_MCP_URL", "https://api.githubcopilot.com/mcp/")
        if not client_id or not client_secret:
            raise ValueError(
                "Missing GitHub OAuth credentials. Set GITHUB_OAUTH_CLIENT_ID and "
                "GITHUB_OAUTH_CLIENT_SECRET in .env."
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            mcp_url=mcp_url,
        )

    def authorization_url(self, state: str) -> str:
        """Build the GitHub authorization URL for the browser redirect."""
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
                "state": state,
                "allow_signup": "true",
            }
        )
        return f"{self.authorize_url}?{query}"

