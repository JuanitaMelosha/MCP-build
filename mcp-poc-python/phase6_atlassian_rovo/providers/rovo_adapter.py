from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from oauth.atlassian_oauth import AtlassianOAuthClient, AtlassianOAuthConfig
from oauth.token_store import OAuthToken, TokenStore

logger = logging.getLogger("phase6.rovo_adapter")


@dataclass(frozen=True)
class Workspace:
    """One Atlassian cloud site returned by accessible-resources."""

    id: str
    name: str
    url: str
    scopes: list[str]


@dataclass(frozen=True)
class AdapterTool:
    """A gateway-friendly tool exposed by the REST compatibility adapter."""

    name: str
    description: str


@dataclass(frozen=True)
class AdapterResource:
    """A gateway-friendly Confluence page resource."""

    uri: str
    name: str
    description: str


class RovoAdapter:
    """Atlassian ecosystem adapter backed by official Jira and Confluence REST APIs.

    The name reflects the learning platform's Rovo integration boundary. This class
    does not claim to call an undocumented native Rovo MCP endpoint.
    """

    name = "rovo"

    def __init__(
        self,
        config: AtlassianOAuthConfig,
        token_store: TokenStore,
        default_cloud_id: str | None = None,
    ) -> None:
        self.config = config
        self.token_store = token_store
        self.oauth_client = AtlassianOAuthClient(config)
        self.default_cloud_id = default_cloud_id

    async def authenticate(self) -> OAuthToken:
        """Return a valid token, refreshing it when necessary."""
        token = self.token_store.load()
        if token is None:
            raise RuntimeError("No Atlassian token found. Run examples/login_rovo.py first.")
        if not token.is_expired():
            return token
        if not token.refresh_token:
            raise RuntimeError("Atlassian token expired and no refresh token is available.")

        try:
            refreshed = await self.oauth_client.refresh(token.refresh_token)
        except Exception as exc:
            raise RuntimeError(f"Atlassian token refresh failed: {exc}") from exc

        # Atlassian uses rotating refresh tokens. Always save the newest response.
        self.token_store.save(refreshed)
        logger.info("atlassian_token_refreshed")
        return refreshed

    async def discover_workspaces(self) -> list[Workspace]:
        """Discover Atlassian cloud sites available to the OAuth token."""
        data = await self._request(
            "GET",
            self.config.accessible_resources_url,
            include_cloud_id=False,
        )
        return [
            Workspace(
                id=item["id"],
                name=item.get("name", item["id"]),
                url=item.get("url", ""),
                scopes=list(item.get("scopes", [])),
            )
            for item in data
        ]

    async def discover_projects(self, cloud_id: str | None = None) -> list[dict[str, Any]]:
        """List Jira projects visible to the authenticated user."""
        data = await self._request(
            "GET",
            self._jira_url(cloud_id, "/rest/api/3/project/search"),
            params={"maxResults": 50},
        )
        return list(data.get("values", []))

    async def discover_resources(
        self,
        cloud_id: str | None = None,
    ) -> list[AdapterResource]:
        """Discover Confluence pages and represent them as gateway resources."""
        pages = await self.list_pages(cloud_id=cloud_id)
        return [
            AdapterResource(
                uri=f"confluence://{self._cloud_id(cloud_id)}/pages/{page['id']}",
                name=page.get("title", page["id"]),
                description=f"Confluence page with status {page.get('status', 'unknown')}",
            )
            for page in pages
        ]

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Route a gateway tool name to an official Jira or Confluence REST call."""
        handlers = {
            "discover_workspaces": self.discover_workspaces,
            "discover_projects": self.discover_projects,
            "create_jira_ticket": self.create_jira_ticket,
            "get_issue": self.get_issue,
            "search_issues": self.search_issues,
            "update_issue": self.update_issue,
            "list_pages": self.list_pages,
            "read_page": self.read_page,
            "search_pages": self.search_pages,
        }
        try:
            handler = handlers[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown Rovo adapter tool: {tool_name}") from exc
        return await handler(**arguments)

    async def list_tools(self) -> list[AdapterTool]:
        """Return the tools exposed through the gateway."""
        return [
            AdapterTool("discover_workspaces", "Discover authorized Atlassian cloud sites."),
            AdapterTool("discover_projects", "Discover Jira projects in a cloud site."),
            AdapterTool("create_jira_ticket", "Create a Jira issue."),
            AdapterTool("get_issue", "Read one Jira issue."),
            AdapterTool("search_issues", "Search Jira issues with JQL."),
            AdapterTool("update_issue", "Update Jira issue fields."),
            AdapterTool("list_pages", "List Confluence pages."),
            AdapterTool("read_page", "Read a Confluence page."),
            AdapterTool("search_pages", "Search Confluence pages with CQL."),
        ]

    async def create_jira_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        cloud_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a Jira issue using Atlassian Document Format for description."""
        payload = {
            "fields": {
                "project": self._project_reference(project_key),
                "summary": summary,
                "description": self._adf_text(description),
                "issuetype": {"name": issue_type},
            }
        }
        return await self._request(
            "POST",
            self._jira_url(cloud_id, "/rest/api/3/issue"),
            json=payload,
        )

    async def get_issue(
        self,
        issue_key: str,
        cloud_id: str | None = None,
    ) -> dict[str, Any]:
        """Read one Jira issue by key or id."""
        return await self._request(
            "GET",
            self._jira_url(cloud_id, f"/rest/api/3/issue/{issue_key}"),
            params={"fields": "summary,status,issuetype,priority,description"},
        )

    async def search_issues(
        self,
        jql: str,
        cloud_id: str | None = None,
        max_results: int = 20,
    ) -> dict[str, Any]:
        """Search Jira issues with JQL."""
        return await self._request(
            "GET",
            self._jira_url(cloud_id, "/rest/api/3/search/jql"),
            params={
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,issuetype,priority",
            },
        )

    async def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any],
        cloud_id: str | None = None,
    ) -> dict[str, Any]:
        """Update Jira issue fields."""
        await self._request(
            "PUT",
            self._jira_url(cloud_id, f"/rest/api/3/issue/{issue_key}"),
            json={"fields": fields},
            expect_empty=True,
        )
        return {"issue_key": issue_key, "status": "Updated"}

    async def list_pages(
        self,
        cloud_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """List Confluence pages visible to the user."""
        data = await self._request(
            "GET",
            self._confluence_url(cloud_id, "/wiki/api/v2/pages"),
            params={"limit": limit},
        )
        return list(data.get("results", []))

    async def read_page(
        self,
        page_id: str,
        cloud_id: str | None = None,
    ) -> dict[str, Any]:
        """Read a Confluence page including storage-format body."""
        return await self._request(
            "GET",
            self._confluence_url(cloud_id, f"/wiki/api/v2/pages/{page_id}"),
            params={"body-format": "storage"},
        )

    async def search_pages(
        self,
        query: str,
        cloud_id: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Search Confluence pages using CQL."""
        escaped = query.replace('"', '\\"')
        return await self._request(
            "GET",
            self._confluence_url(cloud_id, "/wiki/rest/api/search"),
            params={
                "cql": f'type=page AND text~"{escaped}"',
                "limit": limit,
            },
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        include_cloud_id: bool = True,
        expect_empty: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Send an authenticated Atlassian API request with readable errors."""
        del include_cloud_id  # Documents that accessible-resources has no cloud id.
        token = await self.authenticate()
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
        }
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=headers, **kwargs)

        if response.status_code >= 400:
            raise RuntimeError(self._api_error(response))
        if expect_empty or response.status_code == 204 or not response.content:
            return {}
        return response.json()

    def _cloud_id(self, cloud_id: str | None) -> str:
        """Resolve a supplied cloud id or the configured default."""
        resolved = cloud_id or self.default_cloud_id
        if not resolved:
            raise ValueError(
                "A cloud_id is required. Run discover_workspaces() and set "
                "ATLASSIAN_CLOUD_ID."
            )
        return resolved

    def _jira_url(self, cloud_id: str | None, path: str) -> str:
        """Build an OAuth Jira API URL."""
        return f"https://api.atlassian.com/ex/jira/{self._cloud_id(cloud_id)}{path}"

    def _confluence_url(self, cloud_id: str | None, path: str) -> str:
        """Build an OAuth Confluence API URL."""
        return (
            f"https://api.atlassian.com/ex/confluence/{self._cloud_id(cloud_id)}{path}"
        )

    def _api_error(self, response: httpx.Response) -> str:
        """Build a beginner-readable Atlassian API error."""
        try:
            payload = response.json()
            detail = (
                payload.get("errorMessages")
                or payload.get("errors")
                or payload.get("message")
                or payload
            )
        except ValueError:
            detail = response.text
        return f"Atlassian API HTTP {response.status_code}: {detail}"

    def _adf_text(self, text: str) -> dict[str, Any]:
        """Convert plain text to a minimal Atlassian Document Format document."""
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }

    def _project_reference(self, project_key_or_id: str) -> dict[str, str]:
        """Build Jira's project reference from a project key or numeric id."""
        value = project_key_or_id.strip()
        if not value:
            raise ValueError("Jira project key or id cannot be empty.")
        if value.isdigit():
            return {"id": value}
        return {"key": value.upper()}
