---
name: lacp-agent-builder
description: Design, create, test, back up, and restore reliable agents on a remote LiteLLM Agent Control Plane (LACP) through its existing REST API. Use when a user wants to configure an LACP connection; turn a goal into accurate agent instructions; choose a runtime, model, tools, skills, rules, memory, or schedule; decide between one agent and an orchestrator with specialists; register, discover, restrict, attach, or troubleshoot MCP servers and platform MCP tools; validate an agent workflow; or migrate agents and settings between LACP instances.
---

# LACP Agent Builder

Use `scripts/lacp_client.py` for LACP requests. Do not print, paste into chat,
or place an LACP key or integration credential in a repository or command
argument. Do not install this skill or change LACP server code unless the user
separately requests it.

## Connect and inspect

1. Run `python3 scripts/lacp_client.py status --profile <profile>`.
2. If missing, ask for the LACP URL and run
   `python3 scripts/lacp_client.py configure --profile <profile> --url <url>`.
   Let the helper collect the key with a hidden terminal prompt.
3. Use `default` unless the user names a profile. Use distinct source and target
   profiles for migration.
4. Run `python3 scripts/lacp_client.py inventory --profile <profile>` before
   designing anything. Use only returned runtimes, models, tools, agent IDs,
   MCP server IDs, platform MCP IDs, skill IDs, and rule IDs.
5. Treat authentication failure, an unreachable URL, or an unsupported API as
   a blocker. Never guess live capabilities or IDs.

The helper accepts any key the target accepts. Recommend the master key when
administrative inventory, MCP registration, backup, or restore is required.
Warn that it is powerful and that the local profile file is sensitive.

## Design before creating

1. Read `references/agent-design.md` for every create or redesign request.
2. Convert the goal into an operating contract: outcome, inputs, allowed scope,
   workflow, tool policy, output contract, completion test, failure behavior,
   approvals, and explicit prohibitions.
3. Default to one agent. Read `references/multi-agent.md` before recommending
   specialists or an orchestrator. Split only at boundaries that have distinct
   expertise, tools, permissions, context, or independently verifiable output.
4. Read `references/mcp.md` before registering, attaching, or prompting for an
   integration or platform MCP tool.
5. Select the least-capable connected runtime, model, tools, MCP servers,
   skills, rules, and vault keys that can satisfy the contract. Do not attach a
   tool merely because it is available.
6. Draft the complete instructions and acceptance cases before writing the
   blueprint. Show the user the proposed topology, permissions, side effects,
   and unresolved prerequisites.

## Create and validate

1. Build a JSON blueprint from `references/lacp-api.md`. Use symbolic `ref`
   values for sub-agent relationships and real inventory IDs everywhere else.
2. Run `python3 scripts/lacp_client.py create --profile <profile> --spec <file>`
   without `--apply`.
3. Review the normalized result against the quality gate in
   `references/agent-design.md` and, for a parent/child design, the contracts in
   `references/multi-agent.md`. Correct the blueprint rather than dismissing a
   mismatch as a future prompt problem.
4. Ask for explicit confirmation, then rerun with `--apply`. The helper creates
   every agent paused, resolves real child IDs, and patches parents afterward.
5. Run safe acceptance cases while paused or in an isolated test context. Test
   tool discovery, read-only work, denied/out-of-scope requests, missing input,
   an upstream failure, and approval behavior before enabling delivery tools or
   schedules.
6. Retrieve the parent and every child. Report IDs, topology, attachments,
   acceptance results, limitations, and prerequisites. A successful parent run
   is not evidence that each child or MCP tool succeeded.

## Register and attach MCP servers

Follow `references/mcp.md` in order: define, discover, restrict, register,
connect credentials in LACP, verify the saved server, attach it, teach the agent
when to use it, and run an end-to-end acceptance case.

- Discover without saving:
  `python3 scripts/lacp_client.py mcp-discover --profile <profile> --spec <file>`
- Preview registration:
  `python3 scripts/lacp_client.py mcp-add --profile <profile> --spec <file>`
- Register after confirmation: add `--apply`.
- Verify a saved server:
  `python3 scripts/lacp_client.py mcp-tools --profile <profile> --server-id <id> --user-id <owner>`
- Attach registered integrations through blueprint `mcp_server_ids` only.
- Attach LACP platform tools through `platform_mcp_ids` only. Sub-agent links
  automatically enable the platform list/run tools.

The helper refuses credential-bearing MCP definition fields and prompts hidden
for temporary discovery variables. Configure instance, per-user, or OAuth
credentials through the target LACP credential flow; never save them in an MCP
JSON spec.

## Back up and restore

1. Explain that this is a sensitive, portable API backup, not a PostgreSQL or
   host backup. Choose a new output path outside a public repository.
2. Back up with
   `python3 scripts/lacp_client.py backup --profile <source> --output <path>`.
3. Report counts, checksum, warnings, and secrets that must be re-entered.
4. Configure and verify a separate target profile.
5. Dry-run with
   `python3 scripts/lacp_client.py restore --profile <target> --input <path>`.
6. Review prerequisites and conflicts, obtain explicit confirmation, then add
   `--apply`. Keep agents and routines paused unless the user explicitly asks
   for `--restore-status`.
7. Use `--conflict skip` only to preserve matching target objects and
   `--conflict rename` only when duplicates are acceptable. Never delete to
   resolve a conflict.
8. Use `--restore-instance-settings` only after verifying the source MCP proxy
   URL is correct for the target.

The archive includes REST-exportable agents, skills, rules, routines, memory,
files, sanitized MCP definitions, metadata, vault-key names, and the MCP proxy
setting. It excludes credentials, OAuth tokens, provider/runtime secrets,
vault values, sessions, run history, approvals, inbox items, and encryption
keys. Read `references/lacp-api.md` for the complete boundary.

## Non-negotiable safety

- Require confirmation before `create --apply`, `mcp-add --apply`, or
  `restore --apply`.
- Never overwrite a backup without explicit approval for `--force`.
- Preserve `mcp_server_ids` as the source of truth for integration attachment;
  never author or retain stale `mcp_toolset` entries.
- Use `platform_mcp_ids` only for LACP's built-in platform tools.
- Keep agents, routines, external-delivery tools, and schedules paused until
  credentials and acceptance tests pass.
- Require a human approval boundary for sends, publishes, purchases, deletes,
  permission changes, or other irreversible external effects.
- Never claim success from configuration, HTTP status, or parent completion
  alone; verify the observable result and every relevant child/tool outcome.
