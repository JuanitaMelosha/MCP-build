from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from events.event_bus import Event
from examples.common import temporary_platform


async def main() -> None:
    with temporary_platform() as platform:
        events = [
            Event(
                "github.pr.created",
                {"number": 42, "pull_request": {"title": "Add MCP event runtime"}},
                "demo",
            ),
            Event("jira.issue.created", {"customer_id": "123"}, "demo"),
            Event("jira.issue.updated", {"ticket_id": "T-1001"}, "demo"),
            Event(
                "slack.message.posted",
                {"event": {"type": "message", "text": "Help customer 123"}},
                "demo",
            ),
            Event("daily.summary", {"city": "Chennai"}, "demo"),
            Event(
                "friday.rewind",
                {"customer_id": "123", "ticket_id": "T-1001"},
                "demo",
            ),
        ]
        for event in events:
            await platform.runtime.publish(event)
        await platform.runtime.run_until_idle()

        print("Completed autonomous workflows:")
        for item in platform.completion_agent.completed:
            print(f"- {item['trigger_event']}")

        print("\nMetrics:")
        print(json.dumps(platform.metrics.snapshot(), indent=2))

        print("\nStored history records:")
        print(len(platform.store.history()))


if __name__ == "__main__":
    asyncio.run(main())

