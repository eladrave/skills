# Custom Codex Agent Contract

Complete this contract before finalizing the agent bundle. Remove sections that genuinely do not apply. Do not leave placeholders in installed artifacts.

## 1. Identity

- Proposed agent name:
- One-sentence role:
- Scope: personal or project
- Agent TOML target path:
- Companion Skill name and path, if any:

## 2. Selection behavior

### Use this agent when

-

### Do not use this agent when

-

### Positive trigger examples

1.
2.

### Negative trigger examples

1.
2.

### Explicit invocation example

-

## 3. Primary objective

- Primary outcome:
- Definition of done:
- Maximum acceptable uncertainty:

## 4. Inputs

### Required from the parent agent

-

### Discoverable by the subagent

-

### Supported formats and limits

-

### Missing or invalid input behavior

-

## 5. Authority and permissions

- Sandbox mode:
- Approval policy assumptions:
- Writable locations:
- Readable sources:
- Allowed network access:
- Allowed external actions:
- Dependency installation policy:
- Actions requiring approval:
- Prohibited actions:
- Runtime, thread, or resource limits:

## 6. Sources of truth

List sources in priority order.

1.
2.
3.

Conflict-resolution rule:

Evidence requirements:

## 7. Execution architecture

Choose all that apply and justify each.

- Custom agent TOML:
- Companion Skill:
- Skill scripts:
- MCP server:
- Hook:
- Codex SDK or external orchestration:
- `AGENTS.md` changes:

Why simpler mechanisms are insufficient:

## 8. Required workflow

1.
2.
3.

Required Skill invocation:

Required script or tool commands:

Output validation:

Stop conditions:

Return-to-parent conditions:

## 9. Script contract, if applicable

- Script path:
- Runtime and dependencies:
- Required arguments:
- Output location and schema:
- Exit codes:
- Timeout:
- Idempotency:
- Atomic output:
- stderr and logging behavior:
- Failure behavior:

## 10. MCP tool and integration contract, if applicable

- Existing server or new MCP server implementation:
- Server identifier:
- Configuration scope and location:
- Transport: Streamable HTTP or STDIO
- URL, or command, arguments, and working directory:
- Authentication mode:
- OAuth scopes or resource:
- Environment variable names, without secret values:
- Required tools:
- Explicitly denied tools:
- New tool definitions, if any:
- Input and output schema for each tool:
- Read-only, mutating, idempotent, and side-effect classification:
- Default and per-tool approval modes:
- Startup and tool timeouts:
- Required initialization:
- Safe read-only smoke test:
- Approved write smoke test and cleanup, if essential:
- Authentication failure behavior:
- Tool discovery failure behavior:
- Tool call and malformed-output behavior:
- Evidence required before declaring the integration working:

## 11. Hook contract, if applicable

- Event:
- Matcher:
- Command:
- Expected stdin fields:
- Expected stdout or JSON:
- Timeout:
- Failure visibility:
- Why normal sandbox and permissions remain necessary:

## 12. Output contract

Required format:

Required evidence:

Required fields:

How to report no findings:

How to distinguish fact, inference, assumption, and unresolved issue:

## 13. Failure behavior

- Required runtime unavailable:
- Tool unavailable:
- MCP authentication missing or expired:
- MCP server initialization failure:
- Required MCP tool not discovered:
- MCP output malformed or incomplete:
- MCP write partially succeeds or cleanup fails:
- Script nonzero exit:
- Output missing:
- Output malformed:
- Output stale or mismatched:
- Source unavailable:
- Conflicting evidence:
- Permission denied:
- Validation fails:
- User request exceeds scope:

## 14. Quality and validation

- Accuracy criteria:
- Completeness criteria:
- Security criteria:
- Determinism criteria:
- Performance or cost constraints:
- Required commands or tests:
- Acceptance threshold:

## 15. Model and tools

- Inherit parent model: yes or no
- Pinned model, if justified:
- Reasoning effort, if justified:
- Required MCP servers:
- Required MCP tools and allowlists:
- MCP authentication and secret environment variable names:
- Required skills:
- Optional nickname candidates:

## 16. Evaluation cases

- Positive selection:
- Negative selection:
- Boundary violation:
- Missing input:
- Tool unavailable:
- Script required:
- Script must not run:
- Script failure:
- Malformed output:
- Accuracy trap:
- Permission test:
- MCP initialization, if applicable:
- MCP tool discovery and allowlist, if applicable:
- MCP read-only smoke test, if applicable:
- MCP invalid-input test, if applicable:
- MCP write and cleanup test, if applicable:
- Hook event, if applicable:
- Representative real task:
