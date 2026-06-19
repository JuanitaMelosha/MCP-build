from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from governance.rbac import Principal, RBAC
from governance.risk_assessor import RiskAssessment, RiskAssessor, RiskLevel


class DecisionType(StrEnum):
    """Possible governance outcomes."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    """Explainable result of governance policy evaluation."""

    outcome: DecisionType
    tool_name: str
    risk: RiskAssessment
    reasons: list[str]
    required_approval_role: str | None = None

    def explanation(self) -> str:
        """Return a concise human-readable explanation."""
        reason_text = " ".join(self.reasons + self.risk.reasons)
        approval = (
            f" Required approval role: {self.required_approval_role}."
            if self.required_approval_role
            else ""
        )
        return (
            f"Decision={self.outcome}; risk={self.risk.level.name}; "
            f"score={self.risk.score}. {reason_text}{approval}"
        )


class PolicyEngine:
    """Evaluate risk, human RBAC, agent permissions, and approval policy."""

    def __init__(self, rbac: RBAC, risk_assessor: RiskAssessor) -> None:
        self.rbac = rbac
        self.risk_assessor = risk_assessor

    def evaluate(
        self,
        *,
        principal: Principal,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> PolicyDecision:
        """Return an explainable policy decision for one proposed MCP action."""
        risk = self.risk_assessor.assess(tool_name, arguments)

        if not self.rbac.agent_can_use(agent_name, tool_name):
            return PolicyDecision(
                DecisionType.DENY,
                tool_name,
                risk,
                [f"Agent '{agent_name}' is not permitted to request this tool."],
            )

        if risk.level <= RiskLevel.MEDIUM:
            if not self.rbac.has_permission(principal, "tool:read"):
                return PolicyDecision(
                    DecisionType.DENY,
                    tool_name,
                    risk,
                    [f"Role '{principal.role}' lacks tool:read permission."],
                )
            return PolicyDecision(
                DecisionType.ALLOW,
                tool_name,
                risk,
                ["Low/medium-risk action is allowed by role and agent policy."],
            )

        if not self.rbac.has_permission(principal, "tool:request_write"):
            return PolicyDecision(
                DecisionType.DENY,
                tool_name,
                risk,
                [f"Role '{principal.role}' cannot request write operations."],
            )

        if risk.level == RiskLevel.CRITICAL:
            return PolicyDecision(
                DecisionType.ESCALATE,
                tool_name,
                risk,
                ["Critical actions require administrator escalation."],
                required_approval_role="admin",
            )

        return PolicyDecision(
            DecisionType.REQUIRE_APPROVAL,
            tool_name,
            risk,
            ["High-risk external-system changes require human approval."],
            required_approval_role="approver",
        )

