# SharedKnowledgeLibrary

A single canonical Google Drive tree for durable general knowledge shared across ChatGPT, Codex, Codex CLI, and other authorized agents.

## Canonical storage

Google Drive:

`ChatGPT Library`

Folder ID:

`1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

As of 2026-08-16, the existing folders below have been moved under that root without changing their Drive IDs:

- `Medical records` → `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa` → `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

They are normal canonical subtrees of SharedKnowledgeLibrary.

## Separate operational library

Google Drive `Codex` remains outside this tree.

Its purpose is credentials, infrastructure, deployment and recovery runbooks, private connection details, and other operational agent memory.

Do not merge or mirror `Codex` into SharedKnowledgeLibrary.

## Architecture

```text
Google Drive
│
├── ChatGPT Library/                 CANONICAL GENERAL KNOWLEDGE
│   ├── Medical records/
│   ├── Cynapsa/
│   ├── Memories/
│   ├── Personal/
│   ├── Projects/
│   ├── ...
│   ├── _LIBRARY_POLICY.md
│   └── _sync/                       OPTIONAL
│       └── _shared_library_manifest.json
│
└── Codex/                           CANONICAL OPERATIONAL KNOWLEDGE
    ├── credentials
    ├── infrastructure
    ├── deployment runbooks
    └── operational instructions

ChatGPT native Library
    = immediate access + cache/mirror + optional ingress
    ≠ canonical authority
```

## Important: the skill does not require a sync job

`SharedKnowledgeLibrary` is designed to work correctly on a fresh ChatGPT installation with no scheduled tasks.

Normal operation without any reconciliation job:

```text
User/agent needs durable shared knowledge
        ↓
read/write Google Drive / ChatGPT Library directly
        ↓
canonical result is immediately available to other authorized agents
```

If the user says `save this to my Library`, the active skill saves directly to canonical Drive. It must not postpone the write because a future sync may or may not exist.

A scheduled reconciliation task is only **catch-up insurance** for cases such as:

- a file uploaded in an unrelated ChatGPT conversation;
- a ChatGPT-generated artifact automatically retained in native Library;
- content created when SharedKnowledgeLibrary was not active;
- maintaining optional native Library mirrors of Drive content.

So there are three supported states:

1. **No reconciliation job:** fully functional direct Drive library. Native-only items created elsewhere may remain local until explicitly saved/migrated.
2. **Reconciliation job present:** same direct behavior plus automatic catch-up/mirroring.
3. **Job status unknown:** behave as though no future job will save the current item, and complete authorized Drive persistence now.

## Installing the skill does not migrate native Library

This is a deliberate safety boundary.

Installing or invoking `SharedKnowledgeLibrary` must **not** sweep or copy an existing native ChatGPT Library.

Ordinary reads do not authorize migration.

Pre-existing native Library content is moved into canonical Drive only through:

- an explicit per-item save;
- an explicitly authorized bootstrap migration;
- an explicitly created reconciliation task.

This makes the skill safe to install on a new or existing ChatGPT account regardless of what its native Library contains.

## Why reconciliation is not normal two-way sync

When reconciliation is deployed, native ChatGPT Library participates because it can receive uploads and ChatGPT-generated files.

However, normal last-writer-wins bidirectional synchronization would create stale-copy and deletion hazards.

The optional unified reconciler therefore uses asymmetric ownership.

### New native Library item during reconciliation

```text
new upload/generated file
        ↓
native ChatGPT Library
        ↓
copy/adopt into Drive
        ↓
Drive becomes canonical
```

### Existing mapped item

```text
Google Drive
   ↓ authoritative updates
native Library mirror
```

Once mapped, a native Library edit, move, rename, or deletion does not automatically mutate Drive.

## ChatGPT Web

ChatGPT Web may naturally surface native Library results first. That is fine for immediate use.

The skill separates retrieval from ownership:

- a current-turn upload can be used immediately;
- a corresponding Drive item is the durable authority;
- if native and Drive copies disagree, Drive owns durable state;
- `save this to my Library` means canonical Drive when the skill is active, unless the user explicitly asks for native/built-in ChatGPT Library;
- ordinary use of a native Library file does not automatically migrate it.

