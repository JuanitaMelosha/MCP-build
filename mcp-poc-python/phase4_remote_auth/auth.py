from __future__ import annotations

import contextvars
import json
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

logger = logging.getLogger("phase4.auth")


@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity used for authorization checks."""

    subject: str
    role: str
    auth_method: str


class AuthenticationError(Exception):
    """Raised when credentials are missing or invalid."""


class AuthorizationError(Exception):
    """Raised when a caller is authenticated but not allowed to perform an action."""


CURRENT_PRINCIPAL: contextvars.ContextVar[Principal | None] = contextvars.ContextVar(
    "current_principal",
    default=None,
)

API_KEYS: dict[str, Principal] = {
    "viewer-api-key-123": Principal(
        subject="api-key-viewer",
        role="viewer",
        auth_method="api_key",
    ),
    "admin-api-key-456": Principal(
        subject="api-key-admin",
        role="admin",
        auth_method="api_key",
    ),
}

BEARER_TOKENS: dict[str, Principal] = {
    "viewer-bearer-token-123": Principal(
        subject="bearer-viewer",
        role="viewer",
        auth_method="bearer",
    ),
    "admin-bearer-token-456": Principal(
        subject="bearer-admin",
        role="admin",
        auth_method="bearer",
    ),
}


def authenticate(headers: dict[bytes, bytes]) -> Principal:
    """Authenticate one HTTP request using X-API-Key or Authorization: Bearer."""
    api_key = headers.get(b"x-api-key", b"").decode()
    authorization = headers.get(b"authorization", b"").decode()

    if api_key:
        principal = API_KEYS.get(api_key)
        if principal is None:
            raise AuthenticationError("Invalid API key.")
        return principal

    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        principal = BEARER_TOKENS.get(token)
        if principal is None:
            raise AuthenticationError("Invalid bearer token.")
        return principal

    raise AuthenticationError("Missing credentials. Use X-API-Key or Authorization: Bearer.")


def require_role(*allowed_roles: str) -> Principal:
    """Return the current principal if its role is allowed."""
    principal = CURRENT_PRINCIPAL.get()
    if principal is None:
        raise AuthenticationError("No authenticated principal is available.")
    if principal.role not in allowed_roles:
        raise AuthorizationError(
            f"Role '{principal.role}' cannot perform this operation. "
            f"Allowed roles: {', '.join(allowed_roles)}."
        )
    return principal


class AuthenticationMiddleware:
    """ASGI middleware that authenticates every remote MCP HTTP request."""

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in {"/health", "/"}:
            await self.app(scope, receive, send)
            return

        try:
            principal = authenticate(dict(scope["headers"]))
        except AuthenticationError as exc:
            logger.warning(
                "authentication_failed",
                extra={"path": path, "reason": str(exc)},
            )
            await self._send_json(send, status=401, payload={"error": str(exc)})
            return

        token = CURRENT_PRINCIPAL.set(principal)
        logger.info(
            "authentication_succeeded",
            extra={
                "subject": principal.subject,
                "role": principal.role,
                "auth_method": principal.auth_method,
                "path": path,
            },
        )
        try:
            await self.app(scope, receive, send)
        finally:
            CURRENT_PRINCIPAL.reset(token)

    async def _send_json(self, send: Callable, status: int, payload: dict[str, str]) -> None:
        body = json.dumps(payload).encode()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

