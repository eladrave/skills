# SharedKnowledgeLibrary

This package defines a cross-agent shared knowledge architecture using Google Drive as the canonical storage layer while preserving ChatGPT native Library as an ingress and convenience surface.

## Status

**Source package only. Not installed. No scheduled task is created by these files.**

Installation, Drive initialization, bootstrap migration, and scheduling are separate actions and should occur only after explicit user approval.

## Canonical general library

- Google Drive folder: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`
- URL: `https://drive.google.com/drive/folders/1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

## Package files

### `SKILL.md`

The agent-facing SharedKnowledgeLibrary skill.

It defines:

- The canonical Drive root.
- ChatGPT native Library semantics.
- ChatGPT Web behavior when native Library retrieval appears first.
- Read/write ownership and conflict rules.
- Medical Records and Cynapsa exclusions.
- Codex operational knowledge separation.
- Manifest semantics.
- No-MCP transport assumption.

### `_LIBRARY_POLICY.md`

Template for the live governance file that should eventually be placed at the root of the Google Drive `ChatGPT Library` folder.

Once deployed to Drive, the Drive copy becomes the authoritative live policy. The repository copy remains the reviewed bootstrap/source template.

### `_EXTERNAL_SOURCES.md`

Template for the live registry of separately canonical knowledge domains.

Currently defines:

- Medical records.
- Cynapsa.
- Codex operational knowledge.
- ChatGPT Library's mounted `/Google Drive` exclusion.

### `bootstrap_migration.md`

One-time migration procedure for existing ChatGPT native Library content.

It deliberately separates migration from ongoing synchronization because the existing native Library already contains mixed content, including externally synced trees and historical operational-looking files.

The bootstrap:

- Fully inventories native Library.
- Excludes `/Medical records`, `/Cynapsa`, and `/Google Drive` recursively.
- Detects/skips operational candidates that may belong to Codex.
- Migrates eligible general knowledge to Drive.
- Deduplicates against existing Drive content.
- Creates the Library-to-Drive manifest.
- Performs no deletions.

### `scheduledprompt.md`

Recurring incremental native Library -> canonical Drive ingestion prompt.

Recommended cadence: hourly.

It is intentionally **not** a bidirectional mirror.

Key behavior:

- New/changed eligible Library content may flow to Drive.
- After ingestion, Drive is canonical.
- Drive changes do not flow back to native Library.
- Native Library deletion does not delete Drive.
- A deleted Drive destination is not silently recreated from stale native Library.
- Concurrent changes become conflicts instead of last-writer-wins overwrites.

## Existing synchronization jobs

The following existing scheduled jobs are intentionally outside this package and must remain unchanged:

### `Medical Records Sync`

```text
Google Drive / Medical records
        ->
ChatGPT native Library /Medical records
```

Google Drive remains the sole source of truth.

SharedKnowledgeLibrary never syncs `/Medical records` back to Drive.

### `Sync Cynapsa Drive`

```text
Google Drive / Cynapsa
        ->
ChatGPT native Library /Cynapsa
```

Google Drive remains the sole source of truth.

SharedKnowledgeLibrary never syncs `/Cynapsa` back to Drive.

## Codex boundary

`Google Drive / Codex` remains a different use case.

It is operational shared memory for agents and is governed by `CodexAsKnowledgeReadWrite`.

SharedKnowledgeLibrary does not duplicate:

- Credentials.
- Private endpoints.
- Deployment runbooks.
- Infrastructure topology.
- SSH/database/MCP connection instructions.
- Runtime/recovery procedures.

A document is routed based on what the knowledge is for, not which agent happened to create it.

## Why no MCP is required

This architecture defines storage ownership, not transport.

ChatGPT, Codex, Codex CLI, or another agent may use whatever authorized Google Drive integration is available in that environment.

The SharedKnowledgeLibrary skill does not require the user to provision another OAuth application or MCP server merely to access the same Drive folder.

## ChatGPT Web design

ChatGPT Web can naturally surface native Library files because uploads and generated files are retained there.

The architecture does not fight that product behavior.

Instead:

- Current-turn files may be used directly.
- Native Library is valid discovery/ingress.
- Older general knowledge resolves to canonical Drive when freshness or modification matters.
- New Library-only general artifacts are `pending ingress` until copied to Drive.
- Medical Records and Cynapsa Library trees remain intentional read mirrors.
- `/Google Drive` is never re-exported to Drive.

This prevents retrieval convenience from becoming an accidental source-of-truth policy.

## Recommended deployment sequence after review

Do not perform these steps until explicitly approved.

1. Place reviewed `_LIBRARY_POLICY.md` in the Google Drive `ChatGPT Library` root.
2. Place reviewed `_EXTERNAL_SOURCES.md` in that same root.
3. Install/enable the `SharedKnowledgeLibrary` skill in the desired agent environments.
4. Run `bootstrap_migration.md` once to migrate existing eligible native Library content and create `_shared_knowledge_library_manifest.json`.
5. Review bootstrap conflicts and Codex-routing candidates.
6. Create the recurring task using `scheduledprompt.md`.
7. Leave the existing Medical Records and Cynapsa tasks untouched.

## Governing principle

**One logical knowledge item, one canonical owner, many authorized consumers.**
