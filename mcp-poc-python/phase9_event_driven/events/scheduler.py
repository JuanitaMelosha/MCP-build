from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from events.event_bus import Event


@dataclass(frozen=True)
class Schedule:
    """Configuration for one scheduled event."""

    name: str
    event_type: str
    payload: dict[str, Any]
    interval_seconds: float
    max_occurrences: int | None = None


class EventScheduler:
    """Publish scheduled events onto the same event bus as webhooks."""

    def __init__(self, publisher: Callable[[Event], Awaitable[None]]) -> None:
        self.publisher = publisher
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def schedule(self, schedule: Schedule) -> None:
        """Start a recurring schedule."""
        if schedule.name in self._tasks:
            raise ValueError(f"Schedule already exists: {schedule.name}")
        self._tasks[schedule.name] = asyncio.create_task(self._run(schedule))

    async def publish_once(
        self,
        event_type: str,
        payload: dict[str, Any],
        delay_seconds: float = 0,
    ) -> Event:
        """Publish one scheduled event after an optional delay."""
        if delay_seconds:
            await asyncio.sleep(delay_seconds)
        event = Event(event_type, payload, "scheduler")
        await self.publisher(event)
        return event

    async def stop(self, name: str) -> None:
        """Stop one recurring schedule."""
        task = self._tasks.pop(name, None)
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def stop_all(self) -> None:
        """Stop every schedule."""
        for name in list(self._tasks):
            await self.stop(name)

    async def _run(self, schedule: Schedule) -> None:
        """Publish recurring events until stopped or the occurrence limit is reached."""
        count = 0
        while schedule.max_occurrences is None or count < schedule.max_occurrences:
            await asyncio.sleep(schedule.interval_seconds)
            await self.publisher(
                Event(schedule.event_type, schedule.payload, f"schedule.{schedule.name}")
            )
            count += 1
