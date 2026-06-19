from __future__ import annotations

import logging

from agent.runtime import AgentRuntime
from gateway import build_gateway


def configure_logging() -> None:
    """Configure logs that show agent decisions and tool execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("mcp").setLevel(logging.WARNING)


def build_agent() -> AgentRuntime:
    """Create an agent connected to customer, weather, and ticket MCP servers."""
    configure_logging()
    return AgentRuntime(build_gateway())

