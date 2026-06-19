from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gateway import build_gateway
from governed_gateway import GovernedMCPGateway
from governance.approval_engine import ApprovalEngine
from governance.audit_logger import AuditLogger
from governance.policy_engine import PolicyEngine
from governance.rbac import RBAC
from governance.risk_assessor import RiskAssessor


@dataclass
class GovernancePlatform:
    """All Phase 10 governance components."""

    governed_gateway: GovernedMCPGateway
    approvals: ApprovalEngine
    audit: AuditLogger
    policy: PolicyEngine
    rbac: RBAC
    risks: RiskAssessor


def build_platform(data_directory: Path) -> GovernancePlatform:
    """Construct the complete governance layer and MCP gateway."""
    rbac = RBAC()
    risks = RiskAssessor()
    policy = PolicyEngine(rbac, risks)
    audit = AuditLogger(data_directory / "audit.jsonl")
    approvals = ApprovalEngine(data_directory / "approvals.json", rbac, audit)
    governed_gateway = GovernedMCPGateway(
        build_gateway(),
        policy,
        approvals,
        audit,
    )
    return GovernancePlatform(
        governed_gateway=governed_gateway,
        approvals=approvals,
        audit=audit,
        policy=policy,
        rbac=rbac,
        risks=risks,
    )
