from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import seed_organizational_memory, temporary_platform


def main() -> None:
    with temporary_platform() as platform:
        seed_organizational_memory(platform)
        results = platform.context.organizational_context(
            "How should we handle a premium customer login problem?"
        )
        print("Semantic organizational-memory results:")
        for result in results:
            print(f"- {result.score:.3f}: {result.memory.content}")


if __name__ == "__main__":
    main()

