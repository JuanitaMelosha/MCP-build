from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connect_to_phase2_server() -> AsyncIterator[ClientSession]:
    """Start the Phase 2 server and yield an initialized MCP client session."""
    server_path = Path(__file__).with_name("server.py")
    server = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def tool_result_to_json(result: Any) -> dict[str, Any]:
    """Convert the first text block in a tool result into a Python dictionary."""
    text = result.content[0].text
    return json.loads(text)


def resource_result_to_text(result: Any) -> str:
    """Convert the first resource content block into text."""
    return result.contents[0].text

