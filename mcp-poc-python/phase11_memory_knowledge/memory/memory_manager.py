from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class MemoryType(StrEnum):
    """Memory scopes used by the agent platform."""

    WORKING = "working"
    SESSION = "session"
    LONG_TERM = "long_term"
    ORGANIZATIONAL = "organizational"


@dataclass(frozen=True)
class MemoryRecord:
    """One piece of remembered information."""

    content: str
    memory_type: MemoryType
    source: str
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_accessed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    access_count: int = 0

    def with_access(self) -> "MemoryRecord":
        """Return a copy updated for one retrieval."""
        return MemoryRecord(
            id=self.id,
            content=self.content,
            memory_type=self.memory_type,
            source=self.source,
            importance=self.importance,
            metadata=self.metadata,
            created_at=self.created_at,
            last_accessed_at=datetime.now(UTC).isoformat(),
            access_count=self.access_count + 1,
        )


@dataclass(frozen=True)
class ScoredMemory:
    """Memory plus retrieval score and score explanation."""

    memory: MemoryRecord
    score: float
    semantic_score: float
    recency_score: float
    importance_score: float


class MemoryManager:
    """Manage working, session, long-term, and organizational memory."""

    def __init__(
        self,
        long_term_path: Path,
        organizational_path: Path,
    ) -> None:
        self.long_term_path = long_term_path
        self.organizational_path = organizational_path
        self.long_term_path.parent.mkdir(parents=True, exist_ok=True)
        self.organizational_path.parent.mkdir(parents=True, exist_ok=True)
        self._working: list[MemoryRecord] = []
        self._session: list[MemoryRecord] = []

    def remember(
        self,
        content: str,
        memory_type: MemoryType,
        *,
        source: str,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Store information in the selected memory scope."""
        record = MemoryRecord(
            content=content,
            memory_type=memory_type,
            source=source,
            importance=max(0.0, min(1.0, importance)),
            metadata=metadata or {},
        )
        if memory_type == MemoryType.WORKING:
            self._working.append(record)
        elif memory_type == MemoryType.SESSION:
            self._session.append(record)
        elif memory_type == MemoryType.LONG_TERM:
            self._append(self.long_term_path, record)
        elif memory_type == MemoryType.ORGANIZATIONAL:
            self._append(self.organizational_path, record)
        return record

    def all_memories(
        self,
        memory_types: set[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """Return memories from selected or all scopes."""
        selected = memory_types or set(MemoryType)
        memories: list[MemoryRecord] = []
        if MemoryType.WORKING in selected:
            memories.extend(self._working)
        if MemoryType.SESSION in selected:
            memories.extend(self._session)
        if MemoryType.LONG_TERM in selected:
            memories.extend(self._read(self.long_term_path))
        if MemoryType.ORGANIZATIONAL in selected:
            memories.extend(self._read(self.organizational_path))
        return memories

    def score(
        self,
        memory: MemoryRecord,
        semantic_score: float,
        *,
        now: datetime | None = None,
    ) -> ScoredMemory:
        """Combine semantic relevance, recency, and importance."""
        current = now or datetime.now(UTC)
        created = datetime.fromisoformat(memory.created_at)
        age_days = max(0.0, (current - created).total_seconds() / 86400)
        recency = math.exp(-age_days / 30)
        score = (semantic_score * 0.6) + (recency * 0.2) + (memory.importance * 0.2)
        return ScoredMemory(
            memory=memory,
            score=score,
            semantic_score=semantic_score,
            recency_score=recency,
            importance_score=memory.importance,
        )

    def build_timeline(
        self,
        *,
        entity_id: str | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        """Build a chronological timeline, optionally filtered by entity id."""
        memories = self.all_memories()
        if entity_id is not None:
            memories = [
                memory
                for memory in memories
                if memory.metadata.get("entity_id") == entity_id
                or entity_id.lower() in memory.content.lower()
            ]
        return sorted(memories, key=lambda memory: memory.created_at)[-limit:]

    def promote_session_memory(self, minimum_importance: float = 0.7) -> int:
        """Promote important session memories into long-term memory."""
        promoted = 0
        for memory in self._session:
            if memory.importance < minimum_importance:
                continue
            self.remember(
                memory.content,
                MemoryType.LONG_TERM,
                source=f"promotion:{memory.source}",
                importance=memory.importance,
                metadata=memory.metadata,
            )
            promoted += 1
        return promoted

    def clear_working(self) -> None:
        """Clear short-lived working memory."""
        self._working.clear()

    def clear_session(self) -> None:
        """Clear the current session."""
        self._session.clear()

    def _append(self, path: Path, record: MemoryRecord) -> None:
        """Append one persistent memory as JSONL."""
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(record), default=str, sort_keys=True) + "\n")

    def _read(self, path: Path) -> list[MemoryRecord]:
        """Read persistent memories."""
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as file:
            memories: list[MemoryRecord] = []
            for line in file:
                if not line.strip():
                    continue
                data = json.loads(line)
                memories.append(
                    MemoryRecord(
                        **{
                            **data,
                            "memory_type": MemoryType(data["memory_type"]),
                        }
                    )
                )
            return memories
