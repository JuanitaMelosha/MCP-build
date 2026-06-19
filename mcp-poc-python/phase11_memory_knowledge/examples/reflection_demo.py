from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform
from memory.memory_manager import MemoryType


def main() -> None:
    with temporary_platform() as platform:
        for outcome in ("ticket_created", "ticket_created", "resolved_without_ticket"):
            platform.manager.remember(
                f"Handled a premium customer login issue with outcome {outcome}.",
                MemoryType.SESSION,
                source="support_agent",
                importance=0.8,
                metadata={
                    "pattern": "premium_login_issue",
                    "outcome": outcome,
                },
            )

        reflections = platform.reflections.reflect(minimum_occurrences=2)
        print("Reflections:")
        for reflection in reflections:
            print(f"- confidence={reflection.confidence:.2f}: {reflection.summary}")


if __name__ == "__main__":
    main()

