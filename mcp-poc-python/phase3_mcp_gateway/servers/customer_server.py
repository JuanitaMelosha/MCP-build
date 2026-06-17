from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("Customer MCP")


@mcp.tool()
def get_customer(customer_id: str) -> dict[str, str]:
    """Return a customer profile."""
    return {"id": customer_id, "name": "John Doe", "plan": "Premium"}


@mcp.tool()
def get_customer_plan(customer_id: str) -> dict[str, str]:
    """Return the customer's subscription plan."""
    return {"customer_id": customer_id, "plan": "Premium"}


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        raise SystemExit(0) from None

