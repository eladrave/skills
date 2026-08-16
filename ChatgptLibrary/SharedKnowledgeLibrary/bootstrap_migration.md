# SharedKnowledgeLibrary Bootstrap Cutover

This is the one-time non-destructive cutover procedure for the ingress-only SharedKnowledgeLibrary architecture.

## Goal

Establish Google Drive `ChatGPT Library`, folder ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`, as the single canonical general library while ensuring existing native ChatGPT Library content is not lost or accidentally re-uploaded as duplicates.

No Drive-to-native-Library mirror is created.

## Safety

During bootstrap:

- do not delete Drive content;
- do not permanently delete native Library content;
- do not overwrite canonical Drive from native Library;
- do not guess ambiguous SharedKnowledgeLibrary-vs-Codex classification;
- do not use newest timestamp as a general winner rule.

## Phase 1: verify canonical Drive structure

Verify:

- `ChatGPT Library` ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`;
- child `Medical records` ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`;
- child `Cynapsa` ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`;
- separate `Codex` ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0` is not under the canonical root;
- root `_LIBRARY_POLICY.md` exists and is readable.

## Phase 2: create ingress control state

Create canonical Drive folder:

`ChatGPT Library/_sync/`

Create:

`_sync/_shared_library_ingress_manifest.json`

If raw JSON file creation is unavailable, a Google Doc named exactly `_shared_library_ingress_manifest.json` containing JSON text is acceptable.

Initialize with:

- schema version;
- canonical root ID;
- `cutover_at` UTC timestamp;
- legacy native subtrees `/Medical records` and `/Cynapsa`;
- hard exclusion `/Google Drive`;
- mappings/adoptions added by later ingress processing.

## Phase 3: recognize legacy Medical/Cynapsa mirrors

Locate:

- `/Medical records/_drive_sync_manifest.json`
- `/Cynapsa/_drive_sync_manifest.json`

These old manifests prove that the pre-cutover native `/Medical records` and `/Cynapsa` trees were Drive-backed copies.

It is not necessary to reproduce every old mapping in the new manifest. Instead:

1. verify both legacy manifests reference the expected stable Drive folder IDs;
2. record in the new manifest that native content already present in those two subtrees at/before `cutover_at` is `legacy-drive-mirror` and must not be ingested back into Drive;
3. preserve the old manifests in native Library for rollback/history, but exclude them from future ingress.

New native files created after `cutover_at` under those paths may be considered for ingress normally.

## Phase 4: inventory existing native Library backlog

Recursively enumerate native ChatGPT Library with pagination.

Hard exclude:

- `/Google Drive/**`;
- the two legacy `_drive_sync_manifest.json` files;
- protected/internal artifacts that cannot safely be materialized.

Classify remaining pre-existing items into:

- durable general knowledge, eligible backlog ingress;
- strongly operational/credential-bearing, pending classification for Codex;
- temporary/ambiguous, skipped without deletion.

Do not require the entire backlog to be migrated in one cutover transaction. The recurring ingress task may process a bounded backlog safely over later runs.

## Phase 5: validate direct Drive access

Perform read tests through the connected Drive capability on at least:

- one Medical records source file;
- one Cynapsa source file;
- `_LIBRARY_POLICY.md`.

Perform a safe write/readback test in the canonical root or `_sync` control area and verify the result.

The architecture is valid only if ChatGPT can read canonical Drive directly, because Drive-to-native mirroring is intentionally retired.

## Phase 6: create recurring ingress task

Create one recurring catch-up task from `scheduledprompt.md`.

Recommended cadence: hourly.

Its job is only native-Library-to-Drive ingress for files that were not directly persisted by the agent handling them.

## Phase 7: retire legacy per-folder jobs

After:

- canonical folder structure is verified;
- legacy mirrors are marked by cutover boundary;
- direct Drive read/write tests pass;
- the unified ingress task is created;

then disable, but do not immediately delete:

- `Medical Records Sync`;
- `Sync Cynapsa Drive`.

They are no longer needed because ChatGPT reads Medical records and Cynapsa directly from canonical Drive.

Keep the disabled jobs temporarily as rollback references.

## Success criteria

Cutover succeeds when:

1. canonical Drive root and subtrees are verified;
2. live policy exists and is readable;
3. `_sync` ingress state exists;
4. legacy Medical/Cynapsa native copies cannot be mistaken for new ingress;
5. direct canonical Drive read/write is validated;
6. one unified recurring ingress task exists;
7. legacy per-folder sync jobs are disabled;
8. no destructive migration occurred;
9. unresolved operational-looking native files remain pending rather than duplicated.