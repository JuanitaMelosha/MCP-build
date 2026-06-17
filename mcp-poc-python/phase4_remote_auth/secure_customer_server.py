from __future__ import annotations

import logging

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from auth import AuthenticationMiddleware, AuthorizationError, require_role

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("mcp").setLevel(logging.WARNING)
logger = logging.getLogger("phase4.secure_customer_mcp")

mcp = FastMCP(
    "SecureCustomerMCP",
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def get_customer(customer_id: str) -> dict[str, str]:
    """Read a customer profile. viewer and admin roles are allowed."""
    principal = require_role("viewer", "admin")
    logger.info(
        "tool_allowed",
        extra={"tool": "get_customer", "subject": principal.subject, "role": principal.role},
    )
    return {"id": customer_id, "name": "John Doe", "plan": "Premium"}


@mcp.tool()
def create_customer(name: str, plan: str) -> dict[str, str]:
    """Create a customer. admin role is required."""
    principal = require_role("admin")
    logger.info(
        "tool_allowed",
        extra={"tool": "create_customer", "subject": principal.subject, "role": principal.role},
    )
    return {"id": "C-1001", "name": name, "plan": plan, "status": "Created"}


@mcp.tool()
def update_customer(customer_id: str, plan: str) -> dict[str, str]:
    """Update a customer's subscription plan. admin role is required."""
    principal = require_role("admin")
    logger.info(
        "tool_allowed",
        extra={"tool": "update_customer", "subject": principal.subject, "role": principal.role},
    )
    return {"id": customer_id, "plan": plan, "status": "Updated"}


async def health(_: object) -> JSONResponse:
    """Return a simple health response for example scripts."""
    return JSONResponse({"status": "ok"})


def create_app() -> AuthenticationMiddleware:
    """Create the authenticated remote MCP ASGI application."""
    mcp_app = mcp.streamable_http_app()
    mcp_app.add_route("/health", health, methods=["GET"])
    return AuthenticationMiddleware(mcp_app)


if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8765, log_level="warning")
