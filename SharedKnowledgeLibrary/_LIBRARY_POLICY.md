# SharedKnowledgeLibrary Canonical Policy

This policy governs the canonical Google Drive `ChatGPT Library` tree and the private Drive staging queue used by authorized foreground tasks.

## Canonical root

- Name: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

This Drive tree is the single canonical durable general knowledge library shared across authorized agents.

Canonical subtrees include:

- `Medical records`, ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

Do not create additional Drive copies of these trees for synchronization purposes.

## Separate Codex operational root

Google Drive `Codex`, folder ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`, remains outside SharedKnowledgeLibrary.

Its purpose is operational agent memory such as credentials, private infrastructure connections, deployment and recovery runbooks, MCP connection details, production configuration, and system-operation instructions.

Do not merge `Codex` into `ChatGPT Library` and do not duplicate operational facts across both roots.

## Neutral Drive ingress queue

Google Drive `ChatGPT Ingress Queue`, folder ID `1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`, is private staging only.

It is not canonical SharedKnowledgeLibrary content and it is not Codex.

Use it only when an authorized foreground task already requires durable persistence but cannot safely determine the final canonical destination or ownership classification while it still has access to the original file bytes.

Do not treat queue presence as canonical ownership.

## Ownership model

There are two durable canonical knowledge domains:

1. `ChatGPT Library`: general durable knowledge.
2. `Codex`: operational agent knowledge.

The queue is temporary staging, not a third canonical domain.

The consumer does not determine ownership. Store each durable item according to its purpose.

## Native ChatGPT Library

Native ChatGPT Library is not canonical and does not need to be a mirror of Drive.

It may contain current uploads, generated files, legacy convenience copies, or automatically retained content.

Use it for immediate foreground access when useful, but once a logical item exists in canonical Drive, Drive owns durable state.

There is intentionally no requirement to copy Drive changes back into native ChatGPT Library.

Native ChatGPT Library must not be a scheduled dependency for SharedKnowledgeLibrary reconciliation.

## ChatGPT Web

ChatGPT Web may naturally surface native Library results first. Retrieval order does not determine ownership.

Rules:

1. A current-turn upload may be used immediately as the user's newest supplied source.
2. If the same logical item exists in Drive, Drive owns durable state.
3. When freshness or conflict matters, verify against Drive.
4. If the user asks to persist a current upload or generated artifact and the destination is known, save or adopt it into canonical Drive directly.
5. If durable persistence is authorized but destination or ownership is genuinely uncertain, stage the original file in `ChatGPT Ingress Queue` while the foreground runtime still has access to its bytes.
6. Native Library auto-retention does not create a second authority.

## Direct persistence

A scheduled job is not required for SharedKnowledgeLibrary to work.

When the current authorized task creates or changes durable general knowledge, persist it directly to canonical Drive whenever the destination is known.

Examples include:

- `save this to my Library`;
- `add this to Medical records`;
- `keep this in Cynapsa`;
- update an existing canonical library document;
- create a durable report or artifact that must remain available across agents.

Do not defer a save by assuming a future reconciliation job will recover it.

Installing the skill does not authorize bulk migration of a pre-existing native ChatGPT Library.

## Meaning of “save to my Library”

When SharedKnowledgeLibrary applies, `save this to my Library` means save under canonical Google Drive `ChatGPT Library`, unless the user explicitly asks for native or built-in ChatGPT Library.

## One item, one canonical owner

Before creating or moving a Drive item into canonical storage:

1. search for an existing canonical owner;
2. update, adopt, or move the existing item when appropriate;
3. preserve Drive IDs when possible;
4. avoid parallel `new`, `v2`, `updated`, or date-stamped copies unless they are genuinely separate artifacts;
5. verify the completed write or move.

## Foreground queue staging

Use `ChatGPT Ingress Queue` only when durable persistence is already authorized and the final destination or ownership cannot yet be determined safely.

When staging:

1. preserve the original filename and MIME type when practical;
2. verify the queued Drive file after upload;
3. update `_sync/_shared_library_ingress_manifest.json` only after verification;
4. record the queued Drive file ID, original filename, source, requested domain/path when known, classification when known, staged time, and status;
5. never mark an item canonical merely because it is staged.

If durable persistence is not authorized, do not stage the item merely because ChatGPT retained a native Library copy.

## Scheduled reconciliation

Scheduled reconciliation must be Drive-only.

The scheduled job may read and mutate only the relevant Google Drive surfaces:

- canonical `ChatGPT Library`;
- `_LIBRARY_POLICY.md`;
- `_sync/_shared_library_ingress_manifest.json`;
- `ChatGPT Ingress Queue`.

It must never depend on native ChatGPT Library or Files connector actions.

For each staged queue item:

1. read its queue metadata from the manifest;
2. if metadata is missing, mark `orphan-pending` and do not guess its destination;
3. classify durable general knowledge versus operational versus temporary/ambiguous;
4. for durable general knowledge, determine the canonical destination;
5. search the canonical destination for an existing logical equivalent;
6. adopt an equivalent instead of creating a duplicate;
7. otherwise move the queued Drive file into the canonical destination while preserving its Drive ID when possible;
8. verify file ID, title, MIME type, and destination parent;
9. only then mark it `managed` or `adopted` in the manifest.

A queue item or native Library copy never automatically overwrites canonical Drive.

## Operational classification boundary

Strong Codex-owned examples include:

- live passwords, tokens, API keys, private keys, secret-bearing URLs;
- SSH and production connection procedures;
- private infrastructure host details;
- deployment, rollback, recovery, or system-operation runbooks;
- MCP connection credentials;
- production configuration ownership;
- durable instructions whose purpose is allowing agents to operate a system.

Do not move such items into SharedKnowledgeLibrary.

If they are already in the neutral queue, leave them there as `pending-operational` and notify only without exposing secret values.

Do not silently move them into Codex unless the user or an applicable operational workflow explicitly authorizes that write.

## Temporary or ambiguous items

If the durable purpose, ownership, or canonical destination cannot be established safely, leave the staged item in the neutral queue as `pending-ambiguous` rather than guessing.

Do not repeatedly notify for an unchanged pending item.

## Native Library audits

Reading or searching native ChatGPT Library does not itself authorize copying those files into Drive.

Native Library audits may be performed interactively in a foreground conversation when explicitly useful, for example to find a suspected stranded file.

Such audits are maintenance only, not scheduled architecture.

If an authorized interactive audit finds a file that must be durably persisted:

1. classify it;
2. search Drive for an existing logical equivalent;
3. adopt the existing Drive item if equivalent;
4. otherwise materialize it in the foreground runtime;
5. write it directly to canonical Drive when the destination is known;
6. or stage it in `ChatGPT Ingress Queue` when durable persistence is authorized but destination remains uncertain;
7. verify the Drive result before updating control state.

Do not schedule native Library audits and do not bulk-migrate native Library without explicit authorization.

## Legacy Medical Records and Cynapsa native copies

The native Library `/Medical records` and `/Cynapsa` trees were created by older Drive-to-Library jobs.

They are legacy convenience copies only.

Do not recreate missing Drive files from those native mirrors merely because the mirror exists. Drive owns those trees.

The old per-folder Drive-to-Library jobs are unnecessary and should remain disabled.

On a new ChatGPT installation, do not recreate those legacy jobs.

## Medical records

`ChatGPT Library/Medical records` in Drive is authoritative.

When explicitly asked to save or update medical records, write directly there and verify the write.

Freshness-sensitive retrieval should verify Drive rather than relying solely on a legacy native Library copy.

## Cynapsa

`ChatGPT Library/Cynapsa` in Drive is authoritative for general Cynapsa business, investor, product, market, and project knowledge.

Operational credentials and infrastructure runbooks belong in `Codex` when their primary purpose is operating systems.

## Ingress control data

Keep reconciliation control data under:

`_sync/`

Recommended manifest:

`_sync/_shared_library_ingress_manifest.json`

Track:

- canonical root metadata;
- historical native-Library migration/adoption mappings when needed for legacy protection;
- `drive_ingress_queue.folder_id`;
- `drive_ingress_queue.items` with queued Drive identity, source, requested destination, classification, status, and canonical mapping when resolved;
- conflicts and failures;
- last verified run state.

The manifest is control metadata, not documentary evidence.

## Deletion model

Scheduled reconciliation must never delete canonical Drive content.

Ordinary queue processing must not permanently delete queue items either.

Native Library deletion, move, rename, or edit never authorizes deleting, moving, renaming, or overwriting canonical Drive.

Canonical Drive deletion does not need to propagate to native Library because native Library is not maintained as an authoritative mirror.

## Duplicate and conflict handling

Never use newest timestamp as a general conflict-resolution rule.

Before moving or adopting a queued item:

1. check the manifest by queued Drive file ID;
2. search the canonical destination;
3. compare path/name, size, MIME/type, and available content, hash, or revision evidence;
4. adopt an equivalent instead of duplicating it;
5. if equivalence is ambiguous, mark a conflict and leave the queued file in place.

## Privacy

Treat library and queue content as private unless explicitly designated otherwise.

Use the minimum necessary information. Avoid exposing credentials or operational secrets in SharedKnowledgeLibrary or queue notifications.

## Failure behavior

For direct authorized writes, verify Drive before claiming persistence.

For queue reconciliation, fail closed on ambiguous classification, unresolved duplicate identity, or unverified Drive mutations.

If Drive itself is temporarily unavailable, retry the failed read once after fresh Drive action discovery when possible, then end without mutations if it still fails.

Do not fall back to native ChatGPT Library as a scheduled recovery path.

## Governing rule

**Google Drive `ChatGPT Library` is the single canonical general library. Google Drive `Codex` is the separate canonical operational library. Foreground write-through to Drive is the correctness path. `ChatGPT Ingress Queue` is private Drive staging for authorized durable items whose final destination is uncertain. Scheduled reconciliation is Drive-only. Native ChatGPT Library is immediate foreground access and optional interactive maintenance, never a scheduled dependency or competing authority.**