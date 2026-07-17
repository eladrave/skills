# MCP Tool and Integration Contract

Use this contract whenever a custom agent will use an MCP server or the user wants to define new formal tools.

A custom-agent TOML can configure MCP servers and select their tools. It cannot implement a new tool by itself. New tools require an MCP server implementation, followed by agent configuration and runtime validation.

## Integration

- Existing server, newly configured server, or new implementation:
- Server identifier:
- User, project, plugin, or agent scope:
- Why MCP is preferable to a Skill script:

## Transport

Choose exactly one:

### Streamable HTTP

- URL:
- HTTPS policy:
- Startup timeout:
- Tool timeout:

### STDIO

- Command:
- Arguments:
- Working directory:
- Runtime and dependencies:

## Authentication and secrets

Choose the applicable mechanism:

- OAuth using stored Codex credentials
- Trusted ChatGPT session authentication
- Bearer token from an environment variable
- HTTP header values from environment variables
- STDIO environment variables
- No authentication

Record environment-variable names and OAuth scopes, never secret values. Never write tokens, passwords, cookies, private keys, or authorization headers into TOML, Skills, scripts, fixtures, logs, or shell history.

## Tool contract

For every required tool define:

- Exact tool name and purpose
- Required and optional input fields
- Output schema
- Read-only or mutating behavior
- Idempotency and side effects
- Required authorization
- Expected errors
- Timeout and retry behavior
- Safe smoke-test input
- Cleanup for write tests

Prefer narrow typed tools. Do not expose a generic command-execution tool unless the user explicitly accepts the risk and no safer design works.

## Exposure and approvals

- Required tool allowlist:
- Explicit deny list:
- Default approval mode:
- Per-tool approval overrides:
- Whether initialization is required:
- Inherited servers to disable:

Expose only what the agent needs.

## Failure behavior

Define behavior for initialization failure, authentication failure, missing scopes, missing tools, timeout, malformed output, partial writes, failed cleanup, and parent permission blocks. Required MCP dependencies must fail closed. The agent must not fabricate a result or silently substitute an unapproved source.

## Validation runbook

### A. Static configuration

1. Parse TOML with a real parser.
2. Confirm exactly one transport.
3. Validate authentication fields.
4. Confirm no credentials are embedded.
5. Confirm required environment variables exist without printing values.
6. Confirm STDIO executable, working directory, and dependencies.
7. Confirm HTTP URL and TLS policy.
8. Confirm allowlists, deny lists, approvals, and timeouts.

### B. Codex initialization

1. Configure the server in the intended layer.
2. Complete OAuth using `codex mcp login <server-name>` when applicable.
3. Inspect `codex mcp list` or `/mcp`.
4. Restart Codex after material changes.
5. Set `required = true` for a hard dependency so startup failure is visible.

A listed server is not proof that the custom agent can use it.

### C. Spawned-agent discovery

1. Explicitly spawn the generated custom agent.
2. Inspect the actual tools visible in its thread.
3. Compare them with the allowlist and deny list.
4. Fail if a required tool is absent or an unnecessary sensitive tool is exposed.

### D. Safe tool tests

1. Call a harmless read-only tool using representative valid input.
2. Verify that a real MCP call occurred.
3. Validate result shape, source identity, and required fields.
4. Test controlled invalid input and confirm a real error without fabricated success.
5. For required mutations, use disposable data, obtain approval, verify the write, and clean it up.

### E. Representative workflow

Run an in-scope task that requires MCP. Confirm the agent chooses the correct tool, validates output before relying on it, handles denial or unavailability according to contract, and includes actual tool evidence in the final response.

Do not call the integration working until all applicable stages pass.

## Evidence record

- Codex client and version:
- Agent path and name:
- MCP configuration location:
- Server and transport:
- Authentication mode:
- Environment-variable names checked:
- Initialization result:
- Discovered tools:
- Smoke-test tool and input:
- Result identity and schema validation:
- Invalid-input result:
- Write and cleanup result:
- Representative workflow result:
- PASS or FAIL:
- Remaining limitations:
