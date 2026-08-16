# SharedKnowledgeLibrary Bootstrap Migration

This is a one-time migration/adoption procedure for establishing the unified SharedKnowledgeLibrary.

Do not run this procedure merely because the source exists in GitHub. Run it only after explicit user authorization.

## Goal

Establish one canonical Google Drive tree:

`ChatGPT Library` folder ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

while preserving existing native ChatGPT Library identities wherever possible and avoiding duplicate copies.

The existing Drive folders `Medical records` and `Cynapsa` have already been moved under the canonical root with their IDs preserved.

## Safety mode

Bootstrap is **non-destructive**.

During bootstrap:

- do not delete anything from Google Drive;
- do not permanently delete anything from native ChatGPT Library;
- do not remove existing Medical/Cynapsa mirrors;
- do not disable old scheduled jobs;
- do not resolve ambiguous operational-vs-general classification by guessing;
- do not use last-writer-wins.

All deletion reconciliation remains disabled until after a later validated cutover.

## Sources

### Canonical Drive root

- `ChatGPT Library`
- ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

### Native ChatGPT Library

Inventory the entire persistent Library recursively.

### Existing legacy mappings

Locate and read, when present:

- `/Medical records/_drive_sync_manifest.json`
- `/Cynapsa/_drive_sync_manifest.json`

Treat these files as synchronization metadata only.

They contain valuable mapping information between stable Drive IDs and existing native Library items.

## Hard native-Library exclusion

Never ingest the native Library `/Google Drive` mounted/connected source back into Drive.

Exclude:

`/Google Drive/**`

This is a connector-backed view of Drive and ingesting it would create a loop.

Also exclude protected/internal Library artifacts that cannot safely be copied or mutated.

## Phase 1: verify canonical Drive structure

