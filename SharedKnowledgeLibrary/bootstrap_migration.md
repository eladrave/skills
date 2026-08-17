# SharedKnowledgeLibrary Bootstrap Cutover

This is the one-time non-destructive cutover procedure for the Drive-first SharedKnowledgeLibrary architecture.

## Goal

Establish Google Drive `ChatGPT Library`, folder ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`, as the single canonical general library, keep Google Drive `Codex` separate for operational knowledge, and use a neutral Google Drive ingress queue only when an authorized foreground task cannot safely determine a final canonical destination while it still has access to the original file bytes.

No Drive-to-native-Library mirror is created.

No scheduled native ChatGPT Library scan is created.

## Safety

During bootstrap:

- do not delete Drive content;
- do not permanently delete native Library content;
- do not overwrite canonical Drive from native Library or queue state;
- do not guess ambiguous SharedKnowledgeLibrary-versus-Codex classification;
- do not use newest timestamp as a general winner rule;
- do not bulk-migrate native ChatGPT Library without explicit authorization.

## Phase 1: verify canonical Drive structure

Verify:

- `ChatGPT Library` ID `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`;
- child `Medical records` ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`;
- child `Cynapsa` ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`;
- separate `Codex` ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0` is not under the canonical root;
- root `_LIBRARY_POLICY.md` exists and is readable.

## Phase 2: create Drive ingress queue

Create or verify the private Google Drive staging folder:

- `ChatGPT Ingress Queue`
- ID `1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`

The queue is not canonical SharedKnowledgeLibrary content and it is not Codex.

Use it only for authorized durable files whose final destination or ownership is still uncertain in the foreground runtime.

## Phase 3: create ingress control state

Create canonical Drive folder:

`ChatGPT Library/_sync/`

Create:

`_sync/_shared_library_ingress_manifest.json`

If raw JSON file creation is unavailable, a Google Doc named exactly `_shared_library_ingress_manifest.json` containing JSON text is acceptable.

Initialize it with:

- schema version;
- canonical root ID;
- queue folder ID;
- `drive_ingress_queue.items` array;
- historical native-Library mappings only when needed for legacy protection;
- conflicts, failures, and last-run state.

## Phase 4: recognize legacy Medical/Cynapsa mirrors

The old native Library `/Medical records` and `/Cynapsa` trees were Drive-backed convenience copies from retired sync jobs.

If their old `_drive_sync_manifest.json` files are still available, preserve them only as historical evidence that those trees were mirrors.

Do not use those native copies as a recovery source for canonical Drive merely because they exist.

Do not create a recurring native-Library ingress job for them.

## Phase 5: validate direct Drive access

Perform read tests through the connected Drive capability on at least:

- one Medical records source file;
- one Cynapsa source file;
- `_LIBRARY_POLICY.md`.

Perform a safe write/readback test in the canonical root, queue, or `_sync` control area and verify the result.

The architecture is valid only if ChatGPT can read and write canonical Drive directly.

## Phase 6: validate foreground persistence behavior

Verify that a foreground task follows this decision path:

1. if the canonical destination is known, search for an existing logical owner and write or adopt directly in canonical Drive;
2. if durable persistence is authorized but final destination or ownership is uncertain, upload the original file into `ChatGPT Ingress Queue` while the foreground runtime still has access to the bytes;
3. verify the staged Drive file;
4. record queue metadata in the ingress manifest;
5. never rely on native ChatGPT Library retention as the persistence guarantee.

## Phase 7: create optional Drive-only recurring queue processor

Create one recurring task from `scheduledprompt.md` only if recurring reconciliation is desired.

Recommended cadence: hourly.

The task must use Google Drive only.

Its job is to:

- inspect `ChatGPT Ingress Queue`;
- read queue metadata from the manifest;
- search for canonical equivalents;
- adopt verified equivalents;
- otherwise move staged Drive files into canonical destinations while preserving Drive IDs when possible;
- leave operational items pending without copying them into SharedKnowledgeLibrary;
- never call native ChatGPT Library or Files connector actions.

## Phase 8: retire legacy per-folder jobs

After:

- canonical folder structure is verified;
- direct Drive read/write tests pass;
- foreground persistence behavior is validated;
- the optional Drive-only queue processor is created when desired;

then disable, but do not immediately delete:

- `Medical Records Sync`;
- `Sync Cynapsa Drive`.

They are no longer needed because ChatGPT reads Medical records and Cynapsa directly from canonical Drive.

Keep disabled jobs temporarily as rollback references if useful.

## Native Library maintenance

If historical native ChatGPT Library content needs review, perform a manual foreground audit only when explicitly authorized or useful.

A manual audit may materialize a stranded file and write it to canonical Drive or the Drive queue after classification and duplicate checks.

It is maintenance, not recurring architecture.

## Success criteria

Cutover succeeds when:

1. canonical Drive root and subtrees are verified;
2. live policy exists and is readable;
3. `_sync` control state exists;
4. `ChatGPT Ingress Queue` exists and is identified as non-canonical staging;
5. direct canonical Drive read/write is validated;
6. foreground tasks write through to Drive or stage uncertain durable items in the Drive queue;
7. any recurring reconciliation task is Drive-only;
8. legacy per-folder sync jobs are disabled;
9. native ChatGPT Library is not a scheduled dependency;
10. no destructive migration occurred.