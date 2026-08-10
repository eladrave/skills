# LACP REST and portable backup reference

## Agent blueprint

Use this local blueprint shape. It is translated into existing LACP
`POST /api/agents` and `PATCH /api/agents/{id}` requests.

```json
{
  "agents": [
    {
      "ref": "researcher",
      "name": "Researcher",
      "owner_id": "local-user",
      "description": "Collects source-backed evidence.",
      "runtime": "configured-runtime-alias",
      "model": "available-model-id",
      "system": "Complete, self-contained operating instructions.",
      "tools": [{"type": "bash"}],
      "mcp_server_ids": ["mcp_server_id"],
      "skill_ids": ["skill_id"],
      "rule_ids": ["rule_id"],
      "vault_keys": ["KEY_NAME"],
      "max_runtime_minutes": 30,
      "on_failure": "pause_and_notify",
      "sub_agents": []
    },
    {
      "ref": "orchestrator",
      "name": "Research Orchestrator",
      "owner_id": "local-user",
      "runtime": "configured-runtime-alias",
      "model": "available-model-id",
      "system": "Delegate evidence collection, verify results, and synthesize the answer.",
      "sub_agents": ["researcher"]
    }
  ]
}
```

Rules:

- Make every `ref` unique within the blueprint.
- Require `name`, `owner_id`, `runtime`, `model`, and a non-empty `system`.
- Use only IDs returned by `inventory`.
- Put integration IDs in `mcp_server_ids`; do not author `mcp_toolset` entries.
- Put symbolic agent refs, not IDs, in `sub_agents`.
- Agents are created paused. Activation is a separate operator decision.

## Existing API resources used

| Resource | Read | Write during create/restore |
|---|---|---|
| Models | `GET /v1/models` | none |
| Runtime harnesses | `GET /api/runtime-harnesses` | not restored without secrets |
| Built-in runtimes | `GET /api/agent-runtimes` | not restored without secrets |
| Agents | `GET/POST /api/agents` | `POST`, then `PATCH` for relationships |
| Skills | `GET/POST /api/skills` | `POST` |
| Rules | `GET/POST /api/rules` | `POST` |
| Routines | `GET/POST /api/routines` | `POST` |
| Memory | `GET/POST /api/agents/{id}/memory` | `POST` |
| Files | `GET/PUT /api/agents/{id}/files/{path}` | `PUT` |
| MCP definitions | `GET/POST /v1/mcp/server` | sanitized `POST` |
| MCP proxy setting | `GET/PUT /v1/mcp/settings/proxy-base-url` | optional `PUT` |
| Providers | `GET /api/providers` | secrets must be re-entered |
| Vault | key-name list endpoints | values must be re-entered |

## Portable backup boundary

The JSON archive is integrity-checked and written with owner-only permissions.
It is intentionally portable across LACP instances and therefore does not
contain database IDs that must be preserved. Restore creates new resources and
rewrites these references:

1. MCP server IDs.
2. Skill and rule IDs.
3. Agent IDs and `config.sub_agents` links.
4. Routine agent IDs.
5. Agent MCP server names, URLs, and toolset server names.

The archive contains prompts, rules, memory, and file content. Treat it as
sensitive and encrypt it before copying it through an untrusted medium.

## Non-exportable prerequisites

REST responses deliberately do not expose provider/runtime API keys or vault
values. MCP credentials and inline authorization values are redacted by the
helper. Restore reports the names and metadata needed for an operator to
re-enter them.

Static agents loaded from server configuration can be represented in the
archive, but REST restore turns them into paused database-backed managed agents.
For an exact server-level recovery including configuration files, encryption
keys, sessions, event history, and secrets, use the LACP deployment's database,
environment, and persistent-state backup procedure instead.
