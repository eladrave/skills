# Capability Selection Guide

Choose the mechanism based on who decides when code runs, how strongly typed the interface must be, and where orchestration lives.

| Question | Agent TOML | Skill | Skill script | MCP | Hook | Codex SDK |
|---|---:|---:|---:|---:|---:|---:|
| Defines a specialized delegated role | Yes | No | No | No | No | Can |
| Adds reusable instructions | Limited | Yes | Yes | Tool docs only | No | Can |
| Runs local deterministic code | Model chooses shell | Model chooses | Model chooses | Tool call | Lifecycle chooses | Program chooses |
| Runs automatically on lifecycle event | No | No | No | No | Yes | Program controls |
| Provides a typed callable interface | No | No | CLI contract | Yes | Event JSON | Program API |
| Best for a remote shared service | No | No | Usually no | Yes | No | Can |
| Best for complete orchestration | No | No | No | Partial | No | Yes |

## Decision sequence

1. Is the requirement mainly a specialized role, permissions profile, or delegation target?
   - Create a custom agent TOML.
2. Is there a reusable procedure, domain method, reference set, or command sequence?
   - Add a companion Skill.
3. Does part of the task require deterministic local computation or parsing?
   - Put a tested script under the Skill's `scripts/` directory.
4. Must the capability be a typed tool, remote service, shared integration, or authenticated API?
   - Use MCP.
   - If the tool already exists, configure and validate the server.
   - If the user is defining a new tool, implement an MCP server first. Agent TOML cannot define a new tool schema by itself.
5. Must code run because a lifecycle event happened, independent of model choice?
   - Use a hook.
6. Does an external program need to control sessions, state, handoffs, CI/CD, or the entire workflow?
   - Use the Codex SDK, App Server, non-interactive mode, or Codex as an MCP server.

## Common combinations

### Reviewer

```text
Custom agent TOML, read-only
+ optional review methodology Skill
```

### Dataset analyst

```text
Custom agent TOML, workspace-write or read-only as needed
+ companion Skill
+ deterministic Python analyzer
+ JSON output schema
```

### Documentation researcher

```text
Custom agent TOML, read-only
+ official-docs MCP server
+ optional citation methodology Skill
```

### Policy-enforced implementation agent

```text
Custom agent TOML
+ implementation Skill
+ PreToolUse or PostToolUse hooks
+ normal sandbox and approval controls
```

### CI/CD multi-agent pipeline

```text
Codex SDK or Agents SDK orchestrator
+ Codex MCP server or Codex SDK sessions
+ custom agents or instruction profiles
+ trace and evaluation system
```

## Reliability rule

Use model instructions for judgment. Use code for deterministic transformations and validation. Use MCP for formal reusable tools. Use hooks for lifecycle automation. Use SDK orchestration when an external program must own control flow.


## MCP-specific decision

Use an existing MCP server when it already exposes the required narrow tools and authentication model. Implement a new MCP server when the user needs a new typed tool contract, shared remote capability, service-side authorization, or reusable integration.

For an existing server, collect transport, URL or command, authentication method, environment variable names, OAuth scopes, exact tool allowlist, approval policy, timeouts, and a safe smoke test.

For a new server, define every tool's name, description, input schema, output schema, side effects, idempotency, authorization, errors, timeouts, and test cases before choosing a framework. Avoid generic command-execution tools.

Configuration is not validation. A working MCP integration requires Codex initialization, spawned-agent tool discovery, a real safe tool call, output validation, and error-path testing.
