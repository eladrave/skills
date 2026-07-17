---
name: creating-codex-custom-subagents
description: Use when a user wants to design, create, install, refine, evaluate, troubleshoot, or extend a reusable custom Codex subagent, including agents that use skills, scripts, hooks, MCP servers, or programmatic orchestration.
---

# Creating Codex Custom Subagents

## Purpose

Guide the user from an idea to a narrow, installed, validated, and behaviorally tested custom Codex subagent.

A custom Codex subagent is a spawned Codex session configured by TOML. The TOML is configuration, not a Python class, constructor, lifecycle object, or executable entry point.

Personal agents belong in:

```text
~/.codex/agents/<agent-name>.toml
```

Project agents belong in:

```text
<repository>/.codex/agents/<agent-name>.toml
```

Every agent TOML must define:

```toml
name = "agent_name"
description = "When Codex should use this agent."
developer_instructions = """
The agent's operating instructions.
"""
```

Do not invent fields such as `entrypoint = "agent.py"`. A subagent can run Python through normal Codex shell tools when permissions and the runtime allow it.

## Core rules

1. Give each agent one clear job.
2. Separate role configuration from deterministic implementation.
3. Use the smallest mechanism that satisfies the requirement.
4. Define positive triggers, negative triggers, and explicit non-goals.
5. Apply least privilege to sandbox, writable paths, tools, and external actions.
6. Prefer inherited model settings unless evaluation justifies pinning.
7. Never embed credentials in TOML, Skills, scripts, hooks, fixtures, or logs.
8. Validate syntax before runtime tests.
9. Test behavior, permissions, failure paths, and agent selection.
10. Never call the agent operational until a fresh Codex session has spawned it and the required behavior has been observed.

## Select the correct mechanism

| Requirement | Mechanism |
|---|---|
| Specialized delegated role, instructions, model, or permission profile | Custom agent TOML |
| Reusable procedure, methodology, references, or command sequence | Companion Skill |
| Deterministic local Python or another utility chosen by the model | Skill with `scripts/` |
| Typed callable tool, external service, authenticated API, or shared remote capability | MCP server |
| Code that must run automatically on a lifecycle event | Hook |
| External application, CI/CD, stateful orchestration, or complete control flow | Codex SDK, App Server, non-interactive mode, or Codex as MCP server |
| Repository-wide conventions | `AGENTS.md` |
| One temporary independent task | Direct subagent delegation |

A common bundle is:

```text
.codex/agents/<agent>.toml
.agents/skills/<skill>/SKILL.md
.agents/skills/<skill>/scripts/<tool>.py
```

Add MCP, hooks, or SDK orchestration only when required.

Read `references/capability-selection.md` before selecting architecture for scripts, MCP, hooks, or external orchestration.

## Operating modes

### Guided mode

Use when material requirements are missing. Ask one focused question at a time only when the answer changes the design and cannot be discovered from the repository or current Codex configuration.

### Fast mode

Use when role, scope, inputs, outputs, tools, permissions, and architecture are already clear. State material assumptions, create the artifacts, and validate them.

### Audit mode

Use when an agent bundle already exists. Read the actual files, identify concrete weaknesses, preserve deliberate behavior, make focused changes, and rerun validation and behavioral tests.

## Phase 1: inspect the environment

Before creating files:

1. Determine personal or project scope.
2. Inspect existing agents under `~/.codex/agents/` and `.codex/agents/`.
3. Inspect user and project `config.toml`.
4. Inspect applicable `AGENTS.md` files.
5. Inspect available Skills, MCP servers, hooks, project runtimes, tests, and commands.
6. Check for name collisions, including built-ins such as `default`, `worker`, and `explorer`.
7. Determine writable boundaries and approval restrictions.
8. Verify current Codex documentation or installed schema for version-sensitive fields.

Do not expose secret values found during inspection.

## Phase 2: build the Agent Contract

Use `references/agent-requirements-template.md` for complex agents.

