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
        await platform.runtime.publish(
            Event("daily.summary", {"city": "Chennai"}, "replay-demo")
        )
        await platform.runtime.run_until_idle()

        replay_count = await platform.runtime.replay(
            status="completed",
            event_type="daily.summary",
        )
        await platform.runtime.run_until_idle()

        print(f"Replayed events: {replay_count}")
        print("Metrics:")
        print(json.dumps(platform.metrics.snapshot(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

