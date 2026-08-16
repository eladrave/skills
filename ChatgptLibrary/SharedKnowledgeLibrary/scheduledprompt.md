# Shared Knowledge Library Sync Scheduled Task

Recommended schedule: **hourly**, `America/New_York`.

This task is **not created or installed by this file**. Create it only after the user explicitly approves installation/scheduling.

## Purpose

Incrementally ingest new or changed **general-purpose** files from ChatGPT native Library into the canonical Google Drive `ChatGPT Library` folder.

This is not a normal bidirectional mirror.

The canonical direction is:

```text
new/changed eligible ChatGPT native Library item
                    |
                    v
       Google Drive / ChatGPT Library
             becomes canonical
```

After ingestion, Drive changes do **not** sync back to native Library, and native Library deletion does **not** delete Drive.

## Canonical destination

- Folder name: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`
- URL: `https://drive.google.com/drive/folders/1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

## Required policy files

Before mutating anything, read from the canonical Drive root:

- `_LIBRARY_POLICY.md`
- `_EXTERNAL_SOURCES.md`
- `_shared_knowledge_library_manifest.json`

If either policy file is missing, stop the sync and report that SharedKnowledgeLibrary has not been fully initialized. Do not reconstruct policy from memory during a scheduled run.

If the manifest is missing, stop and request/bootstrap the one-time migration/init procedure instead of treating every native Library item as new.

## Existing tasks are independent and protected

Do not modify, disable, recreate, rename, or change the prompts of:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

Those jobs remain one-way Google Drive -> ChatGPT native Library synchronization jobs.

This task must never reverse either flow.

## Hard source exclusions

Recursively exclude ChatGPT native Library content under:

```text
/Medical records/**
/Cynapsa/**
/Google Drive/**
```

Do not materialize, upload, modify, or delete anything from these excluded trees as part of this task.

Do not treat `_drive_sync_manifest.json` files in excluded trees as user knowledge.

Honor any additional exclusions in the live `_EXTERNAL_SOURCES.md`.

## Operational knowledge exclusion

Do not ingest environment-specific operational knowledge that belongs in Google Drive `Codex`.

Potential operational content includes files whose primary purpose is:

- Credentials, passwords, API keys, tokens, private keys, or credential-bearing URLs.
- Private MCP endpoints or connection instructions.
- SSH/private-host connection details.
- Production deployment or rollback runbooks.
- Container/service operation procedures.
- Database operational credentials/access.
- Private infrastructure, network, cloud, runtime, or incident/recovery procedures.

For a newly encountered obvious operational candidate:

1. Do not upload it to SharedKnowledgeLibrary.
2. Do not automatically copy it to Codex.
3. Record a manifest state such as `skipped_operational_candidate` with non-secret routing metadata.
4. Report it only when new or materially changed so the user can decide whether to reconcile it into Codex.
5. Never expose its secret contents in the report.

If classification is uncertain and a wrong choice could create a competing source of truth, skip and report rather than ingest.

## Incremental source scan

Use the manifest's last successful scan time with a safety overlap when the Library tooling supports modified-time filtering.

Recommended behavior:

- Incremental scan: files modified since the previous successful scan minus a 6-hour overlap.
- Full scan: at least once every 24 hours to detect renames, moves, detached/missing sources, or changes that modified-time filtering may miss.

Record `last_incremental_scan_at` and `last_full_scan_at` in the manifest.

A scan must page until complete for its chosen scope. Do not treat a truncated listing as complete.

## New native Library item workflow

For every new eligible general-purpose native Library file:

1. Resolve the source's stable Library file ID, path, version, MIME type, size, and modified time.
2. Determine whether the item belongs to an external or operational domain. Skip if so.
3. Materialize or otherwise obtain the original/best raw representation without changing it unnecessarily.
4. Search the canonical Drive destination for an existing logical copy or path collision.
5. If identical content already exists in Drive, adopt that Drive file and record the mapping. Do not upload a duplicate.
6. If the path exists with different content, do not overwrite. Record a `conflict` and report it.
7. Otherwise create required Drive subfolders and upload the file with its intended filename.
8. Verify the new Drive file by ID, parent, name, MIME type, and size/content fingerprint when available.
9. Only after verification, write the manifest mapping and mark the item `synced`.

Preserve meaningful relative Library folders. Do not invent a new taxonomy during synchronization.

## Existing mapped item workflow

For a native Library source already mapped to a canonical Drive file, retrieve both the current source state and the current Drive destination state.

Compare each side to the last successfully synchronized state stored in the manifest.

### Case A: source changed, destination unchanged

Update the existing Drive file **in place**, preserving its Drive file ID.

