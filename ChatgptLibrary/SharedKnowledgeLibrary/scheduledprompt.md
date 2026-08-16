# SharedKnowledgeLibrary Native-Library Ingress

This prompt defines the optional recurring catch-up task for SharedKnowledgeLibrary.

Its purpose is narrow: find durable files that exist only in native ChatGPT Library and persist them into canonical Google Drive `ChatGPT Library`.

It is **not** a Drive-to-Library mirror and must never attempt to keep native Library synchronized from Drive.

## Canonical Drive root

- Folder: `ChatGPT Library`
- ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Included canonical subtrees include:

- `Medical records`, ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

Separate operational root, never ingested as general library content:

- `Codex`, ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`

## Live policy

Read `_LIBRARY_POLICY.md` from the canonical Drive root before making changes.

Use control folder:

`ChatGPT Library/_sync/`

Use ingress manifest:

`_sync/_shared_library_ingress_manifest.json`

The manifest may be a Google Doc containing JSON text if raw-file creation is unavailable. Treat its text as JSON control data.

## Core rules

1. Google Drive is canonical.
2. Native ChatGPT Library is only an ingress source.
3. Never copy Drive content back into native Library.
4. Never delete, rename, move, or overwrite canonical Drive because of a native Library mutation.
5. Never ingest the native `/Google Drive/**` connector-backed tree.
6. Never use newest timestamp as a general winner rule.
7. Before creating anything in Drive, search for an existing logical equivalent and adopt it instead of duplicating it.
8. Strongly operational or credential-bearing items belong to separate `Codex`, not SharedKnowledgeLibrary. Report them for classification instead of copying them into both roots.

## Legacy subtree cutover

The pre-existing native Library `/Medical records` and `/Cynapsa` trees are legacy Drive-backed copies from retired per-folder sync jobs.

The ingress manifest contains a `cutover_at` timestamp.

For these two native Library paths:

- items created or already present before `cutover_at` are legacy copies and must not be uploaded back into Drive;
- items newly created after `cutover_at` and not otherwise mapped may be considered for ingress into the corresponding canonical Drive subtree.

The legacy `_drive_sync_manifest.json` files themselves are control metadata and must never be ingested.

## Inventory

Recursively enumerate native ChatGPT Library with pagination.

Hard exclude:

- `/Google Drive/**`
- `/Medical records/_drive_sync_manifest.json`
- `/Cynapsa/_drive_sync_manifest.json`
- protected/internal Library artifacts that cannot safely be materialized

Read the ingress manifest and build a set of already-managed native Library IDs.

## Classification

For each untracked candidate, classify as one of:

### A. Eligible durable general knowledge

Examples:

- personal/reference documents;
- research;
- memoir/writing;
- project/business material;
- medical material;
- Cynapsa general knowledge;
- durable ChatGPT-generated reports/artifacts.

### B. Strongly operational or credential-bearing

Examples:

- passwords, tokens, API keys, secret-bearing URLs;
- MCP connection details;
- SSH/production connection instructions;
- deployment, rollback, recovery, or infrastructure operating runbooks.

Do not ingest category B into SharedKnowledgeLibrary. Mark `pending-classification` and report only path/name and reason, never secret values.

### C. Temporary or low-durable-value artifact

Examples may include throwaway previews, transient intermediates, obvious duplicates, or files whose purpose cannot be established.

Do not delete them. Mark `skipped` unless a retention rule says otherwise.

When uncertain, prefer pending/skipped over creating a duplicate.

## Ingress workflow

For each eligible candidate:

1. Determine the canonical Drive relative destination.
2. Preserve the native Library path when reasonable.
3. Search Drive for an existing logical equivalent using path/name plus available size, MIME/type, content/hash/revision evidence.
4. If equivalent exists, record adoption and do not upload.
5. Otherwise materialize the native Library file using supported Files tools.
6. Upload it to the correct canonical Drive folder, preserving filename and MIME type when practical.
7. Verify the Drive file exists and metadata/size/type are plausible.
8. Record native Library ID, version, Drive ID/path, origin, and status in the ingress manifest.
9. Do not delete the native Library source.

If a mapped native item changes later, do not automatically overwrite Drive. Treat Drive as canonical and report drift only when material.

## Folder creation

Create missing canonical Drive folders only when needed for an eligible ingress item.

Before creating a folder, check for an existing folder with the intended name/path.

Do not reorganize unrelated canonical Drive content.

## Existing root backlog

At initial cutover, there may be many pre-existing native Library files outside `/Medical records`, `/Cynapsa`, and `/Google Drive`.

These may be ingested as a backlog when they clearly qualify as durable general knowledge.

Process non-destructively. It is acceptable to ingest a bounded batch per run if the backlog is large, as long as the manifest records progress and later runs continue from remaining untracked candidates.

## Failure behavior

If native Library listing is incomplete, materialization fails, Drive access fails, destination identity is ambiguous, or a create cannot be verified:

- do not guess;
- do not overwrite canonical Drive;
- record failure/pending status when possible;
- continue only with independent safe items;
- do not perform destructive cleanup.

## Report behavior

Notify the user only when at least one of these occurs:

- new files were ingested or existing Drive equivalents were adopted;
- pending operational classifications were found;
- conflicts or failures occurred;
- a meaningful backlog remains after a bounded run.

If nothing changed and there are no issues, do not notify.

When reporting, include counts for:

- native items scanned;
- already managed/legacy skipped;
- ingested;
- existing Drive equivalents adopted;
- pending operational classification;
- skipped temporary/ambiguous;
- failures;
- remaining backlog when known.

Never expose secret values.

## Absolute safety rule

**This task may add or adopt canonical Drive content, but native ChatGPT Library can never authorize deletion or destructive modification of canonical Drive.**