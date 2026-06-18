from __future__ import annotations

import asyncio
import secrets
import webbrowser
from urllib.parse import parse_qs, urlparse

from oauth.atlassian_oauth import AtlassianOAuthClient, AtlassianOAuthConfig
from oauth.token_store import OAuthToken


class AtlassianAuthorizationCodeFlow:
    """Browser-based Atlassian OAuth 2.0 authorization-code flow."""

    def __init__(self, config: AtlassianOAuthConfig) -> None:
        self.config = config
        self.client = AtlassianOAuthClient(config)

    async def login(self) -> OAuthToken:
        """Open consent, receive the callback, and exchange the code."""
        state = secrets.token_urlsafe(24)
        callback = _CallbackServer(expected_state=state)
        authorization_url = self.config.authorization_url(state)

        print("Opening Atlassian OAuth consent in your browser...")
        print(authorization_url)
        webbrowser.open(authorization_url)

        code = await callback.wait_for_code(self.config.redirect_uri)
        return await self.client.exchange_code(code)


class _CallbackServer:
    """Small local HTTP server that receives Atlassian's OAuth callback."""

    def __init__(self, expected_state: str) -> None:
        self.expected_state = expected_state
        self._future: asyncio.Future[str] | None = None

    async def wait_for_code(self, redirect_uri: str) -> str:
        """Listen until Atlassian redirects with an authorization code."""
        parsed = urlparse(redirect_uri)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8767
        expected_path = parsed.path or "/callback"
        self._future = asyncio.get_running_loop().create_future()

        server = await asyncio.start_server(
            lambda reader, writer: self._handle_request(
                reader,
                writer,
                expected_path,
            ),
            host,
            port,
        )
        async with server:
            return await self._future

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        expected_path: str,
    ) -> None:
        """Validate one callback and return its code."""
        request_line = await reader.readline()
        parts = request_line.decode(errors="ignore").split(" ")
        target = parts[1] if len(parts) > 1 else "/"
        parsed = urlparse(target)
        query = parse_qs(parsed.query)

        while True:
            line = await reader.readline()
            if line in {b"\r\n", b""}:
                break

        if parsed.path != expected_path:
            await self._respond(writer, 404, "Unknown OAuth callback path.")
            return

        error = query.get("error", [""])[0]
        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]

        if error:
            self._reject(RuntimeError(f"Atlassian OAuth error: {error}"))
            await self._respond(writer, 400, "Atlassian OAuth failed. Close this tab.")
            return
        if state != self.expected_state:
            self._reject(RuntimeError("OAuth state mismatch. Login rejected."))
            await self._respond(writer, 400, "OAuth state mismatch. Close this tab.")
            return
        if not code:
            self._reject(RuntimeError("Atlassian callback did not include a code."))
            await self._respond(writer, 400, "Missing OAuth code. Close this tab.")
            return

        if self._future is not None and not self._future.done():
            self._future.set_result(code)
        await self._respond(writer, 200, "Atlassian OAuth succeeded. Close this tab.")

    def _reject(self, error: Exception) -> None:
        """Reject the pending callback future."""
        if self._future is not None and not self._future.done():
            self._future.set_exception(error)

    async def _respond(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        message: str,
    ) -> None:
        """Return a small browser response."""
        body = message.encode()
        writer.write(
            (
                f"HTTP/1.1 {status} {'OK' if status == 200 else 'Error'}\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode()
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

