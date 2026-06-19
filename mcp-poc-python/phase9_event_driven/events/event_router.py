from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable

from events.event_bus import Event

EventHandler = Callable[[Event], Awaitable[Event | list[Event] | None]]


class NoEventHandlerError(LookupError):
    """Raised when an event has no registered handler."""


class EventRouter:
    """Route event types to one or more asynchronous agent handlers."""

    def __init__(self) -> None:
        self._routes: dict[str, list[EventHandler]] = defaultdict(list)

    def register(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an exact event type."""
        self._routes[event_type].append(handler)

    def remove(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler when it is currently registered."""
        handlers = self._routes.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def list_routes(self) -> dict[str, int]:
        """Return event types and their handler counts."""
        return {name: len(handlers) for name, handlers in sorted(self._routes.items())}

    async def route(self, event: Event) -> list[Event]:
        """Invoke all handlers and collect chained events."""
        handlers = self._routes.get(event.type, [])
        if not handlers:
            raise NoEventHandlerError(f"No handler registered for event: {event.type}")

        chained: list[Event] = []
        for handler in handlers:
            result = await handler(event)
            if result is None:
                continue
            if isinstance(result, Event):
                chained.append(result)
            else:
                chained.extend(result)
        return chained

