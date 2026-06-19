from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform


def main() -> None:
    with temporary_platform() as platform:
        graph = platform.graph
        graph.upsert_entity("customer:123", "customer", {"name": "John Doe"})
        graph.upsert_entity("plan:premium", "plan", {"name": "Premium"})
        graph.upsert_entity("ticket:T-1001", "ticket", {"status": "Created"})
        graph.add_relationship("customer:123", "SUBSCRIBED_TO", "plan:premium")
        graph.add_relationship("customer:123", "HAS_TICKET", "ticket:T-1001")

        print("Knowledge graph facts:")
        for fact in graph.related("customer:123"):
            print(f"- {fact.sentence()}")


if __name__ == "__main__":
    main()

