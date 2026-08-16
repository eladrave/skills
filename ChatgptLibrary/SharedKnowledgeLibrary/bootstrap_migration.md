# SharedKnowledgeLibrary Bootstrap Migration

This is a **one-time migration procedure**, not a recurring scheduled task.

Its purpose is to migrate existing general-purpose content from ChatGPT native Library into the canonical Google Drive `ChatGPT Library` folder without duplicating the existing Medical Records, Cynapsa, Google Drive mount, or Codex operational knowledge domains.

## Canonical destination

- Google Drive folder: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`
- URL: `https://drive.google.com/drive/folders/1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

## Existing domains that must remain unchanged

Do not modify the existing scheduled tasks:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

Do not change their directionality.

Their source folders remain authoritative and their native Library mirrors remain one-way Drive -> Library mirrors.

Do not modify or migrate the Google Drive `Codex` operational knowledge folder.

## Required governance

Before migration, read the bundled/live versions of:

- `_LIBRARY_POLICY.md`
- `_EXTERNAL_SOURCES.md`

If live copies already exist in the canonical Drive root, use the live Drive copies as authoritative policy.

If they do not yet exist, this bootstrap may create them in the canonical Drive root from the reviewed bundled copies before migrating user content.

Do not overwrite different existing policy files without explicit authorization.

## Source inventory

Inventory ChatGPT native Library recursively.

The source inventory must be complete before making migration decisions.

Record for every native Library item when available:

- Stable Library file/folder ID.
- Full Library path.
- File/folder type.
- MIME type.
- Size.
- Created time.
- Modified time.
- Version ID.
- Whether model-generated when available.

Do not infer folder membership from search snippets alone.

## Hard recursive exclusions

Never migrate anything under:

```text
/Medical records/**
/Cynapsa/**
/Google Drive/**
```

The exclusions include their manifests and all descendants.

Do not read excluded file contents merely to decide whether to migrate them. Their path already defines their ownership boundary.

## Additional semantic exclusion: Codex operational knowledge

Outside the hard exclusions, inspect enough metadata/content to identify files whose primary purpose is environment-specific operational knowledge.

Examples include files containing or primarily documenting:

- Passwords, API keys, tokens, private keys, credential-bearing URLs.
- Private MCP connection information.
- SSH host access or private host connection procedures.
- Production deployment/runbook procedures.
- Container or service operation details.
- Private database access details.
- Infrastructure/network/cloud operational configuration.
- Runtime recovery or incident procedures.

Do **not** automatically migrate obvious operational candidates into SharedKnowledgeLibrary.

Do **not** automatically copy them into the Google Drive `Codex` folder either.

For each operational candidate:

1. Record its Library path and non-secret classification reason.
2. If permitted and useful, check whether an existing Codex canonical file already owns that knowledge.
3. Mark it `skipped_operational_candidate`.
4. Report unique-looking candidates for deliberate later reconciliation.
5. Never reveal secret values in the migration report.

If classification is genuinely ambiguous, skip the item and report it rather than creating a possible second source of truth.

## General migration candidates

Migrate items that are durable general-purpose knowledge and do not belong to an external canonical domain.

Examples include:

- Personal reference documents.
- Research.
- Writing and manuscripts.
- General business documents.
- Project documents without a different canonical owner.
- User uploads intended for long-term reuse.
- ChatGPT-generated reports, spreadsheets, documents, images, and other artifacts worth retaining.
- General technical designs that are not private environment-specific operational runbooks.

Do not migrate obviously disposable temporary artifacts merely because they exist if their content is clearly transient and has no durable reuse value. When uncertain about value, preserve rather than delete, but migration may be skipped and reported.

## Preserve logical structure

For migrated content, preserve the native Library relative folder structure when meaningful.

Root-level Library files may remain root-level under the Drive `ChatGPT Library` folder unless a clear existing folder ownership structure already applies.

Do not invent a large taxonomy during bootstrap merely to make the folder look organized.

Preserve current names unless a collision requires review.

## File bytes and representations

For stored files, preserve original bytes and filename when possible.

For Library artifacts that require materialization, obtain the original/best raw-file representation before upload.

Do not silently transform PDFs to Docs, spreadsheets to Sheets, or other stored formats during migration unless the user has explicitly requested conversion.

For native/generated artifacts where only one supported representation exists, record the chosen representation in the manifest.

## Existing destination inventory

Before uploading candidates, recursively inventory the canonical Drive `ChatGPT Library` root.

The folder may already contain policy files or user content.

Do not assume it is empty simply because it was empty at design time.

