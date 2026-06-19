from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

PROTOCOL_VERSION = "2025-06-18"


@dataclass(frozen=True)
class RawTool:
    """Tool definition used by the raw JSON-RPC server."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class RawMCPServer:
    """Minimal MCP stdio server implemented directly with JSON-RPC 2.0."""

    def __init__(self) -> None:
        self.initialized = False
        self.tools = {
            "echo": RawTool(
                name="echo",
                description="Echo a message through a raw MCP implementation.",
                input_schema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
                handler=lambda arguments: {"message": arguments["message"]},
            ),
            "add": RawTool(
                name="add",
                description="Add two numbers.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "left": {"type": "number"},
                        "right": {"type": "number"},
                    },
                    "required": ["left", "right"],
                },
                handler=lambda arguments: {
                    "result": arguments["left"] + arguments["right"]
                },
            ),
        }

    def run(self) -> None:
        """Read newline-delimited JSON-RPC messages until stdin closes."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
                response = self.handle(message)
            except json.JSONDecodeError:
                response = self.error(None, -32700, "Parse error")
            except Exception as exc:
                response = self.error(None, -32603, "Internal error", {"detail": str(exc)})

            if response is not None:
                self.write(response)

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Dispatch one request or notification."""
        if message.get("jsonrpc") != "2.0":
            return self.error(message.get("id"), -32600, "Invalid Request")

        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            return self.initialize(request_id, params)
        if method == "notifications/initialized":
            self.initialized = True
            return None
        if method == "ping":
            return self.success(request_id, {})

        if not self.initialized:
            return self.error(request_id, -32002, "Server is not initialized")

        if method == "tools/list":
            return self.list_tools(request_id)
        if method == "tools/call":
            return self.call_tool(request_id, params)
        return self.error(request_id, -32601, f"Method not found: {method}")

    def initialize(
        self,
        request_id: int | str | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Negotiate protocol version and server capabilities."""
        requested = params.get("protocolVersion")
        if requested != PROTOCOL_VERSION:
            return self.error(
                request_id,
                -32602,
                "Unsupported protocol version",
                {"supported": [PROTOCOL_VERSION], "requested": requested},
            )
        return self.success(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "raw-mcp-server",
                    "version": "1.0.0",
                },
                "instructions": "Raw learning server exposing echo and add.",
            },
        )

    def list_tools(self, request_id: int | str | None) -> dict[str, Any]:
        """Return tool metadata using the MCP tools/list result shape."""
        return self.success(
            request_id,
            {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema,
                    }
                    for tool in self.tools.values()
                ]
            },
        )

    def call_tool(
        self,
        request_id: int | str | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate and execute a raw MCP tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = self.tools.get(tool_name)
        if tool is None:
            return self.error(request_id, -32602, f"Unknown tool: {tool_name}")

        missing = [
            name
            for name in tool.input_schema.get("required", [])
            if name not in arguments
        ]
        if missing:
            return self.error(
                request_id,
                -32602,
                "Missing required tool arguments",
                {"missing": missing},
            )

        try:
            result = tool.handler(arguments)
        except Exception as exc:
            return self.success(
                request_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )

        return self.success(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "structuredContent": result,
                "isError": False,
            },
        )

    def success(
        self,
        request_id: int | str | None,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a JSON-RPC success response."""
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def error(
        self,
        request_id: int | str | None,
        code: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a JSON-RPC error response."""
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    def write(self, message: dict[str, Any]) -> None:
        """Write exactly one compact JSON-RPC message to stdout."""
        sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    RawMCPServer().run()

