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

They are now normal canonical subtrees of SharedKnowledgeLibrary.

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
│   └── _sync/
│       └── _shared_library_manifest.json
│
└── Codex/                           CANONICAL OPERATIONAL KNOWLEDGE
    ├── credentials
    ├── infrastructure
    ├── deployment runbooks
    └── operational instructions

ChatGPT native Library
    = immediate-access surface + mirror + ingress
    ≠ canonical authority
```

## Why this is not a normal two-way sync

Native ChatGPT Library automatically receives uploads and many ChatGPT-generated files, so it needs to participate in the architecture.

However, using normal last-writer-wins bidirectional synchronization would create stale-copy and deletion hazards.

The unified reconciler therefore uses asymmetric ownership:

### New native Library item

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

The skill explicitly separates retrieval from ownership:

- a current-turn upload can be used immediately;
- a mapped Drive item is the durable authority;
- if mapped native and Drive copies disagree, Drive wins;
- `save this to my Library` means canonical Drive when the skill is active, unless the user explicitly asks for native/built-in ChatGPT Library.

## Medical Records and Cynapsa

The previous architecture had two independent Drive→Library jobs:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

Those jobs may continue running temporarily because their source folder IDs did not change when the folders were moved.

The unified bootstrap should import their existing `_drive_sync_manifest.json` mappings so Library identities and version history can be preserved.

Only after the unified reconciler has completed a successful validation run should the old tasks be disabled.

Do not delete the old tasks immediately. Keep them disabled for rollback until the new process is proven stable.

## Files in this package

### `SKILL.md`

Cross-agent behavior for reading, writing, classification, ChatGPT Web behavior, native Library ingress, and canonical ownership.

### `_LIBRARY_POLICY.md`

Live policy intended to be placed at the root of Google Drive `ChatGPT Library` before activation.

### `bootstrap_migration.md`

One-time migration/adoption procedure. It:

- adopts existing Medical Records and Cynapsa mappings;
- inventories the rest of native ChatGPT Library;
- excludes the native `/Google Drive` mount;
- ingests general untracked content;
- holds strongly operational/credential-bearing material for classification;
- performs no destructive cleanup during bootstrap.

### `scheduledprompt.md`

Ongoing unified reconciliation specification.

### `manifest.example.json`

Reference schema for unified identity and conflict tracking.

## No MCP requirement

This design does not require its own MCP server.

The current environment supplies Drive transport:

- ChatGPT can use its connected Google Drive app;
- Codex/Codex CLI can use whatever authorized Drive integration is available;
- another agent is responsible for its own authorized Drive access.

The skill defines the storage contract, not the transport.

## Recommended cutover sequence

1. **Already completed:** move `Medical records` and `Cynapsa` under Google Drive `ChatGPT Library` while preserving their IDs.
2. Review the revised files in this GitHub folder.
3. Copy `_LIBRARY_POLICY.md` into the canonical Drive root.
4. Install `SharedKnowledgeLibrary` only after explicit user approval.
5. Run `bootstrap_migration.md` in no-deletion mode.
6. Review pending classifications and conflicts.
7. Run one full unified reconciliation in validation/no-deletion mode.
8. Verify existing Medical and Cynapsa Library IDs/mappings were adopted correctly.
9. Create the recurring unified reconciliation task at the desired cadence.
10. Disable `Medical Records Sync` and `Sync Cynapsa Drive` only after the unified task is validated.
11. Keep the disabled old tasks temporarily as rollback.
12. Enable canonical Drive→Library deletion reconciliation only after clean full scans are proven reliable.

## Current status

Repository source: revised for the single-tree model.

Drive structure: Medical Records and Cynapsa have been moved under `ChatGPT Library` with their stable IDs preserved.

Not yet done:

- `_LIBRARY_POLICY.md` has not yet been installed into the Drive root by this package change.
- `SharedKnowledgeLibrary` has not been installed as a skill.
- bootstrap migration has not been run.
- unified scheduled reconciliation has not been created.
- the two legacy sync tasks have not been disabled.

Those are intentionally separate actions.

## Governing principle

**One canonical general Drive tree, one separate Codex operational tree, and native ChatGPT Library as cache, mirror, and ingress.**
