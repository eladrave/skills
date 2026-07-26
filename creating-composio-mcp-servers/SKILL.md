---
name: creating-composio-mcp-servers
description: Use when a user wants a coding agent to create, configure, authenticate, verify, or hand off a Composio MCP server for one or more toolkits such as Gmail, GitHub, Slack, Google Calendar, Shopify, or Notion.
---

# Creating Composio MCP Servers

Create a hosted, user-scoped Composio MCP endpoint that the user can connect to ChatGPT or another MCP client. Prefer a Composio session with `mcp: true`, because Composio documents the standalone MCP-server API as deprecated. Support one or multiple toolkits, Composio-managed OAuth, existing or newly created auth configurations, least-privilege tool allowlists, and safe verification.

## Required input

Ask for the following before making Composio mutations:

1. **Toolkit slug(s)**, one or more exact Composio slugs, for example `gmail`, `github`, `slack`, or `googlecalendar`.
2. **Composio project API key**, supplied through a secret prompt, environment variable, or approved secret store. Never echo it, put it in a URL, commit it, write it to source files, or include it in logs.
3. **Stable Composio user ID**, for example `elad-chatgpt`. Do not invent a new ID if the user already has one. Connected accounts and generated MCP URLs are scoped to this identifier.

Ask these optional questions when the answer materially changes the result:

- Server name, otherwise use `<Toolkit> MCP Server` or `Multi-toolkit MCP Server`.
- Tool policy: read-only, selected tools, or full toolkit access. Default to read-only or an explicit allowlist.
- Whether Composio-managed auth is acceptable. Use it by default for development and testing. Use an existing custom auth config when the user requires custom OAuth branding, scopes, credentials, quotas, or an instance-specific endpoint.
- Whether a harmless read-only action should be executed during verification.

If toolkit slugs are missing, the API key is missing, or the user ID is missing, ask only for the missing values. Do not create partial resources merely to discover what the user meant.

## Secret handling

- Prefer `COMPOSIO_API_KEY` in the runtime environment or a secure secret input. Run shell commands with tracing disabled, such as `set +x`.
- Never request a Google, Microsoft, GitHub, or other provider password, OTP, OAuth authorization code, access token, or refresh token in chat.
- Use Composio Connect Links for user authorization. The user completes the provider login in the hosted flow.
- Never append the Composio API key to the MCP URL. Configure it as the `x-api-key` header in the MCP client when that client supports static headers.
- Redact secrets from errors and diagnostic output. If the user pasted an API key into chat, recommend rotating it after setup.

## Workflow

### 1. Normalize and validate the request

- Normalize toolkit names to the exact Composio slugs. If a name is ambiguous, query the toolkit catalog or ask the user.
- Deduplicate toolkit slugs while preserving the requested order.
- Validate the server name against Composio's constraints: 4 to 30 characters, using alphanumeric characters, spaces, and hyphens.
- Keep the user ID stable across auth links, connected accounts, generated URLs, and future server generations.

### 2. Inspect tools and existing auth configurations

Use the Composio API or SDK. The current REST base URL is `https://backend.composio.dev` and project authentication uses the `x-api-key` header.

For each toolkit:

```http
GET /api/v3.1/auth_configs?toolkit_slug=<toolkit>&limit=50
GET /api/v3.1/tools?toolkit_slug=<toolkit>&limit=50
```

Reuse an enabled auth config only when its toolkit matches and its restrictions satisfy the requested tool policy. If several candidates are suitable and the choice affects scopes, branding, or credentials, ask the user to choose. Do not silently select a custom auth config with unknown scope.

Inspect the tool metadata, especially `slug`, `tags`, `is_deprecated`, and scopes. For a read-only default, prefer tools tagged `readOnlyHint`, exclude deprecated tools, and exclude tools tagged `destructiveHint`, `createHint`, or `updateHint`.

### 3. Create missing managed auth configurations

For a toolkit without a suitable auth config, create a Composio-managed OAuth config unless the user requested custom auth:

