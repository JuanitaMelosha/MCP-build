from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from events.event_bus import Event
from examples.common import temporary_platform


async def main() -> None:
    with temporary_platform(max_attempts=3) as platform:
        await platform.runtime.publish(
            Event(
                "slack.message.posted",
                {
                    "force_failure": True,
                    "event": {"type": "message", "text": "Fail this workflow"},
                },
                "dead-letter-demo",
            )
        )
        await platform.runtime.run_until_idle()

        dead_letters = platform.store.dead_letters()
        print(f"Dead-letter events: {len(dead_letters)}")
        print(json.dumps(platform.metrics.snapshot(), indent=2))
        if dead_letters:
            print(dead_letters[0].detail)


if __name__ == "__main__":
    asyncio.run(main())

