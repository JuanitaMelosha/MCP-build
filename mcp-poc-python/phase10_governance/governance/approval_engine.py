from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from governance.audit_logger import AuditLogger, AuditRecord
from governance.policy_engine import PolicyDecision
from governance.rbac import Principal, RBAC
from governance.risk_assessor import RiskLevel


class ApprovalStatus(StrEnum):
    """Approval request states."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"


@dataclass
class ApprovalRequest:
    """Persisted human approval request for a governed action."""

    requester_id: str
    requester_role: str
    agent_name: str
    tool_name: str
    arguments: dict[str, Any]
    risk_level: str
    explanation: str
    required_approval_role: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    decided_at: str | None = None
    decided_by: str | None = None
    decision_reason: str | None = None


class ApprovalEngine:
    """Persist and decide human approval requests."""

    def __init__(
        self,
        path: Path,
        rbac: RBAC,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.path = path
        self.rbac = rbac
        self.audit_logger = audit_logger
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        requester: Principal,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        decision: PolicyDecision,
    ) -> ApprovalRequest:
        """Create and persist a pending approval request."""
        request = ApprovalRequest(
            requester_id=requester.id,
            requester_role=requester.role,
            agent_name=agent_name,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=decision.risk.level.name,
            explanation=decision.explanation(),
            required_approval_role=decision.required_approval_role or "approver",
        )
        requests = self._load()
        requests.append(request)
        self._save(requests)
        self._audit(
            request,
            action="approval_requested",
            actor_id=requester.id,
            actor_role=requester.role,
            outcome=request.status,
            detail={"explanation": request.explanation},
        )
        return request

    def list_requests(
        self,
        status: ApprovalStatus | None = None,
    ) -> list[ApprovalRequest]:
        """List all or status-filtered approval requests."""
        requests = self._load()
        return [request for request in requests if status is None or request.status == status]

    def get(self, request_id: str) -> ApprovalRequest:
        """Return one approval request."""
        for request in self._load():
            if request.id == request_id:
                return request
        raise KeyError(f"Unknown approval request: {request_id}")

    def approve(
        self,
        request_id: str,
        approver: Principal,
        reason: str,
    ) -> ApprovalRequest:
        """Approve a request when the approver has the required RBAC permission."""
        request = self.get(request_id)
        permission = (
            "approval:critical"
            if request.risk_level == RiskLevel.CRITICAL.name
            else "approval:high"
        )
        if not self.rbac.has_permission(approver, permission):
            raise PermissionError(
                f"Role '{approver.role}' lacks required permission '{permission}'."
            )
        if approver.id == request.requester_id:
            raise PermissionError("Separation of duties prevents self-approval.")
        return self._decide(request_id, ApprovalStatus.APPROVED, approver, reason)

    def deny(
        self,
        request_id: str,
        approver: Principal,
        reason: str,
    ) -> ApprovalRequest:
        """Deny a pending request."""
        request = self.get(request_id)
        permission = (
            "approval:critical"
            if request.risk_level == RiskLevel.CRITICAL.name
            else "approval:high"
        )
        if not self.rbac.has_permission(approver, permission):
            raise PermissionError(
                f"Role '{approver.role}' lacks required permission '{permission}'."
            )
        return self._decide(request_id, ApprovalStatus.DENIED, approver, reason)

    def mark_executed(self, request_id: str) -> ApprovalRequest:
        """Mark an approved request after successful MCP execution."""
        requests = self._load()
        for request in requests:
            if request.id == request_id:
                if request.status != ApprovalStatus.APPROVED:
                    raise ValueError("Only approved requests can be executed.")
                request.status = ApprovalStatus.EXECUTED
                self._save(requests)
                self._audit(
                    request,
                    action="approval_executed",
                    actor_id=request.decided_by or "system",
                    actor_role=request.required_approval_role,
                    outcome=request.status,
                    detail={"approval_request_id": request.id},
                )
                return request
        raise KeyError(f"Unknown approval request: {request_id}")

    def _decide(
        self,
        request_id: str,
        status: ApprovalStatus,
        approver: Principal,
        reason: str,
    ) -> ApprovalRequest:
        """Apply a human decision to a pending request."""
        requests = self._load()
        for request in requests:
            if request.id != request_id:
                continue
            if request.status != ApprovalStatus.PENDING:
                raise ValueError("Only pending requests can be decided.")
            request.status = status
            request.decided_at = datetime.now(UTC).isoformat()
            request.decided_by = approver.id
            request.decision_reason = reason
            self._save(requests)
            self._audit(
                request,
                action=f"approval_{status.value}",
                actor_id=approver.id,
                actor_role=approver.role,
                outcome=status,
                detail={"reason": reason},
            )
            return request
        raise KeyError(f"Unknown approval request: {request_id}")

    def _load(self) -> list[ApprovalRequest]:
        """Load persisted requests."""
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text())
        return [
            ApprovalRequest(
                **{
                    **item,
                    "status": ApprovalStatus(item["status"]),
                }
            )
            for item in data
        ]

    def _save(self, requests: list[ApprovalRequest]) -> None:
        """Persist requests atomically enough for this local learning lab."""
        self.path.write_text(
            json.dumps([asdict(request) for request in requests], indent=2, default=str)
        )

    def _audit(
        self,
        request: ApprovalRequest,
        *,
        action: str,
        actor_id: str,
        actor_role: str,
        outcome: str,
        detail: dict[str, Any],
    ) -> None:
        """Audit an approval lifecycle change when a logger is configured."""
        if self.audit_logger is None:
            return
        self.audit_logger.log(
            AuditRecord(
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                agent_name=request.agent_name,
                tool_name=request.tool_name,
                outcome=outcome,
                detail={"approval_request_id": request.id, **detail},
            )
        )
