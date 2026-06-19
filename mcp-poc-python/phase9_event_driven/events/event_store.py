from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from events.event_bus import Event


@dataclass(frozen=True)
class EventRecord:
    """One persistent event lifecycle record."""

    event: dict[str, Any]
    status: str
    attempt: int
    detail: str | None = None
    recorded_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class EventStore:
    """Append-only JSONL event history and dead-letter store."""

    def __init__(self, history_path: Path, dead_letter_path: Path) -> None:
        self.history_path = history_path
        self.dead_letter_path = dead_letter_path
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.dead_letter_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        event: Event,
        status: str,
        attempt: int = 0,
        detail: str | None = None,
    ) -> None:
        """Append one lifecycle record to event history."""
        record = EventRecord(event.to_dict(), status, attempt, detail)
        self._append(self.history_path, asdict(record))

    def dead_letter(self, event: Event, attempts: int, error: str) -> None:
        """Store an event that exhausted all retries."""
        record = EventRecord(event.to_dict(), "dead_letter", attempts, error)
        serialized = asdict(record)
        self._append(self.dead_letter_path, serialized)
        self._append(self.history_path, serialized)

    def history(self) -> list[EventRecord]:
        """Read all event history records."""
        return [EventRecord(**item) for item in self._read(self.history_path)]

    def dead_letters(self) -> list[EventRecord]:
        """Read all dead-letter records."""
        return [EventRecord(**item) for item in self._read(self.dead_letter_path)]

    def replayable_events(
        self,
        *,
        status: str = "completed",
        event_type: str | None = None,
    ) -> list[Event]:
        """Return unique events matching a stored status for replay."""
        events: list[Event] = []
        seen: set[str] = set()
        for record in self.history():
            event = Event.from_dict(record.event)
            if record.status != status or event.id in seen:
                continue
            if event_type is not None and event.type != event_type:
                continue
            seen.add(event.id)
            events.append(event)
        return events

    def _append(self, path: Path, data: dict[str, Any]) -> None:
        """Append one JSON object as a line."""
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(data, sort_keys=True) + "\n")

    def _read(self, path: Path) -> list[dict[str, Any]]:
        """Read JSONL records when the file exists."""
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

