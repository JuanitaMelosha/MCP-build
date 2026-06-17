# Phase 4 MCP Learning Lab: Remote MCP Servers And Authentication

Phase 1 taught a minimal local MCP server and client.

Phase 2 taught tools, resources, and prompts.

Phase 3 taught multiple MCP servers behind a gateway.

Phase 4 teaches remote MCP servers, authentication, authorization, logging, and error handling.

## What You Build

```text
Client Example
  |
  v
MCP Gateway
  |
  v
Remote SecureCustomerMCP Server
  |
  +-- API key authentication
  +-- Bearer token authentication
  +-- Role-based authorization
  +-- Structured logging
  +-- Error handling
```

## Authentication vs Authorization

**Authentication** asks:

```text
Who are you?
```

Examples:

- API key
- Bearer token
- OAuth access token

**Authorization** asks:

```text
What are you allowed to do?
```

Examples:

- A `viewer` can read customers.
- An `admin` can read, create, and update customers.

Authentication happens first. Authorization happens after the server knows who the caller is.

## API Keys

An API key is a shared secret sent with each HTTP request.

This lab uses:

```http
X-API-Key: viewer-api-key-123
```

Demo API keys:

| API Key | Role |
|---|---|
| `viewer-api-key-123` | viewer |
| `admin-api-key-456` | admin |

API keys are simple, but in real systems they must be stored securely, rotated regularly, and never committed to git.

## Bearer Tokens

A bearer token is sent in the `Authorization` header.

This lab uses:

```http
Authorization: Bearer admin-bearer-token-456
```

Demo bearer tokens:

| Bearer Token | Role |
|---|---|
| `viewer-bearer-token-123` | viewer |
| `admin-bearer-token-456` | admin |

Bearer tokens are common for OAuth and vendor-hosted MCP servers.

## OAuth Concepts

OAuth is a standard way to get bearer tokens.

The usual flow is:

1. The user signs in with a vendor.
2. The vendor asks for consent.
3. The vendor redirects back with an authorization code.
4. The client exchanges the code for an access token.
5. The MCP client sends that token as `Authorization: Bearer <token>`.

This phase does not implement a full OAuth browser flow. It prepares the architecture for it by teaching bearer-token authentication and remote MCP headers.

## Role-Based Authorization

This lab defines two roles.

| Role | Allowed Tools |
|---|---|
| viewer | `get_customer` |
| admin | `get_customer`, `create_customer`, `update_customer` |

If a viewer tries to call `create_customer`, the server rejects the tool call.

## Remote MCP Architecture

```mermaid
flowchart LR
    Client[Client Example] --> Gateway[MCP Gateway]
    Gateway -->|Streamable HTTP + Headers| Server[SecureCustomerMCP]
    Server --> Auth[Authentication Middleware]
    Auth --> Tools[Customer Tools]
    Tools --> RBAC[Role Checks]
```

## Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Server
    participant Tool
    Client->>Gateway: call_tool("secure_customer.get_customer")
    Gateway->>Server: HTTP MCP request + credentials
    Server->>Server: authenticate credentials
    Server->>Tool: authorize role
    Tool-->>Server: customer result
    Server-->>Gateway: MCP tool result
    Gateway-->>Client: JSON result
```

## Failure Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Server
    Client->>Gateway: discover_tools()
    Gateway->>Server: HTTP MCP request without credentials
    Server-->>Gateway: HTTP 401
    Gateway-->>Client: clean ConnectionError
```

## Setup

Use Python 3.12 or newer.

