from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class RiskLevel(IntEnum):
    """Ordered enterprise action-risk levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class RiskAssessment:
    """Risk classification and human-readable explanation."""

    level: RiskLevel
    score: int
    reasons: list[str]


class RiskAssessor:
    """Classify MCP tool calls using transparent educational rules."""

    TOOL_RISK: dict[str, RiskLevel] = {
        "customer.get_customer": RiskLevel.LOW,
        "customer.get_customer_plan": RiskLevel.LOW,
        "weather.get_weather": RiskLevel.LOW,
        "weather.get_forecast": RiskLevel.LOW,
        "ticket.get_ticket_status": RiskLevel.LOW,
        "ticket.create_ticket": RiskLevel.HIGH,
    }

    def assess(self, tool_name: str, arguments: dict[str, Any]) -> RiskAssessment:
        """Assess tool risk from its known behavior and argument content."""
        level = self.TOOL_RISK.get(tool_name, self._infer_unknown_tool_risk(tool_name))
        reasons = [self._base_reason(tool_name, level)]

        if self._contains_sensitive_data(arguments):
            level = max(level, RiskLevel.HIGH)
            reasons.append("Arguments appear to contain sensitive data.")

        if any(word in tool_name.lower() for word in ("delete", "disable", "revoke", "deploy")):
            level = RiskLevel.CRITICAL
            reasons.append("Tool name indicates destructive or production-impacting behavior.")

        return RiskAssessment(level=level, score=int(level) * 25, reasons=reasons)

    def _infer_unknown_tool_risk(self, tool_name: str) -> RiskLevel:
        """Use conservative defaults for tools missing from the catalog."""
        lowered = tool_name.lower()
        if any(word in lowered for word in ("create", "update", "write", "send", "post")):
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    def _base_reason(self, tool_name: str, level: RiskLevel) -> str:
        """Explain the base tool classification."""
        descriptions = {
            RiskLevel.LOW: "Read-only or low-impact operation.",
            RiskLevel.MEDIUM: "Unknown or moderately impactful operation.",
            RiskLevel.HIGH: "Operation changes an external system.",
            RiskLevel.CRITICAL: "Operation may be destructive or production-impacting.",
        }
        return f"{tool_name}: {descriptions[level]}"

    def _contains_sensitive_data(self, arguments: dict[str, Any]) -> bool:
        """Detect obvious sensitive argument field names."""
        sensitive_terms = {"password", "secret", "token", "api_key", "credit_card"}
        return any(str(key).lower() in sensitive_terms for key in arguments)

