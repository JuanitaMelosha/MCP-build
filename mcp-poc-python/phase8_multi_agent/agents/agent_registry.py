from __future__ import annotations

from typing import Protocol

from agents.shared_memory import SharedMemory


class Agent(Protocol):
    """Interface implemented by every specialist agent."""

    name: str

    async def run(self, memory: SharedMemory) -> None:
        """Perform the agent's workflow responsibility."""


class AgentRegistry:
    """Register and retrieve specialist agents by name."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Register one agent."""
        if agent.name in self._agents:
            raise ValueError(f"Agent already registered: {agent.name}")
        self._agents[agent.name] = agent

    def remove(self, name: str) -> None:
        """Remove an agent."""
        self._agents.pop(name, None)

    def get(self, name: str) -> Agent:
        """Return one registered agent."""
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"Agent is not registered: {name}") from exc

    def list_agents(self) -> list[str]:
        """Return registered agent names."""
        return sorted(self._agents)

