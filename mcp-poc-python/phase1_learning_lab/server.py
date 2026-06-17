from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Phase 1 MCP Learning Lab")


@mcp.tool()
def hello_world(name: str) -> dict[str, str]:
    """Return a friendly greeting for the provided name."""
    return {"message": f"Hello {name}"}


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        raise SystemExit(0) from None
