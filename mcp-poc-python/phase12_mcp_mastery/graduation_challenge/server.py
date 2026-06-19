from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP(
    "Incident Response MCP",
    instructions="Graduation challenge solution for incident-response workflows.",
    stateless_http=True,
    json_response=True,
)

INCIDENTS: dict[str, dict[str, Any]] = {}


@mcp.tool()
def declare_incident(title: str, severity: str, service: str) -> dict[str, Any]:
    """Declare a new operational incident."""
    incident_id = f"INC-{len(INCIDENTS) + 1:04d}"
    incident = {
        "id": incident_id,
        "title": title,
        "severity": severity,
        "service": service,
        "status": "Open",
        "timeline": ["Incident declared"],
    }
    INCIDENTS[incident_id] = incident
    return incident


@mcp.tool()
def add_incident_update(incident_id: str, update: str) -> dict[str, Any]:
    """Add an update to an incident timeline."""
    incident = require_incident(incident_id)
    incident["timeline"].append(update)
    return incident


@mcp.tool()
def resolve_incident(incident_id: str, resolution: str) -> dict[str, Any]:
    """Resolve an incident."""
    incident = require_incident(incident_id)
    incident["status"] = "Resolved"
    incident["resolution"] = resolution
    incident["timeline"].append(f"Resolved: {resolution}")
    return incident


@mcp.tool()
def get_incident(incident_id: str) -> dict[str, Any]:
    """Read an incident."""
    return require_incident(incident_id)


@mcp.resource("incident://runbook", name="incident_runbook")
def incident_runbook() -> str:
    """Read the incident-response runbook."""
    return json.dumps(
        {
            "steps": [
                "Confirm impact and severity.",
                "Assign incident commander.",
                "Stabilize the service.",
                "Communicate status regularly.",
                "Resolve, review, and record follow-up work.",
            ]
        },
        indent=2,
    )


@mcp.prompt(name="post_incident_review")
def post_incident_review(incident_id: str) -> str:
    """Create a post-incident review prompt."""
    return (
        f"Create a blameless review for {incident_id}. Include impact, timeline, "
        "root cause, contributing factors, remediation, owners, and due dates."
    )


def require_incident(incident_id: str) -> dict[str, Any]:
    """Return an incident or raise a tool error."""
    if incident_id not in INCIDENTS:
        raise ValueError(f"Unknown incident: {incident_id}")
    return INCIDENTS[incident_id]


def main() -> None:
    """Run the challenge server over a selected transport."""
    requested = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    transport = {
        "stdio": "stdio",
        "http": "streamable-http",
        "streamable-http": "streamable-http",
        "sse": "sse",
    }.get(requested)
    if transport is None:
        raise SystemExit("Expected stdio, http, streamable-http, or sse")
    mcp.run(transport=transport)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(0) from None

