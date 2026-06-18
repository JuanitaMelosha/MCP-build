from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import build_gateway, configure_logging, required_env


async def main() -> None:
    configure_logging()
    try:
        project_key = required_env("ATLASSIAN_JIRA_PROJECT_KEY")
        result = await build_gateway().call_tool(
            "rovo.search_issues",
            {
                "jql": f'project = "{project_key}" ORDER BY created DESC',
                "max_results": 10,
            },
        )
    except Exception as exc:
        print(f"Jira issue search failed: {exc}")
        return

    print("Recent Jira issues:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