This lets ChatGPT Web behave naturally without turning its private Library surface into a competing source of truth.

## Medical Records and Cynapsa

The previous architecture used two independent Drive→Library jobs:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

Those jobs may continue running temporarily because their source folder IDs did not change when the folders were moved.

The unified bootstrap should import their existing `_drive_sync_manifest.json` mappings so Library identities and version history can be preserved.

Only after a unified no-deletion validation run should the old tasks be disabled. Keep them disabled temporarily for rollback instead of deleting them immediately.

A fresh ChatGPT installation does **not** need either old per-folder job. It can access Medical Records and Cynapsa directly through the canonical Drive tree.

## Files in this package

### `SKILL.md`

Cross-agent behavior for direct read/write use, classification, ChatGPT Web behavior, optional native Library ingress, and canonical ownership.

### `_LIBRARY_POLICY.md`

Live policy intended to be placed at the root of Google Drive `ChatGPT Library` before activation.

### `bootstrap_migration.md`

Optional one-time migration/adoption procedure for an existing native ChatGPT Library. It:

- adopts existing Medical Records and Cynapsa mappings;
- inventories the rest of native ChatGPT Library;
- excludes the native `/Google Drive` mount;
- ingests eligible general untracked content;
- holds strongly operational/credential-bearing material for classification;
- performs no destructive cleanup during bootstrap.

### `scheduledprompt.md`

Optional ongoing unified reconciliation specification. It is catch-up/mirror infrastructure, not a prerequisite for the skill.

### `manifest.example.json`

Reference schema used only when bootstrap/reconciliation is deployed.

## No MCP requirement

This design does not require its own MCP server.

The current environment supplies Drive transport:

- ChatGPT can use its connected Google Drive app;
- Codex/Codex CLI can use whatever authorized Drive integration is available;
- another agent is responsible for its own authorized Drive access.

The skill defines the storage contract, not the transport.

## Recommended transition for the current ChatGPT account

1. **Completed:** move `Medical records` and `Cynapsa` under Google Drive `ChatGPT Library` while preserving their IDs.
2. Review the revised package.
3. Copy `_LIBRARY_POLICY.md` into the canonical Drive root.
4. Install `SharedKnowledgeLibrary` only after explicit user approval.
5. Optionally run `bootstrap_migration.md` in no-deletion mode to adopt the current native Library.
6. Review pending classifications and conflicts.
7. Optionally run one full unified reconciliation in validation/no-deletion mode.
8. Verify existing Medical/Cynapsa Library identities and mappings were adopted correctly.
9. If native Library catch-up is desired, create the recurring unified reconciliation task.
10. Disable `Medical Records Sync` and `Sync Cynapsa Drive` only after the unified task is validated.
11. Keep the disabled old tasks temporarily as rollback.
12. Enable canonical Drive→Library deletion reconciliation only after clean full scans are proven reliable.

## Fresh installation sequence

For a new ChatGPT/Codex environment with Drive access:

1. Install the skill.
2. Connect/authorize Google Drive as required by that environment.
3. Use canonical Drive immediately for reads and writes.
4. Do **not** create Medical/Cynapsa legacy jobs.
5. Create the optional unified reconciliation job only if native ChatGPT Library catch-up/mirroring is desired.
6. Run bootstrap only if that environment already has native Library content that should be adopted.

## Current status

Repository source: updated for direct operation with or without scheduled reconciliation.

Drive structure: Medical Records and Cynapsa are under `ChatGPT Library` with stable IDs preserved.

Not yet done in the current account:

- `_LIBRARY_POLICY.md` has not yet been copied into the Drive root.
- `SharedKnowledgeLibrary` has not been installed as a skill.
- bootstrap migration has not been run.
- unified scheduled reconciliation has not been created.
- the two legacy sync tasks have not been disabled.

Those are intentionally separate actions.

## Governing principle

**One canonical general Drive tree, one separate Codex operational tree, direct Drive persistence for authorized durable work, and native ChatGPT Library as immediate access/cache/optional ingress. Reconciliation is catch-up, not correctness.**
