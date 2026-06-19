from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agents.memory_agent import MemoryAwareSupportAgent
from gateway import build_gateway
from memory.context_builder import ContextBuilder
from memory.knowledge_graph import KnowledgeGraph
from memory.memory_manager import MemoryManager
from memory.reflection_engine import ReflectionEngine
from memory.vector_store import VectorStore


@dataclass
class MemoryPlatform:
    """All Phase 11 memory, graph, context, reflection, and agent components."""

    manager: MemoryManager
    vectors: VectorStore
    graph: KnowledgeGraph
    context: ContextBuilder
    reflections: ReflectionEngine
    agent: MemoryAwareSupportAgent


def build_platform(data_directory: Path) -> MemoryPlatform:
    """Construct the complete memory-aware MCP agent platform."""
    manager = MemoryManager(
        data_directory / "long_term.jsonl",
        data_directory / "organizational.jsonl",
    )
    vectors = VectorStore()
    graph = KnowledgeGraph(data_directory / "knowledge_graph.json")
    context = ContextBuilder(manager, vectors, graph)
    reflections = ReflectionEngine(manager)
    agent = MemoryAwareSupportAgent(
        build_gateway(),
        manager,
        context,
        graph,
    )
    return MemoryPlatform(manager, vectors, graph, context, reflections, agent)

