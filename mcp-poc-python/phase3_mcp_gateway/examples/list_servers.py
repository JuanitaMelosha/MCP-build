from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gateway import build_default_gateway


def main() -> None:
    gateway = build_default_gateway()
    print("Gateway server namespaces:")
    for namespace in gateway.list_servers():
        print(f"- {namespace}")


if __name__ == "__main__":
    main()

