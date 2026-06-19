from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gateway import MCPGateway
from governance.approval_engine import ApprovalEngine, ApprovalStatus
from governance.audit_logger import AuditLogger, AuditRecord
from governance.policy_engine import DecisionType, PolicyDecision, PolicyEngine
from governance.rbac import Principal, Role


@dataclass(frozen=True)
class GovernedResult:
    """Result of an allowed MCP execution."""

    result: dict[str, Any]
    decision: PolicyDecision
    approval_request_id: str | None = None


class ApprovalRequired(RuntimeError):
    """Raised when execution is paused for human approval."""

    def __init__(self, request_id: str, decision: PolicyDecision) -> None:
        self.request_id = request_id
        self.decision = decision
        super().__init__(
            f"Approval required. Request id: {request_id}. {decision.explanation()}"
        )


class PolicyDenied(PermissionError):
    """Raised when policy blocks an action."""


class GovernedMCPGateway:
    """Enforce policy, approvals, RBAC, explainability, and audit before MCP calls."""

    def __init__(
        self,
        gateway: MCPGateway,
        policy_engine: PolicyEngine,
        approval_engine: ApprovalEngine,
        audit_logger: AuditLogger,
    ) -> None:
        self.gateway = gateway
        self.policy_engine = policy_engine
        self.approval_engine = approval_engine
        self.audit_logger = audit_logger

    async def request_tool(
        self,
        *,
        principal: Principal,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> GovernedResult:
        """Evaluate and either execute, deny, or pause a proposed MCP action."""
        decision = self.policy_engine.evaluate(
            principal=principal,
            agent_name=agent_name,
            tool_name=tool_name,
            arguments=arguments,
        )
        self._audit_decision(principal, agent_name, tool_name, arguments, decision)

        if decision.outcome == DecisionType.DENY:
            raise PolicyDenied(decision.explanation())

        if decision.outcome in {
            DecisionType.REQUIRE_APPROVAL,
            DecisionType.ESCALATE,
        }:
            request = self.approval_engine.create(
                requester=principal,
                agent_name=agent_name,
                tool_name=tool_name,
                arguments=arguments,
                decision=decision,
            )
            raise ApprovalRequired(request.id, decision)

        result = await self._execute(
            principal=principal,
            agent_name=agent_name,
            tool_name=tool_name,
            arguments=arguments,
        )
        return GovernedResult(result=result, decision=decision)

    async def execute_approved(
        self,
        request_id: str,
        *,
        executor: Principal,
    ) -> GovernedResult:
        """Execute a previously approved request."""
        request = self.approval_engine.get(request_id)
        if request.status != ApprovalStatus.APPROVED:
            raise PermissionError(
                f"Approval request {request_id} is not approved; status={request.status}."
            )

        result = await self._execute(
            principal=executor,
            agent_name=request.agent_name,
            tool_name=request.tool_name,
            arguments=request.arguments,
            approval_request_id=request.id,
        )
        self.approval_engine.mark_executed(request.id)
        return GovernedResult(
            result=result,
            decision=self.policy_engine.evaluate(
                principal=Principal(request.requester_id, Role(request.requester_role)),
                agent_name=request.agent_name,
                tool_name=request.tool_name,
                arguments=request.arguments,
            ),
            approval_request_id=request.id,
        )

    async def _execute(
        self,
        *,
        principal: Principal,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        approval_request_id: str | None = None,
    ) -> dict[str, Any]:
        """Call MCP and audit success or failure."""
        try:
            result = await self.gateway.call_tool(tool_name, arguments)
        except Exception as exc:
            self.audit_logger.log(
                AuditRecord(
                    action="tool_execution",
                    actor_id=principal.id,
                    actor_role=principal.role,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    outcome="failed",
                    detail={
                        "arguments": arguments,
                        "approval_request_id": approval_request_id,
                        "error": str(exc),
                    },
                )
            )
            raise

        self.audit_logger.log(
            AuditRecord(
                action="tool_execution",
                actor_id=principal.id,
                actor_role=principal.role,
                agent_name=agent_name,
                tool_name=tool_name,
                outcome="succeeded",
                detail={
                    "arguments": arguments,
                    "approval_request_id": approval_request_id,
                    "result": result,
                },
            )
        )
        return result

    def _audit_decision(
        self,
        principal: Principal,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        decision: PolicyDecision,
    ) -> None:
        """Audit an explainable policy decision."""
        self.audit_logger.log(
            AuditRecord(
                action="policy_evaluation",
                actor_id=principal.id,
                actor_role=principal.role,
                agent_name=agent_name,
                tool_name=tool_name,
                outcome=decision.outcome,
                detail={
                    "arguments": arguments,
                    "risk_level": decision.risk.level.name,
                    "risk_score": decision.risk.score,
                    "reasons": decision.reasons + decision.risk.reasons,
                    "explanation": decision.explanation(),
                },
            )
        )
