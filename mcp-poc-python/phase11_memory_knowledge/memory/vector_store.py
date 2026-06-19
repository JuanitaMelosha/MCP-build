from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from memory.memory_manager import MemoryRecord


@dataclass(frozen=True)
class VectorSearchResult:
    """One semantic search result."""

    memory: MemoryRecord
    similarity: float


class LocalEmbeddingModel:
    """Deterministic feature-hashing embedding suitable for a learning lab."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Embed text into a normalized fixed-size vector."""
        vector = [0.0] * self.dimensions
        tokens = self._tokens(text)
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def _tokens(self, text: str) -> list[str]:
        """Create word and adjacent-word features."""
        words = re.findall(r"[a-z0-9]+", text.lower())
        bigrams = [f"{left}_{right}" for left, right in zip(words, words[1:])]
        return words + bigrams


class VectorStore:
    """In-memory vector index for semantic memory retrieval."""

    def __init__(self, embedding_model: LocalEmbeddingModel | None = None) -> None:
        self.embedding_model = embedding_model or LocalEmbeddingModel()
        self._vectors: dict[str, tuple[MemoryRecord, list[float]]] = {}

    def index(self, memory: MemoryRecord) -> None:
        """Add or replace one memory vector."""
        self._vectors[memory.id] = (
            memory,
            self.embedding_model.embed(memory.content),
        )

    def index_many(self, memories: list[MemoryRecord]) -> None:
        """Index many memories."""
        for memory in memories:
            self.index(memory)

    def remove(self, memory_id: str) -> None:
        """Remove one memory from the index."""
        self._vectors.pop(memory_id, None)

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        minimum_similarity: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Return memories ranked by cosine similarity."""
        query_vector = self.embedding_model.embed(query)
        results = [
            VectorSearchResult(memory, self._cosine(query_vector, vector))
            for memory, vector in self._vectors.values()
        ]
        return [
            result
            for result in sorted(results, key=lambda item: item.similarity, reverse=True)
            if result.similarity >= minimum_similarity
        ][:limit]

    def count(self) -> int:
        """Return indexed vector count."""
        return len(self._vectors)

    def clear(self) -> None:
        """Remove all indexed vectors."""
        self._vectors.clear()

    def _cosine(self, left: list[float], right: list[float]) -> float:
        """Calculate cosine similarity for normalized vectors."""
        return sum(a * b for a, b in zip(left, right))