Before replacing raw bytes:

- Re-read the Drive file metadata immediately before the write.
- Confirm it still matches the expected destination baseline.

After writing:

- Re-read/verify the Drive file.
- Update the manifest's source and destination baseline.

### Case B: source unchanged, destination changed

Drive is canonical.

Do not write the Drive content back to native Library.

Do not overwrite Drive.

Update observed destination metadata in the manifest if useful, while retaining the source mapping.

### Case C: both source and destination changed

Do not overwrite either side.

Mark the mapping `conflict`.

Report:

- Native Library path.
- Canonical Drive path.
- Non-sensitive modification/version metadata.

State that Drive remains canonical until an explicit merge/resolution is performed.

### Case D: source missing/deleted

Do not delete the Drive destination.

Mark the mapping `source_missing` or `detached`.

Do not recreate native Library content.

### Case E: destination missing/deleted

Do not automatically recreate it from native Library.

A Drive deletion may have been intentional and Drive is canonical after ingestion.

Mark the mapping `destination_missing` and report it for explicit restore/retire decision.

### Case F: source moved or renamed, destination unchanged

Use stable Library ID to recognize the same source.

If the new Library path is only organizational and the canonical Drive artifact has not independently changed, update/move/rename the existing Drive file to preserve the logical path **only when the live policy says Library path changes should be propagated for that item**.

If there is ambiguity, preserve the Drive canonical location and report the discrepancy rather than creating a duplicate.

## ChatGPT-created file already written directly to Drive

Sometimes ChatGPT will generate a file, native Library will retain it automatically, and the task that created the file may also have written the same artifact directly to canonical Drive.

When the scheduled sync later sees the native Library item:

- Compare content and logical identity.
- If the existing Drive file is identical, adopt it into the manifest.
- Do not upload another copy.

## User-uploaded file behavior

A user upload made through ChatGPT may appear in native Library even when no explicit `save to shared library` request was made.

For durable-looking general files, ingest them under this workflow unless excluded by domain policy.

For obvious transient/supporting files whose only purpose was a one-time conversion or manipulation, it is acceptable to skip migration when the classification is clear. Record a reason if the skip matters for future duplicate detection.

When uncertain whether a non-sensitive general file is worth retaining, prefer preserving it in the canonical library rather than silently discarding access to it.

## No reverse general synchronization

Never enumerate `Google Drive / ChatGPT Library` and create/update native Library items merely to make the two stores identical.

ChatGPT can access canonical Drive through its connected Drive capability.

Do not create a Drive -> native Library loop.

## No deletion reconciliation

This task performs no destructive mirror reconciliation.

Never delete a canonical Drive file because:

- A native Library item disappeared.
- A native Library folder was renamed or removed.
- A source scan did not return an item.

Never delete a native Library item because it was successfully ingested.

Never delete files from Medical records, Cynapsa, Codex, or the Google Drive mount.

## Manifest update safety

Do not overwrite the manifest from a stale local copy.

Before writing manifest changes:

1. Fetch the current Drive manifest.
2. Reconcile current file ID/revision/modified state with the version read at the beginning of the run.
3. Merge only the mappings changed by this run.
4. Preserve unrelated mappings and metadata.
5. Write/replace the same manifest file in place.
6. Re-read and verify it.

If concurrent manifest changes cannot be safely merged, do not overwrite them. Report a manifest conflict and leave successfully created Drive artifacts intact for reconciliation on the next run.

## Failure behavior

Fail closed for the affected item when:

- A Library listing is incomplete or truncated.
- A source file cannot be materialized reliably.
- Destination state cannot be read.
- Ownership/domain is materially ambiguous.
- An upload or update cannot be verified.
- Both source and destination changed.
- A concurrent Drive change is detected.

Do not turn an item-level failure into broad destructive cleanup.

Continue unaffected non-conflicting items when safe.

## Reporting and notification

Produce a concise run summary with counts for:

- Scanned.
- New eligible items.
- Created in Drive.
- Existing Drive files adopted/deduplicated.
- Updated in place.
- Drive-newer mappings left unchanged.
- Source-missing mappings retained.
- Destination-missing mappings.
- Hard exclusions.
- Operational candidates skipped.
- Conflicts.
- Failures.

If there were no content changes, conflicts, operational candidates, missing destinations, or failures, a minimal `No SharedKnowledgeLibrary changes` result is sufficient.

Prefer notifying the user only when something was ingested/updated or attention is needed, if task notification settings support that behavior.

Always explicitly confirm that this run did not reverse-sync `/Medical records` or `/Cynapsa` and did not modify their canonical Drive folders.
