from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agent.memory import AgentMemory
from agent.tool_selector import ToolSelector
from gateway import ToolInfo


@dataclass
class PlanStep:
    """One planned tool call."""

    intent: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlan:
    """An ordered list of steps produced for one user request."""

    user_request: str
    steps: list[PlanStep]


class Planner:
    """Transparent rule-based planner for the Phase 7 learning examples."""

    def __init__(self, tool_selector: ToolSelector) -> None:
        self.tool_selector = tool_selector

    def create_plan(
        self,
        user_request: str,
        available_tools: list[ToolInfo],
    ) -> AgentPlan:
        """Parse a request and create an ordered, validated tool plan."""
        request = user_request.lower()
        steps: list[PlanStep] = []

        if "customer" in request:
            customer_id = self._extract_customer_id(user_request)
            tool = self.tool_selector.select("get_customer", available_tools)
            steps.append(
                PlanStep(
                    intent="get_customer",
                    tool_name=tool.name,
                    arguments={"customer_id": customer_id},
                )
            )

        if "weather" in request:
            city = self._extract_city(user_request)
            tool = self.tool_selector.select("get_weather", available_tools)
            steps.append(
                PlanStep(
                    intent="get_weather",
                    tool_name=tool.name,
                    arguments={"city": city},
                )
            )

        if "ticket" in request:
            tool = self.tool_selector.select("create_ticket", available_tools)
            steps.append(
                PlanStep(
                    intent="create_ticket",
                    tool_name=tool.name,
                    arguments={
                        "title": self._extract_ticket_title(user_request),
                        "priority": self._extract_priority(user_request),
                    },
                )
            )

        if not steps:
            raise ValueError(
                "I can currently handle customer lookup, weather lookup, and ticket creation."
            )

        return AgentPlan(user_request=user_request, steps=steps)

    def resolve_step(self, step: PlanStep, memory: AgentMemory) -> PlanStep:
        """Enrich a later step with results from earlier steps."""
        if step.intent != "create_ticket":
            return step

        customer = memory.latest_result("customer.get_customer")
        if customer is None:
            return step

        arguments = dict(step.arguments)
        arguments["title"] = (
            f"Support request for customer {customer['id']} - {customer['name']}"
        )
        return PlanStep(step.intent, step.tool_name, arguments)

    def _extract_customer_id(self, request: str) -> str:
        """Extract a customer id following the word customer."""
        match = re.search(r"customer\s+(?:id\s+)?([A-Za-z0-9_-]+)", request, re.IGNORECASE)
        return match.group(1) if match else "123"

    def _extract_city(self, request: str) -> str:
        """Extract a city after 'in' or 'for', with Chennai as the teaching default."""
        match = re.search(
            r"weather\s+(?:in|for)\s+([A-Za-z][A-Za-z ]*?)(?:\s+and|\s*$)",
            request,
            re.IGNORECASE,
        )
        return match.group(1).strip().title() if match else "Chennai"

    def _extract_priority(self, request: str) -> str:
        """Extract High, Medium, or Low priority."""
        match = re.search(r"\b(high|medium|low)\b", request, re.IGNORECASE)
        return match.group(1).title() if match else "High"

    def _extract_ticket_title(self, request: str) -> str:
        """Create a simple title from the user request."""
        return "Login Issue" if "login" in request.lower() else "Customer Support Request"

