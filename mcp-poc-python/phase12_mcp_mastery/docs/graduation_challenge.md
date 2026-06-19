# Graduation Challenge

## Assignment

Build an Incident Response MCP server without copying an earlier server.

Required capabilities:

Tools:

- `declare_incident`
- `add_incident_update`
- `resolve_incident`
- `get_incident`

Resource:

- `incident://runbook`

Prompt:

- `post_incident_review`

Requirements:

- Typed inputs and outputs
- Helpful descriptions
- Correct errors for missing incidents
- stdio support
- Streamable HTTP support
- Inspector validation
- At least one write workflow
- Security notes

## Solution

The completed reference solution is:

```text
graduation_challenge/server.py
```

Verify:

```bash
python graduation_challenge/verify.py
```

## Extension Tasks

1. Add incident severity validation.
2. Add idempotency keys.
3. Add an incident timeline resource template.
4. Add role-based approval before resolving SEV-1.
5. Persist incidents.
6. Add metrics and audit logs.
7. Benchmark 100 incident reads.
8. Deploy over Streamable HTTP with OAuth.

## Graduation Rubric

Protocol correctness: 25%

- Lifecycle
- Capabilities
- Errors
- Content shapes

Server design: 25%

- Schemas
- Domain modeling
- Tool/resource/prompt choices

Security and operations: 25%

- Auth design
- Authorization
- Validation
- Logging and reliability

Explanation and debugging: 25%

- Can explain raw messages
- Can inspect failures
- Can justify transport
- Can describe production changes

