from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agents.event_agents import CompletionAgent, ReportingEventAgent, register_event_agents
from events.event_bus import EventBus
from events.event_router import EventRouter
from events.event_store import EventStore
from events.metrics import Metrics
from events.runtime import AutonomousEventRuntime
from events.scheduler import EventScheduler
from events.webhook_handler import WebhookHandler
from gateway import build_gateway


@dataclass
class EventDrivenPlatform:
    """All collaborating components in the Phase 9 autonomous platform."""

    bus: EventBus
    router: EventRouter
    store: EventStore
    metrics: Metrics
    runtime: AutonomousEventRuntime
    scheduler: EventScheduler
    webhooks: WebhookHandler
    reporting_agent: ReportingEventAgent
    completion_agent: CompletionAgent


def build_platform(
    data_directory: Path,
    *,
    github_webhook_secret: str | None = None,
    max_attempts: int = 3,
) -> EventDrivenPlatform:
    """Construct the event bus, agents, gateway, storage, and runtime."""
    bus = EventBus()
    router = EventRouter()
    store = EventStore(
        data_directory / "events.jsonl",
        data_directory / "dead_letters.jsonl",
    )
    metrics = Metrics()
    _, reporting, completion = register_event_agents(router, build_gateway(), metrics)
    runtime = AutonomousEventRuntime(
        bus,
        router,
        store,
        metrics,
        max_attempts=max_attempts,
    )
    return EventDrivenPlatform(
        bus=bus,
        router=router,
        store=store,
        metrics=metrics,
        runtime=runtime,
        scheduler=EventScheduler(runtime.publish),
        webhooks=WebhookHandler(runtime.publish, github_webhook_secret),
        reporting_agent=reporting,
        completion_agent=completion,
    )