Record stable Drive IDs, paths, MIME types, sizes, modified times, checksums/revisions when available.

## Duplicate and collision handling

### Exact or strong content match

If a migration candidate matches an existing Drive file by strong evidence such as:

- Same content hash/checksum.
- Same raw bytes.
- Same stable artifact with verified equivalent content.

adopt the existing Drive file as the canonical destination and record the Library-to-Drive mapping.

Do not upload another copy.

### Same path/name, different content

Do not overwrite an existing Drive file merely because a native Library item has the same path or name.

Treat the Drive file as canonical existing content.

Mark the Library candidate as a collision/conflict and report it.

Do not generate `-copy`, `-new`, or similar filenames automatically unless the user explicitly decides both are separate artifacts.

### Same content, different path

If the same file is already in Drive at a different logical location, do not duplicate it automatically. Prefer the existing canonical Drive identity and report the path discrepancy if it matters.

## Migration write order

Perform safe writes in this order:

1. Verify Drive access and canonical destination folder ID.
2. Read/establish policy files.
3. Complete native Library inventory.
4. Complete Drive destination inventory.
5. Classify exclusions and operational candidates.
6. Create required destination folders for approved general candidates.
7. Upload/adopt files one by one or in safe bounded batches.
8. Verify every created/adopted file.
9. Build/update the synchronization manifest only after verified file operations.
10. Re-read the manifest and spot-check representative files.

Do not delete anything from native Library or Drive during bootstrap.

## Manifest

Create or update:

`_shared_knowledge_library_manifest.json`

in the canonical Drive root.

Recommended top-level structure:

```json
{
  "schema_version": 1,
  "canonical_drive_root_id": "1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb",
  "last_bootstrap_at": "<timestamp>",
  "items": {}
}
```

Key each tracked source item by stable native Library file ID when possible.

Recommended item fields:

```json
{
  "source_library_file_id": "<stable id>",
  "source_library_path": "/path/file.ext",
  "source_version_id": "<version>",
  "source_created_at": "<timestamp>",
  "source_modified_at": "<timestamp>",
  "source_mime_type": "<mime>",
  "source_size": 123,
  "source_fingerprint": "<checksum if available>",
  "source_model_generated": false,
  "drive_file_id": "<stable Drive id>",
  "drive_path": "/path/file.ext",
  "drive_mime_type": "<mime>",
  "drive_modified_at_at_sync": "<timestamp>",
  "drive_fingerprint_at_sync": "<checksum/revision if available>",
  "last_synced_source_version": "<version>",
  "state": "synced",
  "last_synced_at": "<timestamp>"
}
```

For excluded/skipped items, the manifest may record only non-sensitive routing metadata and a state such as:

- `excluded_external_source`
- `excluded_drive_mount`
- `skipped_operational_candidate`
- `conflict`

Do not store secret contents in the manifest.

## Drive becomes canonical after ingestion

For every successfully ingested general artifact:

- Google Drive becomes the canonical copy.
- Native Library remains an ingress/cache copy.
- Future native Library deletion does not delete Drive.
- Future Drive edits do not need to be mirrored back to native Library.
- Future sync logic must not overwrite a changed Drive file from a stale native Library version.

## Fail-closed conditions

Do not continue with destructive or overwriting behavior if:

- Native Library inventory is incomplete or pagination is unresolved.
- Drive destination inventory is incomplete or ambiguous.
- A source file cannot be materialized/read reliably.
- A destination upload cannot be verified.
- Path identity is ambiguous.
- A possible external-domain ownership conflict is unresolved.
- A file may contain unique Codex operational knowledge and classification is uncertain.
- Manifest state cannot be safely reconciled.

Bootstrap is non-destructive, so individual failed files may be reported while unaffected files continue if doing so cannot create incorrect ownership.

## Migration report

Report counts for:

- Native Library files discovered.
- Hard-excluded Medical records items.
- Hard-excluded Cynapsa items.
- Hard-excluded Google Drive mount items.
- General migration candidates.
- Successfully uploaded files.
- Existing Drive files adopted without duplication.
- Unchanged/already mapped items.
- Operational candidates skipped.
- Conflicts/collisions.
- Failures.

List operational candidates and conflicts by safe filename/path only. Do not include credential values or secret content.

Explicitly confirm:

- No existing Medical Records or Cynapsa sync task was modified.
- No Medical Records or Cynapsa content was synced back to Drive.
- No Codex operational file was automatically duplicated into SharedKnowledgeLibrary.
- No files were deleted from native Library.
- No canonical Drive files were deleted.
