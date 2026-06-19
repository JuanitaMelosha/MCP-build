from __future__ import annotations

from dataclasses import dataclass

from memory.knowledge_graph import GraphFact, KnowledgeGraph
from memory.memory_manager import (
    MemoryManager,
    MemoryRecord,
    MemoryType,
    ScoredMemory,
)
from memory.vector_store import VectorStore


@dataclass(frozen=True)
class ContextPackage:
    """Dynamically assembled context suitable for an LLM or agent."""

    query: str
    memories: list[ScoredMemory]
    graph_facts: list[GraphFact]
    timeline: list[MemoryRecord]
    rendered: str


class ContextBuilder:
    """Retrieve, score, and assemble memory and knowledge context."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        vector_store: VectorStore,
        knowledge_graph: KnowledgeGraph,
    ) -> None:
        self.memory_manager = memory_manager
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph

    def refresh_index(self) -> int:
        """Rebuild the local vector index from all memory scopes."""
        memories = self.memory_manager.all_memories()
        self.vector_store.clear()
        self.vector_store.index_many(memories)
        return len(memories)

    def build(
        self,
        query: str,
        *,
        entity_id: str | None = None,
        memory_limit: int = 5,
        graph_depth: int = 2,
        timeline_limit: int = 10,
    ) -> ContextPackage:
        """Run the full memory retrieval pipeline."""
        self.refresh_index()
        candidates = self.vector_store.search(
            query,
            limit=max(memory_limit * 3, memory_limit),
        )
        scored = sorted(
            [
                self.memory_manager.score(item.memory, item.similarity)
                for item in candidates
            ],
            key=lambda item: item.score,
            reverse=True,
        )[:memory_limit]

        facts = (
            self.knowledge_graph.related(entity_id, max_depth=graph_depth)
            if entity_id and entity_id in self.knowledge_graph.entities
            else []
        )
        timeline = self.memory_manager.build_timeline(
            entity_id=entity_id,
            limit=timeline_limit,
        )
        rendered = self._render(query, scored, facts, timeline)
        return ContextPackage(query, scored, facts, timeline, rendered)

    def organizational_context(self, query: str, limit: int = 5) -> list[ScoredMemory]:
        """Retrieve only organizational memories for all-agent knowledge."""
        organizational = self.memory_manager.all_memories(
            {MemoryType.ORGANIZATIONAL}
        )
        temporary = VectorStore(self.vector_store.embedding_model)
        temporary.index_many(organizational)
        return sorted(
            [
                self.memory_manager.score(result.memory, result.similarity)
                for result in temporary.search(query, limit=limit)
            ],
            key=lambda item: item.score,
            reverse=True,
        )

    def _render(
        self,
        query: str,
        memories: list[ScoredMemory],
        facts: list[GraphFact],
        timeline: list[MemoryRecord],
    ) -> str:
        """Render a bounded, labeled context block."""
        sections = [f"QUERY\n{query}"]

        if memories:
            sections.append(
                "RELEVANT MEMORIES\n"
                + "\n".join(
                    f"- [{item.memory.memory_type}] {item.memory.content} "
                    f"(score={item.score:.3f})"
                    for item in memories
                )
            )

        if facts:
            sections.append(
                "KNOWLEDGE GRAPH\n"
                + "\n".join(f"- {fact.sentence()}" for fact in facts)
            )

        if timeline:
            sections.append(
                "TIMELINE\n"
                + "\n".join(
                    f"- {memory.created_at}: {memory.content}" for memory in timeline
                )
            )

        return "\n\n".join(sections)