```http
POST /api/v3.1/auth_configs
x-api-key: <secret header>
Content-Type: application/json

{
  "toolkit": {"slug": "gmail"},
  "auth_config": {
    "type": "use_composio_managed_auth",
    "name": "Gmail MCP",
    "restrict_to_following_tools": ["GMAIL_FETCH_EMAILS"]
  }
}
```

Record only the returned auth config ID, toolkit slug, status, auth scheme, and tool restrictions. Never record credential fields. Create one auth config per toolkit as needed. Do not create duplicate configs when an appropriate enabled config already exists.

If the toolkit uses an API key, bearer token, or basic auth, use the toolkit's supported Composio connection flow. Do not ask the user to place provider credentials in the MCP server URL or source code.

### 4. Choose session or standalone server mode

Use this decision:

| Request | Mode |
|---|---|
| User wants an MCP endpoint to use in ChatGPT or another client | Session-backed MCP, preferred |
| User explicitly requests a persistent Composio server object, server ID, or standalone MCP configuration | Standalone server API |
| User asks for one or multiple toolkits but does not specify the implementation | Session-backed MCP with explicit toolkit and tool filters |

Composio's current recommendation is to create a session with `mcp: true`, then use `session.mcp.url` and `session.mcp.headers`. Create the final session after required accounts are connected. If the SDK creates a session before authorization is complete, retain the session ID, complete the Connect Link flow, then resume the same session. A direct-tools preset makes the endpoint expose exactly the selected tools and removes dynamic search/meta tools:

```python
from composio import Composio, SESSION_PRESET_DIRECT_TOOLS

composio = Composio(api_key=COMPOSIO_API_KEY)
session = composio.sessions.create(
    user_id=USER_ID,
    toolkits=["gmail", "googlecalendar"],
    tools={
        "gmail": {"enable": ["GMAIL_FETCH_EMAILS"]},
        "googlecalendar": {"enable": ["GOOGLECALENDAR_EVENTS_LIST"]},
    },
    session_preset=SESSION_PRESET_DIRECT_TOOLS,
    mcp=True,
    sandbox={"enable": False},
)

mcp_url = session.mcp.url
mcp_headers = session.mcp.headers
```

Use the exact headers returned by `session.mcp.headers`. Do not assume the header is always `x-api-key`, and never reconstruct the endpoint or append a secret to it. For a session using custom auth configs, pass `auth_configs={"gmail": "ac_..."}` and the equivalent mapping for each toolkit. For an existing connected account, pass `connected_accounts={"gmail": ["ca_..."]}` when account selection matters.

If the user requests dynamic tool discovery instead of a fixed tool list, omit the direct-tools preset but still restrict the session to the requested toolkit slugs. Disable the sandbox unless the user explicitly needs Composio remote code execution.

### 5. Create a standalone server only when requested

The standalone MCP API is deprecated, but remains available for explicit server-management requirements. Use the fixed server endpoint for one toolkit when the auth config IDs and allowed tools are already resolved:

```http
POST /api/v3.1/mcp/servers
```

Use the custom server endpoint for multiple toolkits:

```http
POST /api/v3.1/mcp/servers/custom
```

For both endpoints, include the name, auth config IDs, and explicit allowed tools. For the custom endpoint also include the toolkit slugs. Set Composio-managed authentication when using managed auth.

Example multi-toolkit request:

```json
{
  "name": "Gmail and Calendar MCP",
  "auth_config_ids": ["ac_gmail123", "ac_calendar456"],
  "toolkits": ["gmail", "googlecalendar"],
  "allowed_tools": [
    "GMAIL_FETCH_EMAILS",
    "GMAIL_LIST_THREADS",
    "GOOGLECALENDAR_EVENTS_LIST"
  ],
  "managed_auth_via_composio": true
}
```

Do not omit `allowed_tools` unless the user explicitly requests every available tool. An all-tools server can expose sending, deletion, account changes, and other irreversible actions.

### 6. Manage standalone servers

