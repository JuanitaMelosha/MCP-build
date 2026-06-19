from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    """Immutable message transported through the event-driven platform."""

    type: str
    payload: dict[str, Any]
    source: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the event to a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Rebuild an event from stored JSON data."""
        return cls(**data)

    def child(self, event_type: str, payload: dict[str, Any], source: str) -> "Event":
        """Create a chained event linked to this event."""
        return Event(
            type=event_type,
            payload=payload,
            source=source,
            correlation_id=self.correlation_id,
            causation_id=self.id,
        )


class EventBus:
    """Beginner-friendly asynchronous in-memory event bus."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()

    async def publish(self, event: Event) -> None:
        """Publish an event for autonomous processing."""
        await self._queue.put(event)

    async def receive(self) -> Event:
        """Wait for the next event."""
        return await self._queue.get()

    def task_done(self) -> None:
        """Mark the current event as processed."""
        self._queue.task_done()

    async def join(self) -> None:
        """Wait until every published event has been processed."""
        await self._queue.join()

    def pending_count(self) -> int:
        """Return the number of events waiting in memory."""
        return self._queue.qsize()

