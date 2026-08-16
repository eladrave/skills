# Shared Knowledge Library Unified Reconciliation

This prompt is intended for one recurring task after the bootstrap migration and validation have completed.

Do not create or enable the task merely because this file exists. The user must explicitly authorize scheduling.

## Purpose

Reconcile the canonical Google Drive `ChatGPT Library` tree with native ChatGPT Library while preserving a strict ownership model:

- Google Drive is canonical for all mapped items.
- Native ChatGPT Library is mirror/cache for mapped items.
- New untracked native Library items are ingress candidates.
- The separate Google Drive `Codex` folder is not part of this synchronization.

## Canonical Drive root

- Folder: `ChatGPT Library`
- ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Canonical included subtrees include:

- `Medical records`, ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

## Separate excluded operational root

Never recursively sync, mirror, or ingest the Google Drive `Codex` folder as part of this task.

Codex folder ID:

`18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`

Operational/credential-bearing native Library items that appear to belong there must be reported for classification rather than copied into both roots.

## Control files

Read the live root policy before reconciliation:

`_LIBRARY_POLICY.md`

Use the canonical unified manifest:

`_sync/_shared_library_manifest.json`

Control paths are not normal user content and should not be mirrored into native Library:

- `/_sync/**`
- `/_LIBRARY_POLICY.md`

## Preflight

Before mutations:

1. Verify Google Drive access.
2. Verify native ChatGPT Library access.
3. Verify canonical root ID and name.
4. Verify `Medical records` and `Cynapsa` remain descendants of the canonical root with their expected stable IDs.
5. Verify `Codex` is not a descendant of the canonical root.
6. Read and validate the unified manifest JSON.
7. Confirm no unresolved manifest corruption or duplicate identity mappings exist.
8. Determine whether this run is allowed to perform Library-side deletion reconciliation. If any required full enumeration is incomplete, deletion must be suppressed.

If preflight cannot establish the ownership boundaries, perform no destructive reconciliation.

## Full inventories

Recursively enumerate the complete canonical Drive root with pagination.

Recursively enumerate the complete native ChatGPT Library with pagination.

Hard exclude the native connector-backed path:

`/Google Drive/**`

Never ingest that mount back into Drive.

Also exclude protected native Library artifacts that cannot safely participate in normal file synchronization.

## Mapping model

Use stable IDs as primary identity:

- Drive file/folder ID;
- native Library file/folder ID.

Paths are mutable attributes, not identities.

Each managed mapping records a last-successful baseline for conflict detection.

Do not match by filename alone when stable mapping or stronger evidence exists.

## Reconciliation classes

For every logical item, classify it into exactly one of these states.

### 1. Managed, Drive only changed

If the Drive item changed from baseline and the mapped native Library mirror did not:

- Drive wins.
- Update/replace the existing Library mirror rather than creating a new identity when supported.
- Apply canonical Drive move/rename to the Library mirror.
- Verify the Library result.
- Update baseline only after verification.

### 2. Managed, native mirror only changed

If a mapped native Library mirror changed from baseline while canonical Drive did not:

- do not overwrite Drive;
- treat the Library copy as drift, not an authoritative edit;
- restore/refresh it from canonical Drive when safe;
- if safe restoration cannot be verified, mark drift/conflict and report it;
- never propagate a mapped Library rename/move to Drive automatically.

### 3. Managed, both changed

If Drive and mapped native Library both changed independently since baseline:

- do not overwrite either current state;
- mark `conflict`;
- preserve both;
- suppress destructive action for that logical item;
- report it for resolution.

Never choose a winner based only on newest timestamp.

### 4. New canonical Drive item

If a Drive item is new and has no mapping:

- search for an equivalent native Library item first;
- adopt an equivalent when verified;
- otherwise create the corresponding native Library mirror;
- for stored files preserve bytes and filename;
- for Google-native files use the chosen export representation;
- verify the native Library result;
- add mapping and baseline.

### 5. New untracked native Library item

If an item exists in native Library but is not under `/Google Drive`, is not mapped, and is not protected:

1. Determine whether it is durable general knowledge suitable for SharedKnowledgeLibrary.
2. Determine the corresponding canonical Drive relative path.
3. Search for an existing logical/equivalent Drive item.
4. Adopt an existing equivalent when verified rather than creating a duplicate.
5. Otherwise upload/create it under canonical Drive.
6. Verify Drive metadata/bytes/type.
7. Record the mapping and baseline.
8. Drive becomes canonical from this point forward.

Do not delete the native source after ingress. It becomes the mirror identity.

### 6. Strongly operational or credential-bearing untracked native item

