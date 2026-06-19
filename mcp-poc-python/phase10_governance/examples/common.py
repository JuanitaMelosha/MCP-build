from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from governance_platform import GovernancePlatform, build_platform


@contextmanager
def temporary_platform() -> Iterator[GovernancePlatform]:
    """Create an isolated governance platform for one example."""
    with tempfile.TemporaryDirectory() as directory:
        yield build_platform(Path(directory))

