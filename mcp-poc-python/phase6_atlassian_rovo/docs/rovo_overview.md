# Atlassian Rovo, Jira, Confluence, OAuth, and MCP

Research date: June 18, 2026.

This document separates capabilities verified in official Atlassian documentation from assumptions that should not be made.

## What Is Atlassian Rovo?

Rovo is Atlassian's AI product family for finding organizational knowledge, assisting users, and building agents across Atlassian products and connected data sources.

Atlassian's official Rovo page currently presents these product capabilities:

- Search
- Chat
- Studio
- Agents
- Connectors to Atlassian and third-party SaaS applications

Atlassian states that Rovo availability is tied to eligible Jira, Confluence, Jira Service Management, or Teamwork Collection cloud plans, with some rollout conditions.

Rovo is related to Jira and Confluence, but it is not the same thing as their public REST APIs:

- Jira REST APIs expose Jira projects, issues, fields, workflows, and related data.
- Confluence REST APIs expose spaces, pages, content, and search.
- Rovo provides AI search, chat, agents, and connected knowledge experiences.
- The Atlassian Rovo MCP Server connects approved AI clients to Atlassian capabilities using MCP.

## Officially Verified Capabilities

The following capabilities are supported by official Atlassian developer documentation:

### OAuth 2.0 (3LO)

Atlassian supports OAuth 2.0 authorization-code grants, called 3LO.

An external application can:

1. Redirect a user to Atlassian consent.
2. Receive an authorization code.
3. Exchange the code for an access token.
4. Request Jira and Confluence APIs on the user's behalf.
5. Request `offline_access` and use rotating refresh tokens.

### Accessible Resource Discovery

After OAuth login, an application can call:

```text
GET https://api.atlassian.com/oauth/token/accessible-resources
```

The response identifies Atlassian cloud sites the token can access. Atlassian calls these resources; this lab presents them as workspaces/sites.

### Jira Cloud APIs

Official Jira Cloud APIs support:

- Discovering projects
- Creating issues
- Reading issues
- Searching issues with JQL
- Updating issues

OAuth API calls use the cloud id:

```text
https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/...
```

### Confluence Cloud APIs

Official Confluence APIs support:

- Listing pages
- Reading a page
- Searching content with CQL

OAuth API calls use the cloud id:

```text
https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/...
```

## Rovo MCP Compatibility

Atlassian publicly describes a Rovo MCP Server that uses OAuth and existing permission controls.

However, during this research pass, a stable public Rovo MCP endpoint and a versioned public tool schema could not be verified in Atlassian's official developer API documentation.

Therefore this phase does **not**:

- Hard-code an unverified `mcp.atlassian.com` URL.
- Invent native Rovo MCP tool names.
- Claim Jira REST responses are native MCP resources.
- Claim a custom OAuth app can automatically authenticate to the managed Rovo MCP Server.

Instead, this phase implements:

```text
RovoAdapter
  -> Atlassian OAuth 2.0 (3LO)
  -> Official Jira REST APIs
  -> Official Confluence REST APIs
  -> Gateway-friendly tools and resources
```

`RovoAdapter` is an educational compatibility adapter for the Atlassian ecosystem. Its backend is explicitly REST.

When Atlassian publishes an endpoint and programmatic MCP contract appropriate for custom clients, the adapter can gain a native MCP backend without changing client-facing gateway names.

## Jira Integration Options

### OAuth 2.0 (3LO) REST Integration

Best match for this learning platform:

- Acts on behalf of a user.
- Uses scopes and consent.
- Supports access and refresh tokens.
- Works with official Jira Cloud REST APIs.

### API Tokens

Atlassian documents API tokens for simple scripts and direct REST calls, generally using Basic authentication.

They are not used in this phase because the goal is delegated OAuth access and future vendor integrations.

### Forge

Forge is Atlassian's hosted app platform. Authentication is built into the framework.

Forge is suitable for apps that run inside Atlassian, but this learning platform is an external Python application.

### Connect

Atlassian Connect is another app model. It is not used here.

## Confluence Integration Options

This phase uses:

- Confluence REST API v2 for listing and reading pages.
- Confluence REST API v1 search endpoint for CQL search because the official search API is exposed there.
- OAuth 2.0 bearer tokens through `api.atlassian.com`.

## Authentication Methods

| Method | Official Use | Used Here |
|---|---|---|
| OAuth 2.0 (3LO) | External apps acting for users | Yes |
| API token + Basic auth | Scripts and direct REST calls | No |
| Forge authentication | Forge apps | No |
| Connect authentication | Connect apps | No |
| Managed Rovo MCP OAuth | Approved MCP clients | Documented conceptually; custom endpoint contract not assumed |

## OAuth Requirements

Create an app in the Atlassian developer console:

1. Add OAuth 2.0 (3LO).
2. Set a callback URL.
3. Add Jira and Confluence APIs.
4. Add required scopes.
5. Store client id and secret outside source control.

This lab requests classic scopes for readability:

```text
read:jira-work
write:jira-work
read:jira-user
read:confluence-content.all
search:confluence
offline_access
```

Scopes should be reduced for a production integration.

## Available API Mapping

| Learning Method | Official API |
|---|---|
| `discover_workspaces()` | `GET /oauth/token/accessible-resources` |
| `discover_projects()` | Jira project search |
| `create_jira_ticket()` | Jira create issue |
| `get_issue()` | Jira get issue |
| `search_issues()` | Jira enhanced JQL search |
| `update_issue()` | Jira edit issue |
| `list_pages()` | Confluence v2 pages |
| `read_page()` | Confluence v2 page by id |
| `search_pages()` | Confluence CQL search |

## Permissions

OAuth scopes do not override Jira or Confluence permissions.

The user must already have permission to:

- Browse a Jira project.
- View an issue.
- Create or edit issues.
- View a Confluence space or page.

The API returns only data available to that user.

## Official Sources

- Atlassian Rovo product overview: https://www.atlassian.com/software/rovo
- Atlassian OAuth 2.0 (3LO): https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/
- Jira Cloud REST API: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Jira issue APIs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/
- Confluence page APIs: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/
- Confluence search API: https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/