These CRUD operations apply only to persistent standalone MCP server objects. They do not apply to session-backed MCP endpoints. For a session, store the session ID and resume it with the SDK, or create a new session when the toolkit or tool filters need to change.

Use the Composio SDK when available:

```python
servers = composio.mcp.list(limit=20)
server = composio.mcp.get(server_id)
updated = composio.mcp.update(
    server_id=server_id,
    name="Updated Gmail MCP",
    allowed_tools=["GMAIL_FETCH_EMAILS"],
)
result = composio.mcp.delete(server_id)
```

Use these REST operations when direct API calls are required:

#### List servers

```http
GET /api/v3.1/mcp/servers?name=<optional-name>&toolkits=gmail,slack&auth_config_ids=ac_123&page_no=1&limit=20
```

Use the returned pagination fields and continue through all pages when the user asks for all servers. Filter by exact IDs or toolkit slugs when locating a specific resource. Do not choose a server solely by a partial name if multiple results match.

#### Get server details

```http
GET /api/v3.1/mcp/<server-id>
```

Confirm the returned ID matches the requested resource before relying on its name, toolkits, auth config IDs, allowed tools, or connection URL.

#### Update a server

```http
PATCH /api/v3.1/mcp/<server-id>
Content-Type: application/json

{
  "name": "Updated Gmail MCP",
  "allowed_tools": ["GMAIL_FETCH_EMAILS"],
  "toolkits": ["gmail"]
}
```

Updates are partial. Send only fields the user asked to change. Re-fetch the server afterward and verify that the resulting toolkits and allowlist are correct. If an update removes tools or changes auth configurations, warn about the impact before executing it.

#### Delete a server

```http
DELETE /api/v3.1/mcp/<server-id>
```

Deletion is a destructive external action. Before deleting, resolve the exact server ID, show the server name and toolkits, and obtain explicit user confirmation unless the user already explicitly requested deletion of that exact server. Composio documents this as a soft delete that makes the server unavailable, and connected clients lose access. Verify the response reports `deleted: true` and do not delete auth configurations or connected accounts unless separately requested.

### 7. Create user connections

For every toolkit that is not already connected for the requested user ID, create a Connect Link before creating the final session or generating the standalone URL:

```http
POST /api/v3.1/connected_accounts/link
x-api-key: <secret header>
Content-Type: application/json

{
  "auth_config_id": "ac_gmail123",
  "user_id": "elad-chatgpt",
  "alias": "Elad Gmail MCP"
}
```

Return the `redirect_url` to the user and tell them to complete the provider authorization. Do not attempt to enter credentials or OTPs on their behalf. Preserve the same user ID in every link. If a connection already exists and is enabled, do not create another one.

After authorization, verify the connected account is active for the requested toolkit and user. If authorization is incomplete, stop before generating a final tested handoff and report the exact missing connection.

### 8. Generate the URL or read it from the session

For session mode, read `session.mcp.url` and `session.mcp.headers` after the required accounts are connected. For standalone mode, after the server exists and the required accounts are connected, generate the URL:

```http
POST /api/v3.1/mcp/servers/generate
x-api-key: <secret header>
Content-Type: application/json

{
  "mcp_server_id": "<server-id>",
  "managed_auth_by_composio": true,
  "user_ids": ["elad-chatgpt"]
}
```

Use the returned session or generation response exactly as returned. Do not reconstruct it from memory or remove query parameters. The returned headers are part of the connection contract and must be preserved with the URL.

### 9. Verify safely

Verify, in order:

1. For session mode, confirm the session configuration and the returned `session.mcp` URL and headers. For standalone mode, retrieve the server and confirm its name, toolkit list, auth config IDs, and allowed tools.
2. Confirm each required connected account is active and belongs to the requested user ID.
3. Send MCP initialization and `tools/list` requests using the exact URL and headers returned by the session or generation API.
4. Confirm the returned tool set matches the requested allowlist and contains no deprecated or unintended destructive tools.
5. If the user explicitly requested a functional test, execute one harmless read-only tool. Do not send email, delete or modify data, create records, or change settings as part of verification.

