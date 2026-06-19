from __future__ import annotations

import logging

from agents.orchestrator import Orchestrator
from gateway import build_gateway


def configure_logging() -> None:
    """Configure logs for agent delegation and workflow execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("mcp").setLevel(logging.WARNING)


def build_orchestrator() -> Orchestrator:
    """Create the orchestrator and MCP gateway."""
    configure_logging()
    return Orchestrator(build_gateway())