If an untracked native Library file strongly appears to be operational agent knowledge, for example credentials, tokens, MCP connection details, SSH instructions, production deployment/recovery runbooks, or infrastructure operating procedures:

- do not auto-ingest it into SharedKnowledgeLibrary;
- do not silently copy it into `Codex` either;
- mark `pending-classification`;
- report filename/path and reason without exposing secret values.

### 7. Drive-deleted managed item

If a mapped Drive item is absent from a **complete successful canonical enumeration** and deletion is otherwise safe:

- mark canonical deletion/tombstone;
- move the mapped native Library mirror to Library trash when supported;
- never permanently delete it;
- update manifest after verifying the trash/move result.

If Drive enumeration is partial, failed, truncated, or ambiguous, suppress all deletion reconciliation for the run.

### 8. Native-Library-deleted managed item

If Drive still exists but its mapped native mirror is missing:

- do not delete Drive;
- recreate the mirror when useful and supported, or record that the mirror is absent;
- Drive remains canonical.

## Folder behavior

Preserve canonical Drive hierarchy in native Library where practical.

A Drive folder move or rename should update its native Library mirror path while preserving existing Library identity when the Library tool supports it.

A native Library move/rename of a mapped mirror does not move/rename Drive. Restore it to canonical structure or report drift.

## Medical records and Cynapsa

Treat both as normal canonical Drive subtrees of the unified root.

Do not special-case them as external sources.

However, preserve mappings adopted from their legacy manifests.

A new untracked native Library item under `/Medical records` or `/Cynapsa` is eligible for ingress into the corresponding canonical Drive subtree under the same rules as other general content.

Do not treat legacy `_drive_sync_manifest.json` files as documentary content. Once cutover is complete, they may be ignored by this task.

## Google-native files

For native Library mirrors use consistent exports:

- Google Docs → PDF
- Google Sheets → XLSX
- Google Slides → PDF

Record export format in the manifest.

The Google-native Drive item remains canonical.

Never upload the export back into Drive as a second canonical item.

## Duplicate prevention

Before every create operation:

1. search by stable ID mapping;
2. check destination path;
3. compare filename, size, MIME/type, and available content/revision/hash evidence;
4. detect whether the item is already present through another mapping;
5. adopt when equivalent rather than creating `(...1)`, `copy`, `v2`, or another duplicate.

If equivalence cannot be established safely, record a conflict instead of guessing.

## Manifest update order

Apply safe changes in this order:

1. complete inventories;
2. classify all states;
3. create required Drive folders for verified native ingress;
4. ingest/adopt new native items into Drive;
5. create/update/adopt Library mirrors from Drive;
6. apply Drive-authoritative Library moves/renames;
7. verify all successful mutations;
8. perform Library trash reconciliation for verified Drive deletions only if deletion is enabled;
9. write the unified manifest;
10. re-read and validate the manifest.

Never update the baseline for a mutation that was not verified.

## Failure rules

Fail closed on deletion and overwrites.

Suppress deletion reconciliation if:

- Drive inventory is incomplete/truncated;
- Library inventory is incomplete/truncated;
- manifest cannot be parsed or validated;
- duplicate stable IDs appear unexpectedly;
- required exports/downloads fail;
- an intended create/update/move cannot be verified;
- ownership boundary is ambiguous;
- unresolved systemic conflicts make reconciliation unsafe.

Do not roll back verified independent non-destructive creations solely because another unrelated item failed. Report partial success accurately.

## No Drive deletion from native Library

This is absolute for ordinary reconciliation:

**A native ChatGPT Library deletion, move, rename, or content edit never by itself authorizes deleting or replacing the canonical Drive item.**

## Existing legacy tasks during cutover

Before the unified task takes ownership, the existing jobs may remain enabled:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

After a full unified no-deletion validation run confirms their mappings were adopted and no duplicate identities were created, the user may authorize disabling those old tasks.

Do not disable them automatically from this prompt unless the prompt itself has been explicitly updated to include that one-time cutover action.

## Report

Provide a concise reconciliation report with counts for:

- canonical Drive items discovered;
- native Library items discovered;
- managed unchanged;
- Drive-authoritative mirror updates;
- Library drift restored/reported;
- new native ingress uploaded;
- existing Drive equivalents adopted;
- new Drive items mirrored/adopted;
- moved/renamed mirrors;
- canonical deletions mirrored to Library trash;
- missing Library mirrors recreated;
- pending operational classifications;
- conflicts;
- skipped/protected items;
- failures.

Explicitly state whether deletion reconciliation was enabled or suppressed and why.

Do not expose secret values in the report.
