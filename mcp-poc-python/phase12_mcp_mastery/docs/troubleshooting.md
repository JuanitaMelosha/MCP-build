# MCP Troubleshooting Guide

## First Five Checks

1. Confirm Python 3.12+ and the expected virtual environment.
2. Confirm the server starts independently.
3. Confirm initialization succeeds before other requests.
4. Confirm the negotiated capabilities include the requested feature.
5. Inspect stderr, HTTP status, and raw JSON-RPC ids.

## stdio Problems

### Client Hangs

Check:

- Server flushes stdout.
- Each JSON message ends with a newline.
- No embedded newline exists inside the framed message.
- Client and server agree on request ids.
- Server is not waiting for `notifications/initialized`.

### JSON Parse Failure

Check for debug prints on stdout.

Correct:

```python
print("debug", file=sys.stderr)
```

Incorrect:

```python
print("debug")
```

### Server Exits Immediately

- Inspect captured stderr.
- Verify command and working directory.
- Verify imports in the child environment.
- Use absolute script paths.

## Lifecycle Problems

### Server Is Not Initialized

Correct order:

```text
initialize request
initialize response
notifications/initialized
tools/list or other operation
```

### Protocol Version Mismatch

- Compare requested and returned versions.
- Disconnect when the returned version is unsupported.
- For HTTP, send `MCP-Protocol-Version` after negotiation.

## Discovery Problems

### Tools Missing

- Check server declared tools capability.
- Check registration decorators ran.
- Check namespace collisions in gateways.
- Handle pagination and list-changed notifications.

### Invalid Tool Schema

Run the Inspector. Validate JSON Schema independently. Check:

- Root schema is an object.
- Required fields exist in properties.
- Types match handler expectations.
- Output schema matches structured content when provided.

## Tool Call Problems

- Verify exact tool name.
- Validate arguments.
- Distinguish JSON-RPC errors from tool-level `isError`.
- Inspect structured content and text content.
- Confirm external-system permissions.

## HTTP Problems

### 401

Missing, invalid, expired, or wrong-audience credentials.

### 403

Authenticated but missing role, scope, or object permission.

### 404

Wrong endpoint, expired MCP session, or hidden object.

### 400

Protocol header, session header, request shape, or business validation problem.

### DNS Rebinding / Origin Rejection

Use an allowed Origin. Do not disable Origin validation in production.

## SSE Compatibility Problems

- Confirm whether the URL is Streamable HTTP or legacy SSE.
- Try Streamable HTTP POST initialization first.
- Use legacy SSE fallback only for expected 4xx compatibility responses.
- Confirm the old endpoint event provides the message endpoint.

## Inspector Commands

Inspect stdio:

```bash
python inspector/mcp_inspector.py \
  --transport stdio \
  --command python \
  --arg enterprise_pm/server.py \
  --arg stdio
```

Inspect HTTP:

```bash
python inspector/mcp_inspector.py \
  --transport http \
  --url http://127.0.0.1:8000/mcp
```

Call a tool:

```bash
python inspector/mcp_inspector.py \
  --transport stdio \
  --command python \
  --arg enterprise_pm/server.py \
  --arg stdio \
  --call-tool get_project \
  --arguments '{"project_id":"P-100"}'
```

