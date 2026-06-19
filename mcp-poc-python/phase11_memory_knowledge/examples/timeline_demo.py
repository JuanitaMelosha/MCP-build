from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from memory.memory_manager import MemoryType


def main() -> None:
    with temporary_platform() as platform:
        entity_id = "customer:123"
        platform.manager.remember(
            "Customer 123 joined the Premium plan.",
            MemoryType.LONG_TERM,
            source="crm",
            importance=0.8,
            metadata={"entity_id": entity_id},
        )
        platform.manager.remember(
            "Customer 123 reported a login issue.",
            MemoryType.LONG_TERM,
            source="support",
            importance=0.9,
            metadata={"entity_id": entity_id},
        )
        platform.manager.remember(
            "Ticket T-1001 was created for customer 123.",
            MemoryType.LONG_TERM,
            source="ticketing",
            importance=0.9,
            metadata={"entity_id": entity_id},
        )

        print("Customer timeline:")
        for memory in platform.manager.build_timeline(entity_id=entity_id):
            print(f"- {memory.created_at}: {memory.content}")


if __name__ == "__main__":
    main()

