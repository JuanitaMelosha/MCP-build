from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Observation:
    """The recorded result of one executed agent step."""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass
class AgentMemory:
    """In-memory conversation and execution state for one agent runtime."""

    messages: list[dict[str, str]] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        """Remember a user request."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Remember the agent's final response."""
        self.messages.append({"role": "assistant", "content": content})

    def add_observation(self, observation: Observation) -> None:
        """Remember one tool execution result."""
        self.observations.append(observation)

    def latest_result(self, tool_name: str) -> dict[str, Any] | None:
        """Return the most recent result for a specific tool."""
        for observation in reversed(self.observations):
            if observation.tool_name == tool_name:
                return observation.result
        return None

    def clear(self) -> None:
        """Clear all runtime memory."""
        self.messages.clear()
        self.observations.clear()

