from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format logs as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize standard and event-specific logging fields."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for name in ("event_id", "event_type", "attempt", "handler", "metric"):
            value = getattr(record, name, None)
            if value is not None:
                payload[name] = value
        return json.dumps(payload, default=str, sort_keys=True)


def configure_structured_logging() -> None:
    """Configure JSON logs for the autonomous runtime."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("mcp").setLevel(logging.WARNING)

