# Benchmark Guide

## Purpose

The benchmark suite measures:

- Initialization latency
- Tool discovery latency
- Tool-call latency
- Raw JSON-RPC implementation
- Official SDK implementation

It does not claim production capacity or compare different business workloads fairly.

## Run

```bash
python benchmarks/benchmark_suite.py --iterations 20
```

Write JSON:

```bash
python benchmarks/benchmark_suite.py \
  --iterations 20 \
  --output benchmark_results/local.json
```

## Metrics

- Mean
- Median
- p95
- Minimum
- Maximum

Initialization includes child-process startup. Discovery and calls use a warm connection.

## Interpretation

Do not optimize only for microbenchmark latency.

Real MCP latency is usually dominated by:

- External API calls
- Database queries
- Authentication
- LLM calls
- Network distance
- Rate limits
- Tool business logic

Useful benchmark questions:

- Is initialization unexpectedly slow?
- Does discovery scale with tool count?
- Does schema construction dominate startup?
- Are retries or network handshakes visible?
- Does p95 remain stable?

## Production Benchmarking

Add:

- Concurrent clients
- Large tool catalogs
- Pagination
- Large resource payloads
- Streaming
- Remote TLS
- Authentication
- Server saturation
- Memory and CPU
- Error rates
- Session churn

