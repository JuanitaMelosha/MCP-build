from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class MemoryEvent:
    """One immutable communication event shared between agents."""

    agent: str
    event_type: str
    payload: Any
    created_at: str


@dataclass
class SharedMemory:
    """Shared workflow state and communication history."""

    values: dict[str, Any] = field(default_factory=dict)
    events: list[MemoryEvent] = field(default_factory=list)

    def write(self, key: str, value: Any, agent: str) -> None:
        """Store a value and record who produced it."""
        self.values[key] = value
        self.publish(agent, "memory_write", {"key": key, "value": value})

    def read(self, key: str, default: Any = None) -> Any:
        """Read one shared value."""
        return self.values.get(key, default)

    def require(self, key: str) -> Any:
        """Read a required value or raise a clear workflow error."""
        if key not in self.values:
            raise KeyError(f"Shared memory is missing required key: {key}")
        return self.values[key]

    def publish(self, agent: str, event_type: str, payload: Any) -> None:
        """Publish an event for communication and audit history."""
        self.events.append(
            MemoryEvent(
                agent=agent,
                event_type=event_type,
                payload=payload,
                created_at=datetime.now(UTC).isoformat(),
            )
        )

    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of current workflow values."""
        return dict(self.values)

    def clear(self) -> None:
        """Reset shared workflow state."""
        self.values.clear()
        self.events.clear()