If any verification step fails, diagnose the exact layer: invalid API key, missing auth config, incomplete OAuth, wrong user ID, server configuration mismatch, unsupported client authentication, or MCP protocol failure. Do not create duplicate servers as a blind retry.

## ChatGPT handoff

Return all values needed to connect the result:

- Server or session name and ID, when available
- Toolkit slugs
- User ID
- Generated MCP endpoint
- Exact authentication headers required by the session or standalone server, with values redacted
- The fact that secret values are intentionally omitted from the output
- Connected-account status
- Allowed tools and whether they are read-only
- Verification results and any remaining user action

ChatGPT connects to remote MCP servers. In ChatGPT, use the custom app or Developer Mode flow available to the user's plan and workspace, provide the generated endpoint, configure the exact returned authentication headers or supported OAuth mechanism, scan the tools, and create or publish the app as permitted by the workspace. Current OpenAI documentation says Pro supports custom MCP apps with read/fetch permissions in Developer Mode, while full write/modify MCP support is available to Business and Enterprise/Edu plans. Verify current availability if the user requests write actions.

Do not claim that the server is usable in ChatGPT until the endpoint, authentication method, tool scan, and required account authorization have been verified.

## Quick reference

| Need | REST operation |
|---|---|
| List auth configs | `GET /api/v3.1/auth_configs` |
| List toolkit tools | `GET /api/v3.1/tools` |
| Create managed auth config | `POST /api/v3.1/auth_configs` |
| Create session-backed MCP endpoint | `composio.sessions.create(..., mcp=True)` or `composio.create(..., {mcp: true})` |
| Create one-toolkit standalone server | `POST /api/v3.1/mcp/servers` |
| Create multi-toolkit standalone server | `POST /api/v3.1/mcp/servers/custom` |
| List standalone servers | `GET /api/v3.1/mcp/servers` |
| Get standalone server details | `GET /api/v3.1/mcp/{id}` |
| Update standalone server | `PATCH /api/v3.1/mcp/{id}` |
| Delete standalone server | `DELETE /api/v3.1/mcp/{id}` |
| Create OAuth/API connection link | `POST /api/v3.1/connected_accounts/link` |
| Generate standalone user-scoped URL | `POST /api/v3.1/mcp/servers/generate` |
| Inspect server | `GET /api/v3.1/mcp/{id}` |

## Common mistakes

| Mistake | Correct response |
|---|---|
| Use a display name instead of a toolkit slug | Resolve the exact slug first, such as `gmail`. |
| Use the deprecated standalone API for every request | Prefer a session-backed MCP endpoint unless the user explicitly requests a standalone server object. |
| Create a server with no auth config | Reuse or create a suitable auth config for every toolkit. |
| Use one user ID for creation and another for generation | Preserve one stable user ID throughout the workflow. |
| Put a secret in the URL or assume one fixed header | Use the exact headers returned by `session.mcp.headers` or the standalone API contract. |
| Ask the user for provider passwords or OAuth codes | Generate a Composio Connect Link and let the user authorize it. |
| Expose every Gmail or Slack action by default | Start with read-only tools or an explicit allowlist. |
| Test by sending or deleting data | Verify protocol metadata and use only a harmless read-only action. |
| Recreate resources after a timeout | Query by ID or list existing resources first, then retry idempotently. |
| Report the generic server URL as the final user endpoint | Return the exact user-scoped URL from the generation response. |

## Authoritative references

When API behavior may have changed, consult the current official Composio documentation before acting:

- [Single Toolkit MCP](https://docs.composio.dev/docs/single-toolkit-mcp)
- [Using sessions via MCP](https://docs.composio.dev/docs/sessions-via-mcp)
- [Configuring sessions](https://docs.composio.dev/docs/configuring-sessions)
- [MCP API reference](https://docs.composio.dev/reference/api-reference/mcp)
- [Auth Configs API](https://docs.composio.dev/reference/api-reference/auth-configs)
- [Connected Accounts API](https://docs.composio.dev/reference/api-reference/connected-accounts)
- [OpenAI MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt)
