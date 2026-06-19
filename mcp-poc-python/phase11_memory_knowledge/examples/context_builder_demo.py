from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import seed_organizational_memory, temporary_platform
from memory.memory_manager import MemoryType


def main() -> None:
    with temporary_platform() as platform:
        seed_organizational_memory(platform)
        platform.manager.remember(
            "Customer 123 previously had two login failures after a password reset.",
            MemoryType.LONG_TERM,
            source="support_history",
            importance=0.9,
            metadata={"entity_id": "customer:123"},
        )
        platform.graph.upsert_entity(
            "customer:123",
            "customer",
            {"name": "John Doe"},
        )
        platform.graph.upsert_entity(
            "plan:premium",
            "plan",
            {"name": "Premium"},
        )
        platform.graph.add_relationship(
            "customer:123",
            "SUBSCRIBED_TO",
            "plan:premium",
        )

        context = platform.context.build(
            "Help customer 123 with another login failure",
            entity_id="customer:123",
        )
        print(context.rendered)


if __name__ == "__main__":
    main()

