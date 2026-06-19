from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from autonomous_platform import EventDrivenPlatform, build_platform
from events.logging_utils import configure_structured_logging


@contextmanager
def temporary_platform(
    *,
    github_webhook_secret: str | None = None,
    max_attempts: int = 3,
) -> Iterator[EventDrivenPlatform]:
    """Create an isolated platform with temporary event files."""
    configure_structured_logging()
    with tempfile.TemporaryDirectory() as directory:
        yield build_platform(
            Path(directory),
            github_webhook_secret=github_webhook_secret,
            max_attempts=max_attempts,
        )
