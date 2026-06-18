from __future__ import annotations

import asyncio
import logging
import secrets
import webbrowser
from urllib.parse import parse_qs, urlparse

from oauth.github_provider import GitHubOAuthProvider
from oauth.oauth_client import OAuthClient
from oauth.token_store import OAuthToken

logger = logging.getLogger("phase5.auth_flow")


class AuthorizationCodeFlow:
    """Beginner-friendly OAuth authorization-code flow with a local callback server."""

    def __init__(self, provider: GitHubOAuthProvider) -> None:
        self.provider = provider
        self.oauth_client = OAuthClient(provider)

    async def login(self) -> OAuthToken:
        """Open the browser, receive the callback, and exchange the code for a token."""
        state = secrets.token_urlsafe(24)
        callback = _CallbackServer(expected_state=state)
        url = self.provider.authorization_url(state)

        print("Opening browser for GitHub OAuth login...")
        print(url)
        webbrowser.open(url)

        code = await callback.wait_for_code(self.provider.redirect_uri)
        token = await self.oauth_client.exchange_code(code)
        logger.info("oauth_login_succeeded")
        return token


class _CallbackServer:
    """Tiny local HTTP callback server used by the OAuth login example."""

    def __init__(self, expected_state: str) -> None:
        self.expected_state = expected_state
        self._future: asyncio.Future[str] | None = None

    async def wait_for_code(self, redirect_uri: str) -> str:
        """Wait for GitHub to redirect the browser back with ?code=...&state=...."""
        parsed = urlparse(redirect_uri)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8766
        path = parsed.path or "/callback"

        loop = asyncio.get_running_loop()
        self._future = loop.create_future()
        server = await asyncio.start_server(
            lambda reader, writer: self._handle_request(reader, writer, path),
            host=host,
            port=port,
        )
        async with server:
            return await self._future

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        expected_path: str,
    ) -> None:
        """Parse one HTTP callback request and resolve the authorization code."""
        request_line = await reader.readline()
        request_target = request_line.decode(errors="ignore").split(" ")[1]
        parsed = urlparse(request_target)
        query = parse_qs(parsed.query)

        while True:
            line = await reader.readline()
            if line in {b"\r\n", b""}:
                break

        if parsed.path != expected_path:
            await self._respond(writer, 404, "Unknown OAuth callback path.")
            return

        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]
        error = query.get("error", [""])[0]

        if error:
            self._future_set_exception(RuntimeError(f"OAuth error: {error}"))
            await self._respond(writer, 400, "OAuth failed. You can close this tab.")
            return

        if state != self.expected_state:
            self._future_set_exception(RuntimeError("OAuth state mismatch. Login rejected."))
            await self._respond(writer, 400, "OAuth state mismatch. You can close this tab.")
            return

        self._future_set_result(code)
        await self._respond(writer, 200, "GitHub OAuth login succeeded. You can close this tab.")

    async def _respond(self, writer: asyncio.StreamWriter, status: int, message: str) -> None:
        """Send a minimal HTTP response to the browser."""
        reason = "OK" if status == 200 else "Error"
        body = message.encode()
        writer.write(
            (
                f"HTTP/1.1 {status} {reason}\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode()
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    def _future_set_result(self, code: str) -> None:
        """Set the callback future result if it is still pending."""
        if self._future is not None and not self._future.done():
            self._future.set_result(code)

    def _future_set_exception(self, exc: Exception) -> None:
        """Set the callback future exception if it is still pending."""
        if self._future is not None and not self._future.done():
            self._future.set_exception(exc)

