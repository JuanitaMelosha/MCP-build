from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from events.scheduler import Schedule
from examples.common import temporary_platform


async def main() -> None:
    with temporary_platform() as platform:
        platform.scheduler.schedule(
            Schedule(
                name="daily-summary-demo",
                event_type="daily.summary",
                payload={"city": "Chennai"},
                interval_seconds=0.05,
                max_occurrences=1,
            )
        )
        platform.scheduler.schedule(
            Schedule(
                name="friday-rewind-demo",
                event_type="friday.rewind",
                payload={"customer_id": "123", "ticket_id": "T-1001"},
                interval_seconds=0.05,
                max_occurrences=1,
            )
        )
        await asyncio.sleep(0.1)

        await platform.runtime.run_until_idle()
        await platform.scheduler.stop_all()

        print("Scheduled workflows completed:")
        print(json.dumps(platform.completion_agent.completed, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
