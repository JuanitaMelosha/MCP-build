from __future__ import annotations

import asyncio
import logging

from events.event_bus import Event, EventBus
from events.event_router import EventRouter
from events.event_store import EventStore
from events.metrics import Metrics

logger = logging.getLogger("phase9.runtime")


class AutonomousEventRuntime:
    """Process events autonomously with retries, chaining, storage, and metrics."""

    def __init__(
        self,
        bus: EventBus,
        router: EventRouter,
        store: EventStore,
        metrics: Metrics,
        max_attempts: int = 3,
        retry_base_seconds: float = 0.05,
    ) -> None:
        self.bus = bus
        self.router = router
        self.store = store
        self.metrics = metrics
        self.max_attempts = max_attempts
        self.retry_base_seconds = retry_base_seconds

    async def publish(self, event: Event) -> None:
        """Store and publish a new event."""
        self.store.record(event, "published")
        self.metrics.increment("events_published")
        self.metrics.increment(f"events_published.{event.type}")
        await self.bus.publish(event)

    async def run_until_idle(self) -> None:
        """Run a worker until all currently published and chained events finish."""
        worker = asyncio.create_task(self._worker())
        try:
            await self.bus.join()
        finally:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

    async def replay(
        self,
        *,
        status: str = "completed",
        event_type: str | None = None,
    ) -> int:
        """Replay unique stored events as new events linked to their originals."""
        originals = self.store.replayable_events(status=status, event_type=event_type)
        for original in originals:
            replayed = Event(
                type=original.type,
                payload=original.payload,
                source="event_store.replay",
                correlation_id=original.correlation_id,
                causation_id=original.id,
            )
            await self.publish(replayed)
            self.metrics.increment("events_replayed")
        return len(originals)

    async def _worker(self) -> None:
        """Continuously receive and process events."""
        while True:
            event = await self.bus.receive()
            try:
                await self._process(event)
            finally:
                self.bus.task_done()

    async def _process(self, event: Event) -> None:
        """Route one event with bounded exponential retries."""
        self.metrics.increment("events_received")
        for attempt in range(1, self.max_attempts + 1):
            self.store.record(event, "processing", attempt)
            logger.info(
                "Processing event",
                extra={
                    "event_id": event.id,
                    "event_type": event.type,
                    "attempt": attempt,
                },
            )
            try:
                chained = await self.router.route(event)
                for child in chained:
                    await self.publish(child)
                self.store.record(event, "completed", attempt)
                self.metrics.increment("events_completed")
                self.metrics.increment(f"events_completed.{event.type}")
                return
            except Exception as exc:
                self.metrics.increment("event_attempt_failures")
                self.store.record(event, "retrying", attempt, str(exc))
                logger.warning(
                    "Event attempt failed: %s",
                    exc,
                    extra={
                        "event_id": event.id,
                        "event_type": event.type,
                        "attempt": attempt,
                    },
                )
                if attempt < self.max_attempts:
                    self.metrics.increment("event_retries")
                    await asyncio.sleep(self.retry_base_seconds * (2 ** (attempt - 1)))
                    continue

                self.store.dead_letter(event, attempt, str(exc))
                self.metrics.increment("events_dead_lettered")
                logger.error(
                    "Event moved to dead letter: %s",
                    exc,
                    extra={
                        "event_id": event.id,
                        "event_type": event.type,
                        "attempt": attempt,
                    },
                )

