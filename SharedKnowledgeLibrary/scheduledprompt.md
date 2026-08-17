# SharedKnowledgeLibrary Drive Ingress Queue Processor

This prompt defines the optional recurring reconciliation task for SharedKnowledgeLibrary.

Its purpose is narrow: process files that an authorized foreground task already staged in the private Google Drive `ChatGPT Ingress Queue`, then adopt or move them into the correct canonical Google Drive location after classification and duplicate checks.

This scheduled task must use **Google Drive only**. It must never depend on native ChatGPT Library or the Files connector.

## Canonical Drive root

- Folder: `ChatGPT Library`
- ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Included canonical subtrees include:

- `Medical records`, ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

Separate operational root, never treated as general library content:

- `Codex`, ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`

## Neutral queue

- Folder: `ChatGPT Ingress Queue`
- ID: `1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`

The queue is private staging only. It is not canonical SharedKnowledgeLibrary content and it is not Codex.

## Live policy and control state

Before making changes:

1. Read `_LIBRARY_POLICY.md` from canonical Drive `ChatGPT Library`.
2. Read `_sync/_shared_library_ingress_manifest.json` as control state.
3. Use `drive_ingress_queue.items` in the manifest as authoritative queue metadata.

The manifest may be a Google Doc containing JSON text when raw-file creation is unavailable. Treat its text as JSON control data.

## Scheduled dependency rule

The scheduled job may depend only on Google Drive.

Do not call or require:

- native ChatGPT Library;
- `files.list`;
- `files.search`;
- `files.materialize`;
- any Drive-to-native-Library synchronization mechanism.

Foreground tasks are responsible for persisting original bytes into canonical Drive or the neutral Drive queue while those bytes are available.

## Core rules

1. Google Drive `ChatGPT Library` is canonical general knowledge.
2. Google Drive `Codex` is the separate operational domain.
3. `ChatGPT Ingress Queue` is temporary staging only.
4. Native ChatGPT Library is not part of this scheduled workflow.
5. Never copy Drive content back into native Library.
6. Never delete or overwrite canonical Drive because of queue or native Library state.
7. Never use newest timestamp as a general winner rule.
8. Search for an existing logical equivalent before moving a queued item into canonical Drive.
9. Preserve Drive file IDs when possible by moving the existing queued Drive file rather than downloading and re-uploading it.
10. Operational or credential-bearing items must not be moved into SharedKnowledgeLibrary.

## Queue inventory

List up to 100 direct items in `ChatGPT Ingress Queue`.

If 100 items are returned, treat a backlog as potentially remaining and process a safe bounded subset, then continue on later runs.

Never delete queue files as ordinary cleanup.

## Queue metadata

Each staged item should have a manifest entry containing at least:

- queued Drive file ID;
- original filename;
- source, such as current upload or generated artifact;
- requested domain/path when known;
- canonical destination folder ID/path when known;
- classification when known;
- staged time;
- status.

If a physical queue file has no manifest entry:

1. do not guess its destination;
2. record it once as `orphan-pending`;
3. notify the user because foreground staging metadata is missing;
4. leave the file in the queue.

## Classification

Use one of these classifications:

### A. Durable general knowledge

Examples:

- personal/reference documents;
- research;
- memoir/writing;
- project/business material;
- medical material;
- Cynapsa general knowledge;
- durable generated reports or artifacts.

Category A may move into canonical SharedKnowledgeLibrary once the destination is verified.

### B. Operational or credential-bearing

Examples:

- passwords, tokens, API keys, private keys, secret-bearing URLs;
- MCP connection details;
- SSH or production connection instructions;
- private infrastructure details;
- deployment, rollback, recovery, or system-operation runbooks.

Do not move category B into SharedKnowledgeLibrary.

Leave it in the neutral queue as `pending-operational` and notify once without exposing secret values.

Do not move it into `Codex` unless the user or an applicable operational workflow explicitly authorizes that write.

### C. Temporary or ambiguous

Examples may include throwaway previews, transient intermediates, obvious duplicates, or files whose durable purpose cannot be established safely.

Leave them in the queue as `pending-ambiguous` when a decision is required. Do not repeatedly notify for an unchanged pending item.

When uncertain, prefer pending over guessing.

## Reconciliation workflow

For each queue entry that is not already resolved:

1. Confirm the queued Drive file still exists.
2. Confirm its manifest metadata.
3. Determine or verify classification.
4. For durable general knowledge, determine the canonical destination folder ID/path.
5. Search the canonical destination for an existing logical equivalent using filename/path plus available size, MIME/type, content, hash, or revision evidence.
6. If an equivalent exists, record `adopted` with the canonical Drive file ID and do not create a duplicate.
7. If no equivalent exists, move the queued Drive file into the canonical destination using Drive parent metadata so the same Drive file ID is preserved when possible.
8. Verify the resulting file ID, title, MIME type, and destination parent.
9. Only after verification, mark the entry `managed` and record the canonical Drive identity/path.
10. Never overwrite a canonical item from queue content.

## Already tracked items

Do not repeat work or alerts for entries already marked:

- `managed`;
- `adopted`;
- `pending-operational`;
- `pending-ambiguous`;
- `orphan-pending`.

Reconsider them only when the Drive file, manifest entry, or explicit user classification decision materially changes.

## Folder creation

Create missing canonical Drive folders only when necessary for a verified durable general-knowledge destination.

Before creating a folder, check for an existing folder with the intended name/path.

Do not reorganize unrelated canonical Drive content.

## Duplicate and conflict handling

Before moving or adopting a queue item:

1. check the manifest by queued Drive file ID;
2. search the canonical destination;
3. compare path/name, size, MIME/type, and available content/hash/revision evidence;
4. adopt an equivalent instead of duplicating it;
5. if equivalence is ambiguous, mark `conflict` and leave the queued file in place.

Never use newest timestamp as a general conflict-resolution rule.

## Failure behavior

If Drive access fails, destination identity is ambiguous, a move cannot be verified, or duplicate identity is unresolved:

- fail closed;
- do not guess;
- do not overwrite or delete canonical Drive;
- leave the queued source in place;
- record failure or pending state when possible;
- continue only with independent safe items.

If Google Drive itself is temporarily unavailable, retry the specific failed read once after fresh Google Drive action discovery when possible. If it still fails, end without mutations.

Notify only after 3 consecutive scheduled Drive-runtime failures, because Google Drive is the only scheduled dependency.

## Manifest update behavior

Update the manifest only after verified results.

Record a concise `last_run` summary with counts for:

- queue items discovered;
- managed;
- adopted;
- pending operational;
- pending ambiguous;
- orphan pending;
- conflicts;
- failures;
- whether a backlog may remain.

The manifest is control metadata, not documentary evidence.

## Report behavior

Notify the user only when at least one of these occurs:

- files were moved into canonical Drive;
- existing canonical equivalents were adopted;
- a new operational classification needs attention;
- a new ambiguous item actually requires a decision;
- an orphan, conflict, or failure was found;
- a meaningful queue backlog may remain;
- Google Drive has failed for 3 consecutive scheduled runs.

If the queue is empty or every item is unchanged and resolved, do not notify.

Never expose secret values.

## Absolute safety rule

**This task may adopt or move staged Google Drive files into canonical SharedKnowledgeLibrary, but it must never depend on native ChatGPT Library and must never let queue or native Library state authorize deletion, overwrite, or destructive modification of canonical Drive.**