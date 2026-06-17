from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP("Weather MCP")


@mcp.tool()
def get_weather(city: str) -> dict[str, str | int]:
    """Return the current weather for a city."""
    return {"city": city, "temperature_celsius": 32, "condition": "Sunny"}


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> dict[str, object]:
    """Return a simple multi-day forecast."""
    return {
        "city": city,
        "days": days,
        "forecast": [
            {"day": 1, "temperature_celsius": 32, "condition": "Sunny"},
            {"day": 2, "temperature_celsius": 31, "condition": "Cloudy"},
            {"day": 3, "temperature_celsius": 30, "condition": "Light rain"},
        ][:days],
    }


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        raise SystemExit(0) from None

