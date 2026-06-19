from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from memory.memory_manager import MemoryManager, MemoryRecord, MemoryType


@dataclass(frozen=True)
class Reflection:
    """Durable lesson derived from multiple experiences."""

    summary: str
    evidence_memory_ids: list[str]
    confidence: float
    metadata: dict[str, Any]


class ReflectionEngine:
    """Convert repeated session experiences into long-term lessons."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory_manager = memory_manager

    def reflect(self, minimum_occurrences: int = 2) -> list[Reflection]:
        """Find repeated tagged patterns and store durable reflections."""
        memories = self.memory_manager.all_memories(
            {MemoryType.SESSION, MemoryType.LONG_TERM}
        )
        grouped: dict[str, list[MemoryRecord]] = defaultdict(list)
        for memory in memories:
            pattern = str(memory.metadata.get("pattern", "")).strip()
            if pattern:
                grouped[pattern].append(memory)

        reflections: list[Reflection] = []
        for pattern, evidence in grouped.items():
            if len(evidence) < minimum_occurrences:
                continue
            outcomes = Counter(
                str(memory.metadata.get("outcome", "unknown")) for memory in evidence
            )
            most_common_outcome, count = outcomes.most_common(1)[0]
            confidence = count / len(evidence)
            summary = (
                f"Repeated pattern '{pattern}' occurred {len(evidence)} times; "
                f"most common outcome was '{most_common_outcome}'."
            )
            reflection = Reflection(
                summary=summary,
                evidence_memory_ids=[memory.id for memory in evidence],
                confidence=confidence,
                metadata={
                    "pattern": pattern,
                    "outcomes": dict(outcomes),
                },
            )
            self.memory_manager.remember(
                summary,
                MemoryType.LONG_TERM,
                source="reflection_engine",
                importance=min(1.0, 0.7 + confidence * 0.3),
                metadata={
                    **reflection.metadata,
                    "reflection": True,
                    "evidence_memory_ids": reflection.evidence_memory_ids,
                },
            )
            reflections.append(reflection)
        return reflections

    def create_organizational_lesson(
        self,
        summary: str,
        *,
        source: str,
        importance: float = 0.9,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Publish a reviewed lesson to organizational memory."""
        return self.memory_manager.remember(
            summary,
            MemoryType.ORGANIZATIONAL,
            source=source,
            importance=importance,
            metadata={"reviewed": True, **(metadata or {})},
        )

