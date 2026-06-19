from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from memory_platform import MemoryPlatform, build_platform


@contextmanager
def temporary_platform() -> Iterator[MemoryPlatform]:
    """Create an isolated Phase 11 platform."""
    with tempfile.TemporaryDirectory() as directory:
        yield build_platform(Path(directory))


def seed_organizational_memory(platform: MemoryPlatform) -> None:
    """Add sample knowledge shared by all agents."""
    platform.reflections.create_organizational_lesson(
        "Premium customers receive high-priority support and 24x7 coverage.",
        source="support_policy",
        metadata={"topic": "support_policy"},
    )
    platform.reflections.create_organizational_lesson(
        "Never ask a customer for their password or full payment-card number.",
        source="security_policy",
        metadata={"topic": "security"},
    )
    platform.reflections.create_organizational_lesson(
        "Login issues should include account id, observed behavior, and recent changes.",
        source="support_playbook",
        metadata={"topic": "login_issue"},
    )

