from __future__ import annotations

import argparse
import asyncio
import json
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from rich.console import Console
from rich.json import JSON
from rich.table import Table


class Transport(StrEnum):
    """Inspector transport choices."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


@dataclass
class InspectorConfig:
    """Connection settings for the MCP Inspector."""

    transport: Transport
    command: str | None = None
    args: list[str] = field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Timing:
    """One measured inspector operation."""

    operation: str
    duration_ms: float


class MCPInspector:
    """Inspect an MCP server's lifecycle, capabilities, and schemas."""

    def __init__(self, config: InspectorConfig) -> None:
        self.config = config
        self.timings: list[Timing] = []
        self._stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.initialize_result: Any = None

    async def __aenter__(self) -> "MCPInspector":
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        """Open the selected transport and complete initialization."""
        start = time.perf_counter()
        if self.config.transport == Transport.STDIO:
            if not self.config.command:
                raise ValueError("stdio inspection requires --command")
            streams = await self._stack.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=self.config.command,
                        args=self.config.args,
                    )
                )
            )
            read_stream, write_stream = streams
        elif self.config.transport == Transport.HTTP:
            if not self.config.url:
                raise ValueError("HTTP inspection requires --url")
            streams = await self._stack.enter_async_context(
                streamablehttp_client(
                    self.config.url,
                    headers=self.config.headers,
                )
            )
            read_stream, write_stream = streams[0], streams[1]
        else:
            if not self.config.url:
                raise ValueError("SSE inspection requires --url")
            read_stream, write_stream = await self._stack.enter_async_context(
                sse_client(self.config.url, headers=self.config.headers)
            )

        self.session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        self.initialize_result = await self.session.initialize()
        self._record("initialize", start)

    async def disconnect(self) -> None:
        """Close the MCP session and transport."""
        await self._stack.aclose()
        self._stack = AsyncExitStack()
        self.session = None

    async def inspect(self) -> dict[str, Any]:
        """Discover server features and validate tool input schemas."""
        session = self._require_session()
        tools = await self._timed("tools/list", session.list_tools)
        resources = await self._safe_timed("resources/list", session.list_resources)
        prompts = await self._safe_timed("prompts/list", session.list_prompts)

        schema_issues: list[dict[str, str]] = []
        for tool in tools.tools:
            try:
                Draft202012Validator.check_schema(tool.inputSchema)
            except Exception as exc:
                schema_issues.append({"tool": tool.name, "error": str(exc)})

        return {
            "server_info": self._serialize(self.initialize_result.serverInfo),
            "protocol_version": self.initialize_result.protocolVersion,
            "capabilities": self._serialize(self.initialize_result.capabilities),
            "instructions": self.initialize_result.instructions,
            "tools": [self._serialize(tool) for tool in tools.tools],
            "resources": [
                self._serialize(resource)
                for resource in getattr(resources, "resources", [])
            ],
            "prompts": [
                self._serialize(prompt)
                for prompt in getattr(prompts, "prompts", [])
            ],
            "schema_issues": schema_issues,
            "timings": [timing.__dict__ for timing in self.timings],
        }

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool while measuring latency."""
        return await self._timed(
            f"tools/call:{name}",
            self._require_session().call_tool,
            name,
            arguments,
        )

    async def read_resource(self, uri: str) -> Any:
        """Read a resource while measuring latency."""
        return await self._timed(
            f"resources/read:{uri}",
            self._require_session().read_resource,
            uri,
        )

    async def _timed(self, operation: str, function: Any, *args: Any) -> Any:
        """Measure one async SDK operation."""
        start = time.perf_counter()
        result = await function(*args)
        self._record(operation, start)
        return result

    async def _safe_timed(self, operation: str, function: Any) -> Any:
        """Return an empty result when a capability is unsupported."""
        try:
            return await self._timed(operation, function)
        except Exception as exc:
            self.timings.append(Timing(f"{operation}:unsupported:{exc}", 0))
            return object()

    def _record(self, operation: str, start: float) -> None:
        """Record elapsed milliseconds."""
        self.timings.append(
            Timing(operation, (time.perf_counter() - start) * 1000)
        )

    def _require_session(self) -> ClientSession:
        """Return the initialized session."""
        if self.session is None:
            raise RuntimeError("Inspector is not connected.")
        return self.session

    def _serialize(self, value: Any) -> Any:
        """Serialize Pydantic SDK models."""
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json", exclude_none=True)
        return value


def render_report(report: dict[str, Any]) -> None:
    """Render an inspector report with Rich."""
    console = Console()
    console.print("[bold]MCP Server[/bold]")
    console.print(JSON.from_data(report["server_info"]))
    console.print(f"Protocol: [cyan]{report['protocol_version']}[/cyan]")

    table = Table(title="Capabilities")
    table.add_column("Feature")
    table.add_column("Count")
    table.add_row("Tools", str(len(report["tools"])))
    table.add_row("Resources", str(len(report["resources"])))
    table.add_row("Prompts", str(len(report["prompts"])))
    table.add_row("Schema issues", str(len(report["schema_issues"])))
    console.print(table)

    tools = Table(title="Tools")
    tools.add_column("Name")
    tools.add_column("Description")
    tools.add_column("Required")
    for tool in report["tools"]:
        required = ", ".join(tool["inputSchema"].get("required", []))
        tools.add_row(tool["name"], tool.get("description", ""), required)
    console.print(tools)

    timings = Table(title="Timings")
    timings.add_column("Operation")
    timings.add_column("Milliseconds", justify="right")
    for timing in report["timings"]:
        timings.add_row(timing["operation"], f"{timing['duration_ms']:.3f}")
    console.print(timings)


def parse_headers(values: list[str]) -> dict[str, str]:
    """Parse repeated Key=Value headers."""
    headers: dict[str, str] = {}
    for value in values:
        key, separator, header_value = value.partition("=")
        if not separator:
            raise ValueError(f"Header must use Key=Value format: {value}")
        headers[key] = header_value
    return headers


def build_parser() -> argparse.ArgumentParser:
    """Build the inspector CLI parser."""
    parser = argparse.ArgumentParser(description="Inspect an MCP server")
    parser.add_argument("--transport", choices=list(Transport), default="stdio")
    parser.add_argument("--command")
    parser.add_argument("--arg", action="append", default=[])
    parser.add_argument("--url")
    parser.add_argument("--header", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--call-tool")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--read-resource")
    return parser


async def main() -> None:
    """Connect, inspect, and optionally invoke one capability."""
    args = build_parser().parse_args()
    config = InspectorConfig(
        transport=Transport(args.transport),
        command=args.command,
        args=args.arg,
        url=args.url,
        headers=parse_headers(args.header),
    )
    async with MCPInspector(config) as inspector:
        report = await inspector.inspect()
        if args.call_tool:
            result = await inspector.call_tool(
                args.call_tool,
                json.loads(args.arguments),
            )
            report["tool_result"] = inspector._serialize(result)
        if args.read_resource:
            result = await inspector.read_resource(args.read_resource)
            report["resource_result"] = inspector._serialize(result)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        render_report(report)
        if "tool_result" in report:
            Console().print(JSON.from_data(report["tool_result"]))
        if "resource_result" in report:
            Console().print(JSON.from_data(report["resource_result"]))


if __name__ == "__main__":
    asyncio.run(main())

