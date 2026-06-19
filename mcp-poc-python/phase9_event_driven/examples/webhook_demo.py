from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.common import temporary_platform


async def main() -> None:
    secret = "learning-secret"
    body = json.dumps(
        {
            "action": "opened",
            "number": 77,
            "pull_request": {"title": "Webhook-driven MCP workflow"},
        }
    ).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    with temporary_platform(github_webhook_secret=secret) as platform:
        event = await platform.webhooks.process(
            "github",
            {
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
            },
            body,
        )
        await platform.runtime.run_until_idle()

        print(f"Webhook normalized to: {event.type}")
        print(platform.reporting_agent.reports[-1])


if __name__ == "__main__":
    asyncio.run(main())
