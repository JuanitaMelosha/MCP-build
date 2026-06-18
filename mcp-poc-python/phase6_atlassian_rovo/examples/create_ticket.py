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
            "rovo.create_jira_ticket",
            {
                "project_key": project_key,
                "summary": "MCP Learning Lab test issue",
                "description": "Created by the Phase 6 Atlassian OAuth learning example.",
                "issue_type": "Task",
            },
        )
    except Exception as exc:
        print(f"Jira issue creation failed: {exc}")
        return

    print("Jira issue created:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
