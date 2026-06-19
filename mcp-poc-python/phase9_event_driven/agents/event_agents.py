from __future__ import annotations

import json
import logging
import re
from typing import Any

from events.event_bus import Event
from events.event_router import EventRouter
from events.metrics import Metrics
from gateway import MCPGateway

logger = logging.getLogger("phase9.agents")


class AutonomousMCPAgent:
    """Translate external events into automatic MCP tool workflows."""

    name = "autonomous_mcp_agent"

    def __init__(self, gateway: MCPGateway, metrics: Metrics) -> None:
        self.gateway = gateway
        self.metrics = metrics

    async def github_pr_created(self, event: Event) -> Event:
        """Create a review ticket when GitHub opens a pull request."""
        pull_request = event.payload.get("pull_request", {})
        title = pull_request.get("title", "Untitled pull request")
        number = pull_request.get("number") or event.payload.get("number", "unknown")
        result = await self._call(
            "ticket.create_ticket",
            {"title": f"Review PR #{number}: {title}", "priority": "Medium"},
        )
        return self._report_event(event, {"ticket": result})

    async def jira_issue_created(self, event: Event) -> Event:
        """Research the related customer when Jira creates an issue."""
        customer_id = str(event.payload.get("customer_id", "123"))
        customer = await self._call(
            "customer.get_customer",
            {"customer_id": customer_id},
        )
        return self._report_event(event, {"customer": customer})

    async def jira_issue_updated(self, event: Event) -> Event:
        """Check support ticket status after a Jira issue update."""
        ticket_id = str(event.payload.get("ticket_id", "T-1001"))
        status = await self._call(
            "ticket.get_ticket_status",
            {"ticket_id": ticket_id},
        )
        return self._report_event(event, {"ticket_status": status})

    async def slack_message_posted(self, event: Event) -> Event:
        """Turn a Slack customer-support message into a researched ticket."""
        if event.payload.get("force_failure"):
            raise RuntimeError("Intentional Slack agent failure for retry demonstration.")

        text = event.payload.get("event", {}).get("text", "")
        customer_id = self._extract_customer_id(text)
        customer = await self._call(
            "customer.get_customer",
            {"customer_id": customer_id},
        )
        ticket = await self._call(
            "ticket.create_ticket",
            {
                "title": f"Slack request for {customer['name']} ({customer['id']})",
                "priority": "High" if customer["plan"] == "Premium" else "Medium",
            },
        )
        return self._report_event(event, {"customer": customer, "ticket": ticket})

    async def daily_summary(self, event: Event) -> Event:
        """Collect a daily operational signal through MCP."""
        city = str(event.payload.get("city", "Chennai"))
        weather = await self._call("weather.get_weather", {"city": city})
        return self._report_event(event, {"weather": weather})

    async def friday_rewind(self, event: Event) -> Event:
        """Collect multiple MCP signals for a Friday rewind."""
        customer_id = str(event.payload.get("customer_id", "123"))
        ticket_id = str(event.payload.get("ticket_id", "T-1001"))
        customer = await self._call(
            "customer.get_customer",
            {"customer_id": customer_id},
        )
        ticket = await self._call(
            "ticket.get_ticket_status",
            {"ticket_id": ticket_id},
        )
        return self._report_event(
            event,
            {"customer": customer, "ticket_status": ticket},
        )

    async def _call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one MCP tool and update metrics."""
        self.metrics.increment("mcp_tool_calls")
        self.metrics.increment(f"mcp_tool_calls.{tool}")
        logger.info("Autonomous MCP call %s %s", tool, arguments)
        return await self.gateway.call_tool(tool, arguments)

    def _report_event(self, parent: Event, result: dict[str, Any]) -> Event:
        """Chain an agent report request from an external event."""
        return parent.child(
            "agent.report.requested",
            {
                "trigger_event": parent.type,
                "trigger_source": parent.source,
                "result": result,
            },
            self.name,
        )

    def _extract_customer_id(self, text: str) -> str:
        """Extract a customer id from Slack text."""
        match = re.search(r"customer\s+(?:id\s+)?([A-Za-z0-9_-]+)", text, re.IGNORECASE)
        return match.group(1) if match else "123"


class ReportingEventAgent:
    """Convert workflow results into human-readable autonomous reports."""

    name = "reporting_agent"

    def __init__(self) -> None:
        self.reports: list[str] = []

    async def create_report(self, event: Event) -> Event:
        """Create a report and chain workflow completion."""
        report = (
            f"Autonomous workflow for {event.payload['trigger_event']} completed.\n"
            f"{json.dumps(event.payload['result'], indent=2)}"
        )
        self.reports.append(report)
        logger.info("Autonomous report created for %s", event.payload["trigger_event"])
        return event.child(
            "agent.workflow.completed",
            {
                "trigger_event": event.payload["trigger_event"],
                "report": report,
            },
            self.name,
        )


class CompletionAgent:
    """Observe completed workflow events."""

    name = "completion_agent"

    def __init__(self) -> None:
        self.completed: list[dict[str, Any]] = []

    async def workflow_completed(self, event: Event) -> None:
        """Record one completed autonomous workflow."""
        self.completed.append(event.payload)
        logger.info("Workflow completion recorded for %s", event.payload["trigger_event"])


def register_event_agents(
    router: EventRouter,
    gateway: MCPGateway,
    metrics: Metrics,
) -> tuple[AutonomousMCPAgent, ReportingEventAgent, CompletionAgent]:
    """Create agents and register all external and internal event routes."""
    autonomous = AutonomousMCPAgent(gateway, metrics)
    reporting = ReportingEventAgent()
    completion = CompletionAgent()

    router.register("github.pr.created", autonomous.github_pr_created)
    router.register("jira.issue.created", autonomous.jira_issue_created)
    router.register("jira.issue.updated", autonomous.jira_issue_updated)
    router.register("slack.message.posted", autonomous.slack_message_posted)
    router.register("daily.summary", autonomous.daily_summary)
    router.register("friday.rewind", autonomous.friday_rewind)
    router.register("agent.report.requested", reporting.create_report)
    router.register("agent.workflow.completed", completion.workflow_completed)
    return autonomous, reporting, completion

