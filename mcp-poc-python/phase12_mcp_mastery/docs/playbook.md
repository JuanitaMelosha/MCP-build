# MCP Engineering Playbook

## Discovery

1. Initialize.
2. Record negotiated protocol version.
3. Record server capabilities.
4. Send `notifications/initialized`.
5. Discover only negotiated features.
6. Handle pagination.
7. Cache catalogs with invalidation.

## Server Design

- Prefer narrow domain ownership.
- Use stable, action-oriented tool names.
- Write precise descriptions.
- Use strict input schemas.
- Return structured content.
- Keep read context as resources.
- Keep reusable interaction templates as prompts.
- Separate business logic from MCP registration.

## Client Design

- Encapsulate transport lifecycle.
- Set timeouts.
- Normalize errors.
- Expose discovery metadata.
- Validate schemas.
- Support cancellation.
- Close sessions gracefully.

## Gateway Design

- Namespace tools.
- Track server health.
- Isolate server failures.
- Apply policy before execution.
- Preserve identity and correlation.
- Avoid silently merging conflicting tools.

## Security

- Authenticate remote connections.
- Authorize every operation.
- Use least privilege.
- Protect tokens.
- Validate Origin.
- Require approval for high-risk tools.
- Treat retrieved content as untrusted.
- Audit decisions and calls.

## Operations

- Structured logs
- Metrics
- Traces
- Health checks
- Timeouts
- Retries
- Circuit breakers
- Dead letters
- Idempotency
- Capacity limits

## Review Checklist

Protocol:

- Correct initialization order?
- Version negotiation handled?
- Capabilities respected?
- Errors use correct layer?

Tools:

- Schema valid?
- Side effects documented?
- Human confirmation defined?
- Idempotency strategy?

Resources:

- URI stable?
- Size bounded?
- Authorization enforced?
- Subscription behavior defined?

Transports:

- Correct current transport?
- Legacy fallback intentional?
- Shutdown graceful?
- HTTP headers and sessions correct?

## Graduation Questions

You should be able to answer:

1. Why is `notifications/initialized` required?
2. What is the difference between a JSON-RPC error and `isError: true`?
3. Why must stdio logs use stderr?
4. How does Streamable HTTP session management work?
5. Why is legacy SSE different from SSE used inside Streamable HTTP?
6. When should a capability be omitted?
7. How should gateways handle duplicate tool names?
8. Where should OAuth refresh logic live?
9. Why must tools be governed separately from resources?
10. What would you replace before production?

