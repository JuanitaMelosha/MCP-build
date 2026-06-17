from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("Ticket MCP")


@mcp.tool()
def create_ticket(title: str, priority: str) -> dict[str, str]:
    """Create a support ticket."""
    return {"ticket_id": "T-1001", "status": "Created", "priority": priority, "title": title}


@mcp.tool()
def get_ticket_status(ticket_id: str) -> dict[str, str]:
    """Return the status of a support ticket."""
    return {"ticket_id": ticket_id, "status": "Created"}


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        raise SystemExit(0) from None

