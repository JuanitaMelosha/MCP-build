from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Metrics:
    """In-memory counters for event-runtime observability."""

    counters: Counter[str] = field(default_factory=Counter)

    def increment(self, name: str, amount: int = 1) -> None:
        """Increment a named metric."""
        self.counters[name] += amount

    def snapshot(self) -> dict[str, int]:
        """Return current metric values."""
        return dict(sorted(self.counters.items()))

    def reset(self) -> None:
        """Clear all metrics."""
        self.counters.clear()