```bash
cd /Users/juanitamelosha/Desktop/MCP-build/mcp-poc-python/phase4_remote_auth
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If you already use the root project virtual environment, you can run the examples with:

```bash
../.venv/bin/python examples/discover_remote_tools.py
```

## Run Examples

Each example starts the remote MCP server on `127.0.0.1:8765`, talks to it through the gateway, then stops it.

```bash
python examples/authenticate_api_key.py
python examples/authenticate_bearer.py
python examples/discover_remote_tools.py
python examples/call_remote_tool.py
python examples/authorization_failure.py
python examples/missing_credentials.py
python examples/invalid_credentials.py
```

If your environment blocks local ports, allow the command to bind to `127.0.0.1:8765`.

## Expected Output

### API Key Authentication

```text
API key authentication succeeded.
Discovered tools:
- secure_customer.get_customer
- secure_customer.create_customer
- secure_customer.update_customer
```

### Bearer Token Authentication

```text
Bearer token authentication succeeded.
{'id': 'C-1001', 'name': 'Joshua', 'plan': 'Premium', 'status': 'Created'}
```

### Tool Discovery

```text
Remote tools:
- secure_customer.get_customer
- secure_customer.create_customer
- secure_customer.update_customer
```

### Tool Execution

```json
{
  "id": "123",
  "name": "John Doe",
  "plan": "Premium"
}
```

### Forbidden Operation

```text
Authorization failed as expected.
Error executing tool create_customer: Role 'viewer' cannot perform this operation. Allowed roles: admin.
```

### Missing Or Invalid Credentials

```text
Remote MCP request failed with HTTP 401: Missing or invalid credentials.
```

## Every File Explained

### `auth.py`

Authentication and authorization support.

It defines demo credentials, verifies HTTP headers, stores the authenticated principal, and checks roles.

### `secure_customer_server.py`

Remote MCP server.

It exposes `SecureCustomerMCP` over Streamable HTTP and protects it with authentication middleware.

### `gateway.py`

MCP Gateway that supports both local stdio servers and remote HTTP servers.

The Phase 4 examples use the remote HTTP path.

### `examples/example_helpers.py`

Starts and stops the remote MCP server for examples.

This keeps the examples easy to run.

### `examples/authenticate_api_key.py`

Connects to the remote MCP server with an API key and discovers tools.

### `examples/authenticate_bearer.py`

Connects with a bearer token and calls an admin-only tool.

### `examples/discover_remote_tools.py`

Discovers tools from the remote MCP server through the gateway.

### `examples/call_remote_tool.py`

Calls `secure_customer.get_customer` through the gateway.

### `examples/authorization_failure.py`

Shows an authenticated viewer being denied access to an admin-only tool.

### `examples/missing_credentials.py`

Shows a request with no credentials being rejected.

### `examples/invalid_credentials.py`

Shows a request with a wrong API key being rejected.

### `requirements.txt`

Installs the official MCP Python SDK and Uvicorn.

## Every Class Explained

### `Principal`

Represents the authenticated caller.

Fields:

- `subject`: caller id
- `role`: `viewer` or `admin`
- `auth_method`: `api_key` or `bearer`

### `AuthenticationError`

Raised when credentials are missing or invalid.

### `AuthorizationError`

Raised when credentials are valid but the role is not allowed.

### `AuthenticationMiddleware`

ASGI middleware that protects remote MCP HTTP requests.

It reads headers, authenticates the caller, logs the result, and stores the caller in a context variable.

### `Transport`

Enum describing gateway transport types:

- `LOCAL_STDIO`
- `REMOTE_HTTP`

### `ServerConfig`

Stores one MCP server configuration.

It can represent a local server or a remote server.

### `NamespacedTool`

Represents a discovered gateway tool such as:

```text
secure_customer.get_customer
```

### `MCPGateway`

Gateway that registers servers, discovers tools, and routes namespaced tool calls.

It supports both local stdio and remote HTTP MCP servers.

## Every Function Explained

### `authenticate(headers)`

Checks `X-API-Key` first, then `Authorization: Bearer`.

Returns a `Principal` when credentials are valid.

Raises `AuthenticationError` when credentials are missing or invalid.

### `require_role(*allowed_roles)`

Checks the current caller's role.

Raises `AuthorizationError` when the caller is authenticated but not allowed.

### `AuthenticationMiddleware.__call__`

Runs on every HTTP request.

It authenticates credentials before the MCP server handles the request.

### `get_customer(customer_id)`

Remote MCP tool.

Allowed roles: `viewer`, `admin`.

### `create_customer(name, plan)`

Remote MCP tool.

Allowed roles: `admin`.

### `update_customer(customer_id, plan)`

Remote MCP tool.

Allowed roles: `admin`.

### `health(request)`

Simple health endpoint used by examples to wait until the server is ready.

### `create_app()`

Builds the authenticated ASGI application.

### `MCPGateway.register_server(config)`

Registers a local or remote MCP server.

### `MCPGateway.remove_server(namespace)`

Removes a server.

### `MCPGateway.list_servers()`

Lists registered namespaces.

### `MCPGateway.discover_tools()`

Connects to registered servers and returns namespaced tools.

### `MCPGateway.call_tool(namespaced_tool_name, arguments)`

Routes a tool call to the correct MCP server.

### `api_key_headers(api_key)`

Builds headers for API key authentication.

### `bearer_headers(token)`

Builds headers for bearer token authentication.

### `build_remote_gateway(headers, url)`

Creates a gateway with `SecureCustomerMCP` registered as a remote server.

### `running_remote_server()`

Example helper that starts the remote server process and stops it after the example.

### `wait_for_health()`

Waits until the remote server is ready.

## Structured Logging

The server logs authentication and authorization events using Python's `logging` module.

Examples:

- `authentication_succeeded`
- `authentication_failed`
- `tool_allowed`

Real systems usually send these logs to a central logging system such as CloudWatch, Datadog, Splunk, OpenTelemetry, or an internal SIEM.

## How This Prepares You For OAuth

OAuth usually produces bearer tokens.

Once you understand this:

```http
Authorization: Bearer <token>
```

you are ready to replace demo tokens with real OAuth access tokens.

The server-side idea remains the same:

1. Validate token.
2. Identify caller.
3. Check scopes or roles.
4. Allow or deny the MCP operation.

## How This Prepares You For GitHub MCP

GitHub MCP uses remote server patterns where the client sends credentials to a vendor-hosted MCP endpoint.

The gateway pattern lets you register GitHub tools under a namespace like:

```text
github.list_issues
github.create_pull_request
```

## How This Prepares You For Atlassian Rovo MCP

Atlassian/Rovo-style MCP uses remote enterprise context and tools.

The same design applies:

- Remote endpoint
- Bearer token or OAuth flow
- Tool discovery
- Authorization by user, workspace, site, or scope
- Gateway namespace such as `atlassian.search_confluence` or `jira.create_issue`

## How This Prepares You For Enterprise MCP Ecosystems

Enterprise MCP ecosystems need:

- Central gateway
- Secure authentication
- Fine-grained authorization
- Audit logging
- Clear error handling
- Separation between local and remote systems
- Namespaced tool routing

Phase 4 gives you the foundation for all of that.

