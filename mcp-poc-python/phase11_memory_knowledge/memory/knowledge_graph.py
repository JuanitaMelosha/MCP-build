from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Entity:
    """Knowledge graph entity."""

    id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Relationship:
    """Directed relationship between two graph entities."""

    source_id: str
    relation: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphFact:
    """Human-readable graph query result."""

    source: Entity
    relationship: Relationship
    target: Entity

    def sentence(self) -> str:
        """Render the graph fact as readable text."""
        return f"{self.source.id} --{self.relationship.relation}--> {self.target.id}"


class KnowledgeGraph:
    """Small persistent property graph for organizational knowledge."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.entities: dict[str, Entity] = {}
        self.relationships: list[Relationship] = []
        self.load()

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
    ) -> Entity:
        """Create or update an entity."""
        existing = self.entities.get(entity_id)
        combined = dict(existing.properties) if existing else {}
        combined.update(properties or {})
        entity = Entity(entity_id, entity_type, combined)
        self.entities[entity_id] = entity
        self.save()
        return entity

    def add_relationship(
        self,
        source_id: str,
        relation: str,
        target_id: str,
        properties: dict[str, Any] | None = None,
    ) -> Relationship:
        """Create a directed relationship between existing entities."""
        if source_id not in self.entities or target_id not in self.entities:
            raise KeyError("Both relationship entities must exist first.")
        relationship = Relationship(
            source_id,
            relation,
            target_id,
            properties or {},
        )
        if relationship not in self.relationships:
            self.relationships.append(relationship)
            self.save()
        return relationship

    def neighbors(
        self,
        entity_id: str,
        relation: str | None = None,
    ) -> list[GraphFact]:
        """Return outgoing facts for one entity."""
        facts: list[GraphFact] = []
        for relationship in self.relationships:
            if relationship.source_id != entity_id:
                continue
            if relation is not None and relationship.relation != relation:
                continue
            facts.append(
                GraphFact(
                    self.entities[relationship.source_id],
                    relationship,
                    self.entities[relationship.target_id],
                )
            )
        return facts

    def related(
        self,
        entity_id: str,
        max_depth: int = 2,
    ) -> list[GraphFact]:
        """Traverse outgoing relationships breadth-first."""
        visited = {entity_id}
        frontier = [entity_id]
        facts: list[GraphFact] = []
        for _ in range(max_depth):
            next_frontier: list[str] = []
            for current in frontier:
                for fact in self.neighbors(current):
                    facts.append(fact)
                    target_id = fact.target.id
                    if target_id not in visited:
                        visited.add(target_id)
                        next_frontier.append(target_id)
            frontier = next_frontier
            if not frontier:
                break
        return facts

    def find_entities(
        self,
        *,
        entity_type: str | None = None,
        property_name: str | None = None,
        property_value: Any = None,
    ) -> list[Entity]:
        """Find entities by type and optional property."""
        entities = list(self.entities.values())
        if entity_type is not None:
            entities = [entity for entity in entities if entity.type == entity_type]
        if property_name is not None:
            entities = [
                entity
                for entity in entities
                if entity.properties.get(property_name) == property_value
            ]
        return entities

    def save(self) -> None:
        """Persist the graph as JSON."""
        self.path.write_text(
            json.dumps(
                {
                    "entities": [asdict(entity) for entity in self.entities.values()],
                    "relationships": [
                        asdict(relationship) for relationship in self.relationships
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )

    def load(self) -> None:
        """Load graph data when present."""
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        self.entities = {
            item["id"]: Entity(**item) for item in data.get("entities", [])
        }
        self.relationships = [
            Relationship(**item) for item in data.get("relationships", [])
        ]

