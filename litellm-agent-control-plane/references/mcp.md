# MCP servers and tools on LACP

## Contents

1. Distinguish the two MCP surfaces
2. Register an external MCP server
3. Configure credentials safely
4. Attach tools to an agent
5. Write MCP-aware instructions
6. Test and troubleshoot

## Distinguish the two MCP surfaces

| Surface | Inventory | Blueprint field | Purpose |
|---|---|---|---|
| Registered integration MCP | `mcp_servers` from `/v1/mcp/server` | `mcp_server_ids` | External services such as browsers, mail, issue trackers, or data systems |
| LACP platform MCP | `platform_tools` from `/api/platform-mcps` | `platform_mcp_ids` | LACP-native operations such as sub-agent runs, approvals, agent memory, or skill editing |

Never put a platform tool ID in `mcp_server_ids`, and never register
`run_sub_agent` as an external MCP server. When `sub_agents` is non-empty, LACP
automatically selects the platform list/run tools for the parent.

## Register an external MCP server

Use this sequence; do not attach an untested URL directly to an agent.

1. Obtain the authoritative streamable-HTTP MCP endpoint, transport, auth
   model, required variables/headers, and expected tools from the server owner.
2. Preserve the exact URL, including a required trailing slash. Redirects can
   drop authorization headers and create misleading upstream auth errors.
3. Create a secret-free JSON definition:

```json
{
  "server_name": "example-readonly",
  "description": "Reads approved records from Example.",
  "instructions": "Use for Example record lookup only.",
  "url": "https://mcp.example.com/mcp/",
  "transport": "streamable_http",
  "auth_type": "bearer_token",
  "mcp_info": {
    "variables": [
      {
        "name": "EXAMPLE_TOKEN",
        "description": "Per-user Example access token",
        "scope": "per_user"
      }
    ]
  },
  "static_headers": {
    "Authorization": "Bearer ${EXAMPLE_TOKEN}"
  },
  "allowed_tools": ["search_records", "get_record"],
  "is_byok": true,
  "available_on_public_internet": false,
  "approval_status": "active"
}
```

4. Run `mcp-discover`. The helper prompts invisibly for every `${VARIABLE}` and
   sends the values only for that discovery request.
5. Compare discovered names, descriptions, and input schemas with the intended
   use. Put only necessary exact names in `allowed_tools`. An empty allowlist
   currently permits all exposed tools; do not use it as a deny-all policy.
6. Run `mcp-add` without `--apply`, review the normalized definition and public
   visibility, obtain confirmation, then apply it.
7. Record the returned `server_id`; agent attachment uses this ID, not the
   display name, alias, URL, or a guessed identifier.

The helper supports remote URL-based MCP servers. Configure local command-based
servers through an operator-managed LACP workflow only after verifying that the
selected runtime and deployment topology support them.

## Configure credentials safely

Do not put secret values in the MCP definition, blueprint, skill, rule, agent
instructions, shell arguments, or backup.

- For `per_user` variables, connect the value through the target LACP
  integration/vault flow for the same user ID as the agent owner.
- For a single BYOK credential, use LACP's user-credential connection flow.
- For OAuth, complete LACP's browser-based OAuth start/callback flow and verify
  the intended user/account and scopes.
- For instance-scoped secrets, use the target's protected administrator
  credential flow. The local helper intentionally refuses `credentials`,
  `env`, `env_vars`, and `extra_headers` fields.
- Use the minimum scopes required by the selected allowlisted tools.

After connecting, run `mcp-tools --user-id <agent-owner>`. This verifies the
saved server is active, credentials resolve for that identity, the MCP
initialize/initialized/tools-list handshake succeeds, and the allowlist is
applied.

Templated registered URLs are routed through LACP's dynamic MCP proxy so
variables can be resolved at call time. The instance MCP proxy base URL must be
configured and reachable by the managed runtime.

## Attach tools to an agent

- Add registered server IDs to blueprint `mcp_server_ids`.
- Do not manually add `mcp_toolset` entries. The helper strips stale entries,
  resolves the registered IDs, builds `config.mcp_servers`, and creates matching
  toolsets. LACP drops toolsets whose server name is not in the resolved server
  list.
- Add platform tool IDs to `platform_mcp_ids`. Use only current inventory IDs.
- Attach a server only to agents that need it. A multi-agent parent does not
  need a child's MCP server merely to call that child.
- Keep write-capable servers away from research-only agents. If read and write
  operations share one server, restrict `allowed_tools` and require approval in
  the agent instructions.

## Write MCP-aware instructions

For each attached server, tell the agent:

1. What source or system the server represents.
2. Which tasks justify a tool call.
3. Which tools/actions are allowed and prohibited.
4. Required identifiers, time windows, filters, and source precedence.
5. How to interpret empty, partial, or error responses.
6. Which result fields must be verified before claiming success.
7. Which calls require human approval and how to request/check it.

Example:

```text
Use the Example MCP only for records inside project ACME. Search first, then
retrieve the exact record by returned ID. Treat an empty search as no evidence,
not proof that the record does not exist. Do not call create_record or
delete_record. Preserve the MCP error and stop after one retry on a transient
failure. Cite the record ID and updated_at value in the final output.
```

Tool descriptions help the model choose calls but do not replace an explicit
workflow. Never instruct the agent to invent tool names or arguments; it must
use the schemas exposed by the connected MCP server.

## Test and troubleshoot

Validate in layers:

1. `mcp-discover` succeeds against the raw definition.
2. `mcp-add` returns the intended saved server and visibility.
3. LACP credentials are connected for the exact owner/user.
4. `mcp-tools` returns the expected allowlisted tools.
5. The paused agent can call a read-only tool with a known test record.
6. A disallowed tool is absent or rejected.
7. The agent handles empty output and upstream failure according to its prompt.
8. A write test uses an isolated target, human approval, and independent state
   verification.

Common failures:

| Symptom | Check |
|---|---|
| Redirect or malformed-key error | Exact URL and required trailing slash; redirect may have dropped auth |
| No tools | Server active status, credentials for the requested user, initialize handshake, allowlist names |
| Unresolved `${VAR}` | Variable definition/scope, saved owner value, and MCP proxy base URL |
| Tool attached but unavailable | `mcp_server_ids`, resolved `config.mcp_servers`, matching toolset name, runtime support |
| Parent says success but work missing | Parent tool result and child/tool session status, not parent completion alone |
| Unexpected write capability | Empty/overbroad `allowed_tools`, excessive scopes, or server attached to the wrong agent |
