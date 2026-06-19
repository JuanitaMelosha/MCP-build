from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AuditRecord:
    """Immutable governance audit record."""

    action: str
    actor_id: str
    actor_role: str
    agent_name: str
    tool_name: str
    outcome: str
    detail: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AuditLogger:
    """Append-only JSONL audit log for governance decisions and execution."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: AuditRecord) -> None:
        """Append one audit record."""
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(record), default=str, sort_keys=True) + "\n")

    def records(self) -> list[AuditRecord]:
        """Read all audit records."""
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as file:
            return [AuditRecord(**json.loads(line)) for line in file if line.strip()]

    def search(
        self,
        *,
        tool_name: str | None = None,
        outcome: str | None = None,
    ) -> list[AuditRecord]:
        """Filter audit records by tool or outcome."""
        records = self.records()
        if tool_name is not None:
            records = [record for record in records if record.tool_name == tool_name]
        if outcome is not None:
            records = [record for record in records if record.outcome == outcome]
        return records

