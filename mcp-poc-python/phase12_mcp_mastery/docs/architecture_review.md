# Architecture Review

## Learning Journey

```mermaid
flowchart TD
    P1[1: Protocol Basics] --> P2[2: Tools Resources Prompts]
    P2 --> P3[3: Multi-Server Gateway]
    P3 --> P4[4: Remote Auth]
    P4 --> P5[5: GitHub OAuth]
    P5 --> P6[6: Atlassian Integration]
    P6 --> P7[7: Agent Runtime]
    P7 --> P8[8: Multi-Agent]
    P8 --> P9[9: Events]
    P9 --> P10[10: Governance]
    P10 --> P11[11: Memory]
    P11 --> P12[12: Mastery]
```

## Reference Architecture

```mermaid
flowchart TD
    UI[User / Event / Scheduler] --> Host[Agent Host]
    Host --> Governance[Governance and Approval]
    Host --> Memory[Memory and Context]
    Host --> Gateway[MCP Gateway]
    Gateway --> Local[Local stdio MCP]
    Gateway --> Remote[Remote HTTP MCP]
    Gateway --> Vendor[Vendor MCP Adapters]
    Local --> Systems[Business Systems]
    Remote --> Systems
    Vendor --> Systems
    Host --> Observability[Logs Metrics Traces Audit]
```

## Strong Patterns

- Separate host, client, server, and gateway responsibilities.
- Discover capabilities rather than hard-code availability.
- Namespace multi-server tools.
- Keep vendor OAuth inside adapters.
- Place governance before execution.
- Treat memory retrieval as an authorized context operation.
- Use events for autonomous triggers.
- Preserve correlation and audit data.

## Refactoring Before A Real Project

The learning phases intentionally duplicate gateway and connection code. A real project should consolidate:

```text
src/
  mcp_platform/
    clients/
    gateway/
    providers/
    governance/
    memory/
    agents/
    events/
```

Recommended boundaries:

- `TransportFactory`: stdio, HTTP, legacy SSE.
- `MCPConnection`: lifecycle and retries.
- `ProviderAdapter`: vendor auth and endpoint behavior.
- `ToolCatalog`: discovery, schemas, namespacing, caching.
- `GovernedExecutor`: authorization and approvals.
- `AgentRuntime`: planning and execution.
- `MemoryService`: retrieval and persistence.
- `EventRuntime`: triggers, retries, replay.

## Scalability

Local prototype:

- In-process queues
- JSONL data
- One Python process
- Child-process MCP servers

Production:

- Durable event broker
- Relational/vector/graph stores
- Distributed workers
- Central secret manager
- Policy engine
- OpenTelemetry
- Load-balanced Streamable HTTP servers

## Reliability

Add:

- Timeouts for every request
- Bounded retries
- Circuit breakers
- Bulkheads by server
- Idempotency keys
- Health checks
- Session reinitialization
- Dead-letter queues
- Graceful shutdown

## Readiness Decision

You are ready for a real project when you can:

- Draw the lifecycle from memory.
- Explain capability negotiation.
- Read raw JSON-RPC traffic.
- Identify transport-specific failures.
- Build and inspect a new server.
- Define auth and authorization boundaries.
- Choose gateway ownership.
- Set tool-risk and approval policy.
- Define observability and reliability requirements.