1. Fetch metadata for the canonical Drive root.
2. Confirm it is folder ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`.
3. Confirm `Medical records` is a direct child with ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`.
4. Confirm `Cynapsa` is a direct child with ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`.
5. Confirm the separate `Codex` root is not a descendant of SharedKnowledgeLibrary.
6. Fail closed if any of these ownership boundaries are not as expected.

## Phase 2: establish control files

Ensure the canonical Drive root contains the approved `_LIBRARY_POLICY.md`.

Create a reserved control folder if needed:

`_sync/`

Create the unified manifest:

`_sync/_shared_library_manifest.json`

Initialize it from the approved schema in `manifest.example.json`.

Control files are not normal documentary content and should not be mirrored into native ChatGPT Library.

## Phase 3: inventory native Library

Recursively enumerate the entire native ChatGPT Library with pagination until complete.

Record for every item:

- native Library file/folder ID;
- path;
- version when available;
- size;
- MIME/file type;
- generated/uploaded metadata when available;
- whether it is under `/Google Drive`;
- whether it is under `/Medical records`;
- whether it is under `/Cynapsa`;
- whether it appears already managed by a legacy manifest;
- whether it strongly appears operational/credential-bearing.

Do not assume root-level files are all general knowledge.

## Phase 4: adopt Medical Records mappings

If `/Medical records/_drive_sync_manifest.json` exists:

1. Read the complete manifest.
2. For each mapping, verify the Drive ID is still under canonical `ChatGPT Library/Medical records`.
3. Verify the native Library ID still exists when possible.
4. Verify current paths and versions.
5. Add the mapping to the unified manifest without creating a new Drive or Library copy.
6. Record origin as `legacy-medical-sync-adopted` or equivalent.
7. Record current synchronized baseline metadata for future conflict detection.
8. Do not treat the legacy manifest itself as medical evidence.

If an entry cannot be verified, mark it unresolved rather than manufacturing a replacement.

## Phase 5: adopt Cynapsa mappings

Perform the same adoption using `/Cynapsa/_drive_sync_manifest.json`.

For each mapping:

1. verify the Drive item is under canonical `ChatGPT Library/Cynapsa`;
2. verify the Library identity when possible;
3. preserve existing Library identity and version history;
4. add the mapping to the unified manifest;
5. do not upload a duplicate merely because the Drive parent moved.

Folder moves in Drive do not change the stable file/folder ID, so ancestry changes alone are not evidence that an item is new.

## Phase 6: inventory canonical Drive

Recursively enumerate the complete canonical Drive root.

Exclude control paths from documentary mirroring:

- `/_sync/**`
- `/_LIBRARY_POLICY.md`

For each canonical content item, determine whether it already has a mapping through:

1. adopted legacy manifest entries;
2. exact Drive ID mapping;
3. verified equivalent native Library item.

When a canonical Drive item already has an equivalent native Library item, adopt that identity instead of creating another mirror.

## Phase 7: classify remaining native Library items

Consider native Library items that are:

- outside `/Google Drive`;
- not already mapped/adopted;
- not protected internal artifacts.

Classify each into one of:

### A. General SharedKnowledgeLibrary ingress

Examples:

- personal documents;
- research;
- generated reports;
- memoir/writing;
- project knowledge;
- general company/business files;
- medical material;
- Cynapsa general knowledge.

### B. Strongly operational or credential-bearing

Examples:

- credential files;
- live tokens/passwords/API keys;
- MCP connection credential references;
- SSH/production connection instructions;
- deployment/rollback runbooks;
- private infrastructure operating procedures.

Do not automatically copy category B into SharedKnowledgeLibrary.

Mark `pending-classification` and report it. Do not silently copy it to `Codex` either unless that write is independently authorized.

### C. Temporary/no-durable-value artifact

Do not automatically discard it. Keep it in native Library and mark it skipped unless the user has established a retention rule.

When uncertain between A and B, prefer pending classification over duplication.

## Phase 8: ingest verified general native items

For each category-A item:

1. Preserve its relative native Library path where reasonable.
2. Search the canonical Drive destination for an existing logical/equivalent item.
3. Use stable identifiers and content/metadata checks, not filename alone.
4. If an equivalent Drive item exists, adopt it into the unified manifest.
5. Otherwise materialize/download the native Library bytes using supported tools.
6. Upload to the canonical Drive path.
7. Preserve the filename and MIME type when practical.
8. Verify the Drive item exists and has plausible byte size/type.
9. Record both identities and the synchronized baseline.
10. Mark origin as `chatgpt-library-upload`, `chatgpt-generated`, or another supported origin.

Do not delete the native source after successful ingress. It becomes the mirror/cache identity.

## Phase 9: create/adopt mirrors for Drive-only items

For canonical Drive content that has no native Library mapping:

1. Create or adopt the corresponding Library folder structure.
2. For stored non-native Drive files, preserve original bytes and filename.
3. For Google-native files use the configured mirror representation:
   - Docs → PDF
   - Sheets → XLSX
   - Slides → PDF
4. Verify the resulting Library file.
5. Record mapping and baseline.

If creation cannot be verified, record failure and continue non-destructively.

## Phase 10: conflict detection

For any item where an old mapping exists but Drive and Library both differ from the last recorded baseline:

- do not overwrite either side;
- mark conflict;
- preserve current data;
- report the exact logical item/path without exposing sensitive content.

Do not resolve by comparing modification timestamps alone.

## Phase 11: write and verify unified manifest

The manifest must contain all verified managed mappings plus pending/conflict states.

Write it only after all intended non-destructive mutations are complete.

Re-read it and verify:

- valid JSON;
- correct root ID;
- unique Drive IDs among managed mappings unless a documented reason exists;
- unique native Library IDs among managed mappings;
- no `/Google Drive` mount items were ingested;
- adopted Medical/Cynapsa mappings retained their existing identities where possible.

## Bootstrap report

Report:

- canonical Drive files/folders discovered;
- native Library files/folders discovered;
- Medical mappings adopted;
- Cynapsa mappings adopted;
- general native items ingested;
- existing Drive equivalents adopted;
- Drive-only items mirrored;
- operational-looking items pending classification;
- conflicts;
- failures;
- skipped/protected items;
- deletion status: **disabled**.

List pending classifications by filename/path, but never expose secret values.

## Success criteria

Bootstrap is successful only if:

1. canonical root and domain boundaries are verified;
2. Medical and Cynapsa legacy mappings are adopted as far as verifiable;
3. no duplicate Drive copies were created for moved folders/items;
4. general ingress items were verified after upload/adoption;
5. Drive-only mirrors were verified when created;
6. manifest was written and re-read successfully;
7. no destructive reconciliation occurred;
8. all unresolved conflicts/classification issues are reported.

After a successful bootstrap, perform a separate full unified reconciliation in no-deletion validation mode before disabling the legacy jobs.
