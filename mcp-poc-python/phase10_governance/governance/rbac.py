from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """Human roles used by the governance layer."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"
    ADMIN = "admin"


@dataclass(frozen=True)
class Principal:
    """Authenticated human requesting or approving an action."""

    id: str
    role: Role


class RBAC:
    """Role-based and agent-level permission checks."""

    ROLE_PERMISSIONS: dict[Role, set[str]] = {
        Role.VIEWER: {"tool:read"},
        Role.OPERATOR: {"tool:read", "tool:request_write"},
        Role.APPROVER: {"tool:read", "tool:request_write", "approval:high"},
        Role.ADMIN: {
            "tool:read",
            "tool:request_write",
            "approval:high",
            "approval:critical",
            "policy:override",
        },
    }

    AGENT_TOOL_PATTERNS: dict[str, set[str]] = {
        "research_agent": {
            "customer.get_customer",
            "customer.get_customer_plan",
            "weather.get_weather",
            "weather.get_forecast",
            "ticket.get_ticket_status",
        },
        "planning_agent": set(),
        "execution_agent": {
            "customer.get_customer",
            "ticket.get_ticket_status",
            "ticket.create_ticket",
            "ops.deploy_production",
        },
        "reporting_agent": set(),
        "autonomous_agent": {
            "customer.get_customer",
            "weather.get_weather",
            "ticket.get_ticket_status",
            "ticket.create_ticket",
        },
    }

    def has_permission(self, principal: Principal, permission: str) -> bool:
        """Return whether a human role contains a permission."""
        return permission in self.ROLE_PERMISSIONS[principal.role]

    def agent_can_use(self, agent_name: str, tool_name: str) -> bool:
        """Return whether an agent is permitted to request a tool."""
        return tool_name in self.AGENT_TOOL_PATTERNS.get(agent_name, set())

    def explain_role(self, principal: Principal) -> list[str]:
        """Return sorted permissions for explainability."""
        return sorted(self.ROLE_PERMISSIONS[principal.role])

    def explain_agent(self, agent_name: str) -> list[str]:
        """Return sorted agent tool permissions."""
        return sorted(self.AGENT_TOOL_PATTERNS.get(agent_name, set()))
