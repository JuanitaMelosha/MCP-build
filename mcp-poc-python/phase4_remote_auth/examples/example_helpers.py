from __future__ import annotations

import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def running_remote_server() -> object:
    """Start the remote MCP server for one example and stop it afterwards."""
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "secure_customer_server.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_health()
        yield
    finally:
        process.terminate()
        process.wait(timeout=5)


def wait_for_health() -> None:
    """Wait until the demo remote server is accepting HTTP requests."""
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with urlopen("http://127.0.0.1:8765/health", timeout=0.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Remote MCP server did not start in time.")

