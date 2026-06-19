from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inspector.mcp_inspector import InspectorConfig, MCPInspector, Transport
from raw.raw_client import RawMCPClient


@dataclass(frozen=True)
class BenchmarkResult:
    """Summary statistics for one benchmark."""

    name: str
    iterations: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    minimum_ms: float
    maximum_ms: float
    notes: str


def summarize(name: str, samples: list[float], notes: str) -> BenchmarkResult:
    """Calculate basic latency statistics."""
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
    return BenchmarkResult(
        name=name,
        iterations=len(samples),
        mean_ms=statistics.fmean(samples),
        median_ms=statistics.median(samples),
        p95_ms=ordered[p95_index],
        minimum_ms=ordered[0],
        maximum_ms=ordered[-1],
        notes=notes,
    )


def benchmark_raw(iterations: int) -> list[BenchmarkResult]:
    """Benchmark raw stdio initialization, discovery, and tool calls."""
    server = ROOT / "raw" / "raw_server.py"
    initialize_samples: list[float] = []
    discovery_samples: list[float] = []
    call_samples: list[float] = []

    for _ in range(iterations):
        client = RawMCPClient(server)
        start = time.perf_counter()
        client.connect()
        initialize_samples.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        client.list_tools()
        discovery_samples.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        client.call_tool("add", {"left": 20, "right": 22})
        call_samples.append((time.perf_counter() - start) * 1000)
        client.disconnect()

    return [
        summarize("raw_stdio_initialize", initialize_samples, "Includes subprocess startup."),
        summarize("raw_stdio_tools_list", discovery_samples, "Warm connection."),
        summarize("raw_stdio_tool_call", call_samples, "Warm connection; add tool."),
    ]


async def benchmark_sdk(iterations: int) -> list[BenchmarkResult]:
    """Benchmark SDK stdio initialization, discovery, and calls."""
    server = ROOT / "enterprise_pm" / "server.py"
    initialize_samples: list[float] = []
    discovery_samples: list[float] = []
    call_samples: list[float] = []

    for _ in range(iterations):
        inspector = MCPInspector(
            InspectorConfig(
                transport=Transport.STDIO,
                command=sys.executable,
                args=[str(server), "stdio"],
            )
        )
        start = time.perf_counter()
        await inspector.connect()
        initialize_samples.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        await inspector.session.list_tools()  # type: ignore[union-attr]
        discovery_samples.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        await inspector.session.call_tool("list_projects", {})  # type: ignore[union-attr]
        call_samples.append((time.perf_counter() - start) * 1000)
        await inspector.disconnect()

    return [
        summarize("sdk_stdio_initialize", initialize_samples, "Includes subprocess startup."),
        summarize("sdk_stdio_tools_list", discovery_samples, "Warm connection."),
        summarize("sdk_stdio_tool_call", call_samples, "Warm connection; list_projects."),
    ]


async def main() -> None:
    """Run raw and SDK benchmark groups and write JSON when requested."""
    parser = argparse.ArgumentParser(description="Phase 12 MCP benchmark suite")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")

    results = benchmark_raw(args.iterations)
    results.extend(await benchmark_sdk(args.iterations))
    serialized = [asdict(result) for result in results]
    print(json.dumps(serialized, indent=2))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(serialized, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

