from __future__ import annotations

from gateway import ToolInfo


class ToolSelector:
    """Select tools by matching an intent to dynamically discovered metadata."""

    INTENT_TO_TOOL = {
        "get_customer": "customer.get_customer",
        "get_weather": "weather.get_weather",
        "create_ticket": "ticket.create_ticket",
    }

    def select(self, intent: str, available_tools: list[ToolInfo]) -> ToolInfo:
        """Return the discovered tool that satisfies an intent."""
        desired_name = self.INTENT_TO_TOOL.get(intent)
        if desired_name is None:
            raise ValueError(f"Unsupported intent: {intent}")

        for tool in available_tools:
            if tool.name == desired_name:
                return tool

        available_names = ", ".join(tool.name for tool in available_tools)
        raise LookupError(
            f"Required tool '{desired_name}' was not discovered. Available tools: "
            f"{available_names}"
        )