Define:

- Snake-case agent name and one-sentence role
- Personal or project installation path
- Positive and negative selection examples
- Primary objective and observable definition of done
- Required parent inputs and discoverable inputs
- Supported formats, identifiers, repositories, and limits
- Missing-input and invalid-input behavior
- Sandbox, writable paths, network use, side effects, approvals, and prohibited actions
- Sources of truth and conflict priority
- Ordered workflow, validation, stop conditions, and parent handoff
- Output structure and evidence requirements
- Failure behavior
- Accuracy, security, determinism, cost, and performance criteria
- Evaluation cases

Do not write the TOML until the material contract is resolved.

## Phase 3: tools and MCP

The user may require an existing MCP server or define new tools.

### Existing MCP server

Collect:

- Server identifier and configuration scope
- Streamable HTTP or STDIO transport
- URL, or command, arguments, working directory, and runtime
- Authentication mode
- OAuth scopes and resource when applicable
- Environment-variable names, never secret values
- Exact required tools and explicitly denied tools
- Input and output schema for required tools
- Side effects, idempotency, authorization, approvals, and timeouts
- Safe read-only smoke test
- Disposable write test and cleanup when mutation is essential

Use `references/mcp-tool-and-integration-contract.md`.

### New tool

Agent TOML cannot implement a new tool. When the user defines a new formal tool:

1. Define the tool contract first.
2. Choose an MCP server language and framework appropriate to the project.
3. Implement narrow typed tools.
4. Add authentication and service-side authorization.
5. Add unit, schema, error, integration, and security tests.
6. Configure the generated agent to connect to the server.
7. Expose only the required tools.
8. Validate through a spawned agent.

Use a Skill script instead of MCP when the capability is a local deterministic helper that does not need a formal reusable tool interface.

### MCP hard gate

Do not report an MCP-enabled agent as working until all applicable stages pass:

1. TOML parses and static validation passes.
2. Required credentials are available without printing them.
3. OAuth or other authentication completes.
4. A fresh Codex session initializes the server.
5. The spawned agent sees exactly the expected tools.
6. A real harmless read-only tool call succeeds.
7. Output identity and schema are validated.
8. Invalid input produces a real error without fabricated success.
9. Required write tests use disposable data, approval, verification, and cleanup.

`codex mcp list` or `/mcp` alone is not proof.

## Phase 4: scripts

When deterministic Python or another local utility is needed:

1. Put it under the companion Skill's `scripts/` directory.
2. Define its contract using `references/python-tool-contract.md`.
3. Use argument arrays, not unsafe shell interpolation.
4. Validate paths and untrusted input.
5. Produce structured output with a schema version and input identity.
6. Use meaningful exit codes and stderr diagnostics.
7. Avoid writing outside approved roots.
8. Add tests for success, invalid input, malformed output, stale output, spaces, special characters, injection-like input, timeout, and large input.
9. Require the agent to check exit status and validate output before relying on it.

Do not add a Python `entrypoint` to the agent TOML.

## Phase 5: write the agent TOML

Use `references/custom-agent-template.toml`.

Required fields:

```toml
name = "focused_agent"
description = "Use for specific in-scope work. Do not use for nearby excluded work."
developer_instructions = """
Detailed operating instructions.
"""
```

Recommended instruction sections:

- Role
- Primary objective
- Scope
- Non-goals
- Required inputs
- Sources of truth
- Required Skill and tools
- Workflow
- Verification
- Output contract
- Failure and escalation

Use `sandbox_mode = "read-only"` for review, research, and audit roles unless writes are genuinely required.

When a companion Skill is mandatory, explicitly require it in `developer_instructions`. Enabling a Skill does not prove the model will invoke it.

For MCP:

```toml
[mcp_servers.example]
url = "https://example.com/mcp"
bearer_token_env_var = "EXAMPLE_MCP_TOKEN"
required = true
enabled_tools = ["read_item", "search_items"]
default_tools_approval_mode = "auto"
startup_timeout_sec = 20
tool_timeout_sec = 45

[mcp_servers.example.tools.create_item]
approval_mode = "prompt"
```

