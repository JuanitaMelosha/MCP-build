from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2025-06-18"


class RawMCPClient:
    """Raw newline-delimited JSON-RPC MCP client over stdio."""

    def __init__(self, server_script: Path) -> None:
        self.server_script = server_script
        self.process: subprocess.Popen[str] | None = None
        self.next_id = 1
        self.transcript: list[dict[str, Any]] = []

    def connect(self) -> dict[str, Any]:
        """Start the server and complete the MCP initialization lifecycle."""
        self.process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "raw-mcp-client",
                    "version": "1.0.0",
                },
            },
        )
        self.notify("notifications/initialized")
        return result

    def disconnect(self) -> None:
        """Close stdin and terminate the child server if necessary."""
        if self.process is None:
            return
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=2)
        self.process = None

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for its matching response."""
        request_id = self.next_id
        self.next_id += 1
        message: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params
        self._write(message)
        response = self._read()
        if response.get("id") != request_id:
            raise RuntimeError(
                f"Response id mismatch: expected {request_id}, got {response.get('id')}"
            )
        if "error" in response:
            raise RuntimeError(f"JSON-RPC error: {response['error']}")
        return response["result"]

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a JSON-RPC notification with no id and no response."""
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

    def list_tools(self) -> list[dict[str, Any]]:
        """Discover raw server tools."""
        return self.request("tools/list").get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a raw server tool."""
        return self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )

    def _write(self, message: dict[str, Any]) -> None:
        """Write one newline-delimited JSON-RPC message."""
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Raw MCP client is not connected.")
        self.transcript.append({"direction": "client->server", "message": message})
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _read(self) -> dict[str, Any]:
        """Read one newline-delimited JSON-RPC message."""
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("Raw MCP client is not connected.")
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"Raw MCP server closed unexpectedly. {stderr}")
        message = json.loads(line)
        self.transcript.append({"direction": "server->client", "message": message})
        return message


def main() -> None:
    """Run initialization, discovery, and invocation against the raw server."""
    server = Path(__file__).with_name("raw_server.py")
    client = RawMCPClient(server)
    try:
        initialize_result = client.connect()
        print("Initialize result:")
        print(json.dumps(initialize_result, indent=2))
        print("\nTools:")
        print(json.dumps(client.list_tools(), indent=2))
        print("\nCall echo:")
        print(json.dumps(client.call_tool("echo", {"message": "Protocol mastery"}), indent=2))
        print("\nCall add:")
        print(json.dumps(client.call_tool("add", {"left": 20, "right": 22}), indent=2))
        print("\nRaw transcript:")
        print(json.dumps(client.transcript, indent=2))
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()

