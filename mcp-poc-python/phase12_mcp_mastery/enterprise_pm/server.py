from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP(
    "Enterprise Project Management MCP",
    instructions=(
        "Project-management capabilities for projects, sprints, work items, risks, "
        "status reports, resources, and prompts."
    ),
    stateless_http=True,
    json_response=True,
)


class WorkItem(BaseModel):
    """Enterprise project work item."""

    id: str
    project_id: str
    title: str
    status: str
    priority: str
    owner: str | None = None
    estimate_points: int = Field(default=1, ge=1)


PROJECTS: dict[str, dict[str, Any]] = {
    "P-100": {
        "id": "P-100",
        "name": "MCP Enterprise Platform",
        "status": "Active",
        "owner": "Platform Team",
        "objective": "Deliver governed MCP agents for enterprise workflows.",
    }
}

SPRINTS: dict[str, dict[str, Any]] = {
    "S-24": {
        "id": "S-24",
        "project_id": "P-100",
        "name": "Sprint 24",
        "status": "Active",
        "goal": "Complete protocol inspector and governance rollout.",
    }
}

WORK_ITEMS: dict[str, WorkItem] = {
    "WI-1": WorkItem(
        id="WI-1",
        project_id="P-100",
        title="Build MCP Inspector",
        status="In Progress",
        priority="High",
        owner="Joshua",
        estimate_points=5,
    ),
    "WI-2": WorkItem(
        id="WI-2",
        project_id="P-100",
        title="Complete security review",
        status="To Do",
        priority="Critical",
        owner="Security Team",
        estimate_points=3,
    ),
}

RISKS: dict[str, dict[str, Any]] = {
    "R-1": {
        "id": "R-1",
        "project_id": "P-100",
        "title": "Over-permissive remote MCP credentials",
        "severity": "High",
        "status": "Open",
        "mitigation": "Use scoped OAuth tokens and approval controls.",
    }
}


@mcp.tool()
def list_projects() -> list[dict[str, Any]]:
    """List enterprise projects."""
    return list(PROJECTS.values())


@mcp.tool()
def get_project(project_id: str) -> dict[str, Any]:
    """Read one project."""
    if project_id not in PROJECTS:
        raise ValueError(f"Unknown project: {project_id}")
    return PROJECTS[project_id]


@mcp.tool()
def create_work_item(
    project_id: str,
    title: str,
    priority: str,
    owner: str | None = None,
    estimate_points: int = 1,
) -> WorkItem:
    """Create a project work item."""
    if project_id not in PROJECTS:
        raise ValueError(f"Unknown project: {project_id}")
    work_item_id = f"WI-{len(WORK_ITEMS) + 1}"
    item = WorkItem(
        id=work_item_id,
        project_id=project_id,
        title=title,
        status="To Do",
        priority=priority,
        owner=owner,
        estimate_points=estimate_points,
    )
    WORK_ITEMS[work_item_id] = item
    return item


@mcp.tool()
def update_work_item_status(work_item_id: str, status: str) -> WorkItem:
    """Update a work item's status."""
    if work_item_id not in WORK_ITEMS:
        raise ValueError(f"Unknown work item: {work_item_id}")
    updated = WORK_ITEMS[work_item_id].model_copy(update={"status": status})
    WORK_ITEMS[work_item_id] = updated
    return updated


@mcp.tool()
def list_sprint_items(sprint_id: str) -> list[dict[str, Any]]:
    """List work items for a sprint's project."""
    sprint = SPRINTS.get(sprint_id)
    if sprint is None:
        raise ValueError(f"Unknown sprint: {sprint_id}")
    return [
        item.model_dump()
        for item in WORK_ITEMS.values()
        if item.project_id == sprint["project_id"]
    ]


@mcp.tool()
def project_status_report(project_id: str) -> dict[str, Any]:
    """Create a structured project status report."""
    project = get_project(project_id)
    items = [item for item in WORK_ITEMS.values() if item.project_id == project_id]
    risks = [risk for risk in RISKS.values() if risk["project_id"] == project_id]
    completed = sum(item.status == "Done" for item in items)
    return {
        "project": project,
        "delivery": {
            "total_items": len(items),
            "completed_items": completed,
            "completion_percent": round((completed / len(items)) * 100, 1)
            if items
            else 0,
        },
        "work_items": [item.model_dump() for item in items],
        "open_risks": [risk for risk in risks if risk["status"] == "Open"],
        "health": "At Risk" if any(risk["severity"] == "High" for risk in risks) else "On Track",
    }


@mcp.resource("pm://handbook", name="project_management_handbook")
def project_management_handbook() -> str:
    """Read project-management operating principles."""
    return json.dumps(
        {
            "principles": [
                "Every project has a measurable objective and accountable owner.",
                "High-impact changes require review and rollback planning.",
                "Risks are reviewed weekly and escalated by severity.",
                "Status reports distinguish facts, decisions, risks, and asks.",
            ]
        },
        indent=2,
    )


@mcp.resource("pm://roadmap", name="portfolio_roadmap")
def portfolio_roadmap() -> str:
    """Read the sample enterprise roadmap."""
    return json.dumps(
        {
            "quarters": {
                "Q2": ["MCP learning lab", "OAuth vendor adapters"],
                "Q3": ["Governed production pilot", "Enterprise observability"],
                "Q4": ["Agent marketplace", "Multi-tenant rollout"],
            }
        },
        indent=2,
    )


@mcp.prompt(name="sprint_planning_template")
def sprint_planning_template(project_name: str, sprint_goal: str) -> str:
    """Create a structured sprint-planning prompt."""
    return (
        f"Plan a sprint for {project_name}.\n"
        f"Goal: {sprint_goal}\n"
        "Review capacity, dependencies, risks, acceptance criteria, and sequencing."
    )


@mcp.prompt(name="executive_status_template")
def executive_status_template(project_name: str) -> str:
    """Create an executive project-status prompt."""
    return (
        f"Create an executive status update for {project_name}. "
        "Include progress, decisions, risks, mitigations, and leadership asks."
    )


def main() -> None:
    """Run stdio, Streamable HTTP, or legacy SSE for comparison."""
    requested = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    transport = {
        "stdio": "stdio",
        "http": "streamable-http",
        "streamable-http": "streamable-http",
        "sse": "sse",
    }.get(requested)
    if transport is None:
        raise SystemExit("Expected transport: stdio, http, streamable-http, or sse")
    mcp.run(transport=transport)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(0) from None