Never embed tokens or authorization headers.

## Phase 6: hooks

Use hooks only when execution must happen because a lifecycle event occurred, independent of model choice. Define event, matcher, command, input JSON, output contract, timeout, and failure visibility. See `references/subagent-hook-template.toml`.

Hooks are guardrails, not a complete security boundary. Preserve sandboxing, approvals, filesystem restrictions, and service authorization.

## Phase 7: static validation

Run:

```bash
python3 <generator-skill>/scripts/validate_agent.py /path/to/agent.toml --strict
python3 <generator-skill>/scripts/validate_skill.py /path/to/companion-skill --strict
python3 <generator-skill>/scripts/validate_mcp.py /path/to/agent.toml --check-environment --strict
```

Also run Python compilation and the generated project's tests.

Treat validators as guardrails, not proof of operation.

## Phase 8: runtime and behavioral evaluation

Use a fresh Codex session after installation or material configuration changes.

At minimum test:

1. Positive selection
2. Negative selection
3. Explicit spawn
4. Scope boundary
5. Missing input
6. Accuracy trap
7. Permission boundary
8. Required tool unavailable
9. Output contract
10. Representative real task

For scripts also test nonzero exit, missing output, malformed output, stale output, unsupported input, path safety, injection-like input, timeout, and large input.

For MCP also test authentication, initialization, discovered tool allowlist, safe read call, invalid input, output validation, missing authentication, approval behavior, unavailable server, and write cleanup where applicable.

Inspect the spawned subagent thread with `/agent` when available. Verify actual commands and tool calls, not only the parent summary.

Record prompt, expectation, observed behavior, evidence, pass or fail, root cause, and minimal correction. Use `references/evaluation-matrix.md`.

## Phase 9: refine

When a test fails:

1. Identify the root cause before editing.
2. Change the smallest instruction, script, schema, matcher, tool policy, or permission that fixes the failure.
3. Rerun static validation.
4. Rerun the failed test.
5. Rerun at least one positive case, negative selection, permission test, and representative regression case.

Avoid one-off prompt patches that overfit a single test.

## Completion report

Report:

1. Agent name and purpose
2. Installation paths
3. Architecture selected
4. Scope, permissions, model behavior, Skills, scripts, MCP servers, tools, and hooks
5. Files created or changed
6. Static validation commands and results
7. Script, MCP, hook, and runtime tests
8. Behavioral evaluation results
9. Known limitations
10. Reliable invocation prompts
11. Rollback instructions

Distinguish these states accurately:

- Created
- Parsed successfully
- Companion Skill validated
- Scripts compiled
- Script tests passed
- MCP authenticated and initialized
- MCP tool discovered and called
- Discovered by Codex
- Spawned successfully
- Behaviorally validated

Never collapse them into a generic claim that the agent works.

## Common mistakes

- Treating TOML as executable Python
- Inventing `entrypoint`
- Creating a broad super-agent
- Putting workflow details in the description instead of selection criteria
- Omitting non-goals
- Granting write access to a reviewer
- Pinning a model without evidence
- Embedding secrets
- Assuming enabled Skills are always invoked
- Assuming MCP configuration proves connectivity
- Exposing every tool from a broad MCP server
- Calling a shell script a formal typed tool
- Testing only the happy path
- Claiming success without spawning and inspecting the agent

## Package references

- `references/agent-requirements-template.md`
- `references/capability-selection.md`
- `references/custom-agent-template.toml`
- `references/companion-skill-template.md`
- `references/python-tool-contract.md`
- `references/mcp-tool-and-integration-contract.md`
- `references/subagent-hook-template.toml`
- `references/evaluation-matrix.md`
- `scripts/validate_agent.py`
- `scripts/validate_mcp.py`
- `scripts/validate_skill.py`
