---
name: lacp-agent-builder
description: Design, create, back up, and restore agents on a remote LiteLLM Agent Control Plane (LACP) through its existing REST API. Use when a user asks Codex to create one or more LACP agents, choose between a single agent and an orchestrator with specialists, inspect an LACP installation, make a portable backup of agents and settings, or restore that backup to a new or updated LACP instance.
---

# LACP Agent Builder

Use the bundled `scripts/lacp_client.py` for every LACP request. Do not print,
paste into chat, or place an LACP key in a repository or command argument.

## Connect

1. Run `python3 scripts/lacp_client.py status --profile <profile>`.
2. If the profile is missing, ask for the LACP URL, then run
   `python3 scripts/lacp_client.py configure --profile <profile> --url <url>`.
   Let the script collect the key with its hidden terminal prompt.
3. Use `default` unless the user names a profile. For migration, use distinct
   source and target profiles.
4. Treat authentication failure, an unreachable URL, or an unsupported API as
   a blocker. Never guess live models, runtimes, integrations, or IDs.

The v1 helper accepts any key the target LACP accepts. Recommend the master key
when full discovery or backup is required because some current administrative
inventory endpoints require it. Warn that this is a powerful credential and
that the local profile file is sensitive.

## Design and create agents

1. Run `python3 scripts/lacp_client.py inventory --profile <profile>` and use
   only returned models, runtimes, MCP server IDs, skill IDs, and rule IDs.
2. Ask for the goal and only material missing constraints: success criteria,
   repository or data scope, integrations, schedule and timezone, external
   side effects, approvals, runtime limit, and failure behavior.
3. Default to one agent. Recommend multiple specialists only for separable
   work, distinct tools or permissions, useful parallelism, or reusable roles.
   Add an orchestrator only when the deployed LACP system must coordinate those
   specialists after this Codex conversation ends.
4. Prepare a JSON blueprint using `references/lacp-api.md`. Use symbolic `ref`
   values for sub-agent links; never invent LACP agent IDs.
5. Run `python3 scripts/lacp_client.py create --profile <profile> --spec <file>`
   without `--apply`. Show the normalized plan and ask for confirmation.
6. After confirmation, rerun with `--apply`. The helper creates all agents
   paused, resolves real child IDs, and patches orchestrators afterward.
7. Retrieve the created agents and report their IDs, topology, attached
   resources, and any prerequisites still requiring operator setup.

## Back up an LACP instance

1. Explain that this is a portable API backup, not a PostgreSQL or host backup.
   It contains agent prompts, memory, and files and is sensitive even though
   credential values are excluded.
2. Choose a new output path outside a public repository.
3. Run:

   `python3 scripts/lacp_client.py backup --profile <source> --output <path>`

4. Report counts, warnings, the archive checksum, and every prerequisite whose
   secret must be re-entered on restore. Never display archive contents unless
   the user explicitly requests a particular non-secret field.

The backup includes REST-exportable agents, skills, rules, routines, agent
memory and files, sanitized MCP definitions, model/provider/runtime metadata,
vault-key names, and the MCP proxy setting. It excludes API keys, provider and
runtime secrets, vault values, OAuth tokens, session/run history, approvals,
inbox items, and server encryption keys.

## Restore a backup

1. Configure a separate target profile and verify that it identifies the
   intended LACP instance.
2. Run a dry-run first:

   `python3 scripts/lacp_client.py restore --profile <target> --input <path>`

3. Review missing secrets, runtime/provider prerequisites, name conflicts, and
   counts with the user. Default conflict policy is `fail`.
4. Ask for explicit confirmation immediately before applying the restore.
5. Apply with `--apply`. Use `--conflict skip` only when the user wants to keep
   matching target objects. Use `--conflict rename` only when duplicates are
   acceptable.
6. Keep restored agents and routines paused by default. Use `--restore-status`
   only when the user explicitly wants source activation state restored.
7. Do not restore the source MCP proxy URL by default because it is
   instance-specific. Use `--restore-instance-settings` only after verifying
   the value is correct for the target.
8. Report old-to-new ID mappings, restored counts, skipped objects, warnings,
   and secrets or connections that still require manual configuration.

## Safety rules

- Require confirmation before `create --apply` or `restore --apply`.
- Never overwrite a backup unless the user explicitly approves `--force`.
- Never use deletion to resolve a restore conflict.
- Never claim a portable backup contains credentials or operational history.
- Preserve `mcp_server_ids` as the source for MCP attachments. Let the helper
  strip stale `mcp_toolset` entries and rebuild them from resolved server IDs.
- Create leaf agents before attaching them to orchestrators.
- Keep external-delivery tools and active schedules disabled until their
  credentials and acceptance tests are complete.

Read `references/lacp-api.md` when constructing a blueprint or interpreting a
backup/restore report.
