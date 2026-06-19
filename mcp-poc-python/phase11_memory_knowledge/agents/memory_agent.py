from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from gateway import MCPGateway
from memory.context_builder import ContextBuilder, ContextPackage
from memory.knowledge_graph import KnowledgeGraph
from memory.memory_manager import MemoryManager, MemoryType

logger = logging.getLogger("phase11.memory_agent")


@dataclass(frozen=True)
class AgentResponse:
    """Memory-aware response plus the retrieved context package."""

    response: str
    context: ContextPackage


class MemoryAwareSupportAgent:
    """Retrieve memory before MCP execution and remember results afterward."""

    def __init__(
        self,
        gateway: MCPGateway,
        memory_manager: MemoryManager,
        context_builder: ContextBuilder,
        knowledge_graph: KnowledgeGraph,
    ) -> None:
        self.gateway = gateway
        self.memory_manager = memory_manager
        self.context_builder = context_builder
        self.knowledge_graph = knowledge_graph

    async def handle(self, request: str) -> AgentResponse:
        """Build context, use MCP, update memory, and produce a response."""
        customer_id = self._extract_customer_id(request)
        entity_id = f"customer:{customer_id}"

        self.memory_manager.remember(
            request,
            MemoryType.WORKING,
            source="user",
            importance=0.6,
            metadata={"entity_id": entity_id, "kind": "request"},
        )
        context = self.context_builder.build(request, entity_id=entity_id)
        logger.info("Retrieved context with %s memories", len(context.memories))

        customer = await self.gateway.call_tool(
            "customer.get_customer",
            {"customer_id": customer_id},
        )
        self._remember_customer(customer)

        if "ticket" in request.lower():
            ticket = await self.gateway.call_tool(
                "ticket.create_ticket",
                {
                    "title": f"Memory-aware support request for {customer['name']}",
                    "priority": self._choose_priority(context, customer),
                },
            )
            self._remember_ticket(customer, ticket)
            result = {"customer": customer, "ticket": ticket}
        else:
            result = {"customer": customer}

        response = (
            "Memory-aware agent result:\n"
            f"{json.dumps(result, indent=2)}\n\n"
            "Context used:\n"
            f"{context.rendered}"
        )
        episode_summary = (
            f"Completed support request for customer {customer['id']} "
            f"({customer['name']}, {customer['plan']} plan)."
        )
        if "ticket" in result:
            episode_summary += (
                f" Created ticket {result['ticket']['ticket_id']} with "
                f"status {result['ticket']['status']}."
            )
        self.memory_manager.remember(
            episode_summary,
            MemoryType.SESSION,
            source="memory_agent",
            importance=0.8,
            metadata={
                "entity_id": entity_id,
                "pattern": "customer_support_request",
                "outcome": "completed",
            },
        )
        self.memory_manager.clear_working()
        return AgentResponse(response, context)

    def _remember_customer(self, customer: dict[str, str]) -> None:
        """Store customer facts in memory and graph."""
        entity_id = f"customer:{customer['id']}"
        self.memory_manager.remember(
            f"Customer {customer['id']} is {customer['name']} on the {customer['plan']} plan.",
            MemoryType.LONG_TERM,
            source="customer.get_customer",
            importance=0.85,
            metadata={"entity_id": entity_id, "kind": "customer_profile"},
        )
        self.knowledge_graph.upsert_entity(
            entity_id,
            "customer",
            customer,
        )
        plan_id = f"plan:{customer['plan'].lower()}"
        self.knowledge_graph.upsert_entity(
            plan_id,
            "plan",
            {"name": customer["plan"]},
        )
        self.knowledge_graph.add_relationship(entity_id, "SUBSCRIBED_TO", plan_id)

    def _remember_ticket(
        self,
        customer: dict[str, str],
        ticket: dict[str, str],
    ) -> None:
        """Store ticket facts and customer-ticket relationship."""
        customer_id = f"customer:{customer['id']}"
        ticket_id = f"ticket:{ticket['ticket_id']}"
        self.memory_manager.remember(
            f"Ticket {ticket['ticket_id']} was created for customer {customer['id']} "
            f"with status {ticket['status']}.",
            MemoryType.LONG_TERM,
            source="ticket.create_ticket",
            importance=0.9,
            metadata={
                "entity_id": customer_id,
                "ticket_id": ticket["ticket_id"],
                "pattern": "customer_support_request",
                "outcome": "ticket_created",
            },
        )
        self.knowledge_graph.upsert_entity(ticket_id, "ticket", ticket)
        self.knowledge_graph.add_relationship(customer_id, "HAS_TICKET", ticket_id)

    def _extract_customer_id(self, request: str) -> str:
        """Extract a customer id from the request."""
        match = re.search(r"customer\s+(?:id\s+)?([A-Za-z0-9_-]+)", request, re.IGNORECASE)
        return match.group(1) if match else "123"

    def _choose_priority(
        self,
        context: ContextPackage,
        customer: dict[str, str],
    ) -> str:
        """Use retrieved policy context before falling back to live customer data."""
        if "premium customers receive high-priority support" in context.rendered.lower():
            return "High"
        return "High" if customer["plan"].lower() == "premium" else "Medium"
