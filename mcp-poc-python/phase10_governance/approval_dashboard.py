from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from governance.approval_engine import ApprovalStatus
from governance.rbac import Principal, Role
from governance_platform import build_platform

DATA_DIR = Path(__file__).resolve().parent / "runtime_data"


def build_parser() -> argparse.ArgumentParser:
    """Build the approval dashboard command-line parser."""
    parser = argparse.ArgumentParser(description="Phase 10 approval dashboard")
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_parser = subcommands.add_parser("list", help="List approval requests")
    list_parser.add_argument(
        "--status",
        choices=[status.value for status in ApprovalStatus],
    )

    show_parser = subcommands.add_parser("show", help="Show one approval request")
    show_parser.add_argument("request_id")

    for command in ("approve", "deny"):
        decision_parser = subcommands.add_parser(command)
        decision_parser.add_argument("request_id")
        decision_parser.add_argument("--actor", required=True)
        decision_parser.add_argument(
            "--role",
            required=True,
            choices=[role.value for role in Role],
        )
        decision_parser.add_argument("--reason", required=True)

    execute_parser = subcommands.add_parser("execute", help="Execute an approved request")
    execute_parser.add_argument("request_id")
    execute_parser.add_argument("--actor", required=True)
    execute_parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in Role],
    )

    subcommands.add_parser("audit", help="Print audit records")
    return parser


async def run(args: argparse.Namespace) -> None:
    """Execute one dashboard command."""
    platform = build_platform(DATA_DIR)

    if args.command == "list":
        status = ApprovalStatus(args.status) if args.status else None
        requests = platform.approvals.list_requests(status)
        for request in requests:
            print(
                f"{request.id} | {request.status} | {request.risk_level} | "
                f"{request.tool_name} | requester={request.requester_id}"
            )
        return

    if args.command == "show":
        print(
            json.dumps(
                platform.approvals.get(args.request_id).__dict__,
                indent=2,
                default=str,
            )
        )
        return

    if args.command in {"approve", "deny"}:
        actor = Principal(args.actor, Role(args.role))
        if args.command == "approve":
            request = platform.approvals.approve(args.request_id, actor, args.reason)
        else:
            request = platform.approvals.deny(args.request_id, actor, args.reason)
        print(f"{request.id}: {request.status}")
        return

    if args.command == "execute":
        actor = Principal(args.actor, Role(args.role))
        result = await platform.governed_gateway.execute_approved(
            args.request_id,
            executor=actor,
        )
        print(json.dumps(result.result, indent=2))
        return

    if args.command == "audit":
        for record in platform.audit.records():
            print(json.dumps(record.__dict__, default=str, sort_keys=True))


def main() -> None:
    """Parse CLI arguments and run the dashboard."""
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
