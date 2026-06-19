from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Awaitable, Callable
from typing import Any

from events.event_bus import Event


class WebhookValidationError(ValueError):
    """Raised when a webhook body or signature is invalid."""


class WebhookHandler:
    """Normalize GitHub, Jira, and Slack webhooks into platform events."""

    def __init__(
        self,
        publisher: Callable[[Event], Awaitable[None]],
        github_secret: str | None = None,
    ) -> None:
        self.publisher = publisher
        self.github_secret = github_secret

    async def process(
        self,
        provider: str,
        headers: dict[str, str],
        body: bytes,
    ) -> Event:
        """Validate, normalize, and publish one webhook."""
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        if provider == "github":
            self._verify_github_signature(normalized_headers, body)

        try:
            payload: dict[str, Any] = json.loads(body)
        except json.JSONDecodeError as exc:
            raise WebhookValidationError("Webhook body must contain valid JSON.") from exc

        event = self._normalize(provider, normalized_headers, payload)
        await self.publisher(event)
        return event

    def _normalize(
        self,
        provider: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> Event:
        """Map provider-specific webhook fields to platform event types."""
        if provider == "github":
            github_event = headers.get("x-github-event")
            if github_event == "pull_request" and payload.get("action") == "opened":
                return Event("github.pr.created", payload, "github.webhook")

        if provider == "jira":
            event_type = {
                "jira:issue_created": "jira.issue.created",
                "jira:issue_updated": "jira.issue.updated",
            }.get(payload.get("webhookEvent"))
            if event_type:
                return Event(event_type, payload, "jira.webhook")

        if provider == "slack" and payload.get("event", {}).get("type") == "message":
            return Event("slack.message.posted", payload, "slack.webhook")

        raise WebhookValidationError(f"Unsupported {provider} webhook event.")

    def _verify_github_signature(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> None:
        """Verify GitHub's X-Hub-Signature-256 when a secret is configured."""
        if self.github_secret is None:
            return
        supplied = headers.get("x-hub-signature-256", "")
        expected = "sha256=" + hmac.new(
            self.github_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(supplied, expected):
            raise WebhookValidationError("Invalid GitHub webhook signature.")
