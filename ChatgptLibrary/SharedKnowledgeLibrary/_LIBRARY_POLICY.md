# SharedKnowledgeLibrary Canonical Policy

This file is intended to live at the root of the canonical Google Drive `ChatGPT Library` folder.

## Canonical root

- Name: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

This Drive tree is the canonical durable general knowledge library shared across ChatGPT, Codex, Codex CLI, and other authorized agents.

The architecture must remain useful even when no native-ChatGPT-Library reconciliation task exists.

## Included canonical subtrees

As of 2026-08-16, the existing folders below were moved under this root without changing their Drive IDs:

- `Medical records`, ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

These are first-class canonical subtrees of SharedKnowledgeLibrary.

Do not create additional Drive copies of these trees for synchronization purposes.

## Separate Codex operational root

The Google Drive `Codex` folder remains outside SharedKnowledgeLibrary.

- Folder ID: `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`

Its purpose is operational agent memory: credentials, private infrastructure connection details, deployment instructions, recovery runbooks, system-management procedures, and similar material used to operate the user's environments.

Do not merge `Codex` into `ChatGPT Library`.

Do not duplicate operational facts into both roots.

## Ownership model

There are two durable knowledge domains:

1. `ChatGPT Library`: general durable knowledge.
2. `Codex`: operational agent knowledge.

The consumer does not determine ownership. ChatGPT may read Codex operational information when authorized, and Codex may read SharedKnowledgeLibrary material when relevant.

Store each durable item according to its purpose.

## Native ChatGPT Library

Native ChatGPT Library is a product surface, not the canonical durable store for this architecture.

It serves up to three roles:

1. immediate access to uploads and ChatGPT-generated files;
2. a convenient mirror/cache of canonical Drive content when reconciliation exists;
3. an ingress/staging area for newly created content that has not yet been persisted into canonical Drive.

Once a native-Library item corresponds to a canonical Drive item, Drive owns the durable state.

Retrieval order does not change ownership.

## Reconciliation is optional

A scheduled reconciliation task is not required for SharedKnowledgeLibrary to function.

Without such a task:

- agents read canonical knowledge directly from Drive;
- authorized durable saves and updates are written directly to Drive during the current task;
- native-Library-only content created in unrelated chats may remain local until explicitly saved or migrated.

With such a task:

- the same direct read/write behavior continues;
- reconciliation acts only as catch-up and mirror maintenance for content that was not directly persisted.

If reconciliation status is unknown, assume no future job will persist current content. Complete an authorized durable Drive save directly whenever possible.

Never defer a save by saying or assuming that "the sync will handle it" unless a relevant task has actually been verified and delay is intentional.

## Persistence authorization

Installation of the skill does not authorize bulk migration of the existing native ChatGPT Library.

Direct persistence to canonical Drive is authorized when the current user request or active authorized workflow calls for durable storage, for example:

- `save this to my Library`;
- `add this to Medical records`;
- `keep this in Cynapsa`;
- update an existing canonical library document;
- create a durable report/artifact that the requested workflow explicitly requires to remain available across agents.

Do not automatically store every response, temporary artifact, incidental upload, or native Library file merely because it exists.

Bulk bootstrap migration and recurring catch-up reconciliation are distinct actions that require explicit authorization.

## ChatGPT Web

ChatGPT Web may naturally surface native Library results before Drive results.

That behavior is acceptable for immediate access, but native Library retrieval must not silently override canonical Drive state.

Rules:

1. A current-turn user upload may be used immediately as the user's newest supplied source.
2. If the same logical item already exists in canonical Drive, Drive owns durable state.
3. When freshness or conflict matters, verify against Drive.
4. If the user asks to persist the current upload or generated artifact, save/adopt it into Drive now rather than waiting for reconciliation.
5. Native Library auto-retention by ChatGPT does not create a second canonical owner.

## "Save to my Library"

When the SharedKnowledgeLibrary skill is active, an instruction such as `save this to my Library` means save the durable item under canonical Google Drive `ChatGPT Library`, unless the user explicitly says native/built-in ChatGPT Library.

ChatGPT may also retain its automatic native Library copy. That is cache/ingress, not another authority.

## One item, one canonical owner

Do not maintain authoritative copies of the same logical item in multiple Drive locations.

Before creating a new Drive item:

1. search for an existing canonical owner;
2. update or move the existing item when appropriate;
3. preserve Drive IDs when possible;
4. avoid names such as `new`, `v2`, `updated`, or date-stamped copies unless they are genuinely separate artifacts;
5. verify the completed write.

## Direct-write rule

When an authorized current task creates or changes durable general knowledge, prefer direct canonical Drive persistence.

A scheduled job is not part of the correctness path for a save the current agent can perform itself.

For ChatGPT-generated files that may also appear automatically in native Library:

1. determine the intended canonical Drive destination;
2. search for an existing equivalent Drive item;
3. create or update exactly one canonical Drive item;
4. verify it;
5. allow any native Library copy to remain merely as cache/ingress.

Do not upload duplicate Drive copies merely because native Library also contains the file.

## Ordinary reads do not migrate data

Reading or searching native ChatGPT Library does not itself authorize copying those files into Drive.

Do not sweep, migrate, or classify the user's entire native Library during an ordinary question simply because SharedKnowledgeLibrary is installed.

A pre-existing native Library is migrated only through an explicitly authorized bootstrap/migration workflow or explicit per-item save.

## Optional unified reconciliation model

If the user deploys reconciliation, use one unified process for the entire canonical Drive tree and native ChatGPT Library.

The process is asymmetric rather than normal two-way sync.

### Drive to native Library

Drive is authoritative for mapped items.

The reconciler may:

- create native Library mirrors for new canonical Drive files;
- update mirrors when Drive content changes;
- move/rename mirrors when canonical Drive items move or rename;
- move mapped native mirrors to Library trash after a canonical Drive deletion, but only after a complete successful Drive scan.

### Native Library to Drive

Only new untracked native Library items considered by an authorized migration/reconciliation process are ingress candidates.

For an untracked item:

1. determine whether it belongs to SharedKnowledgeLibrary or the separate Codex domain;
2. search for an equivalent Drive item;
3. adopt an existing equivalent rather than duplicate it;
4. otherwise create it in the corresponding canonical Drive path;
5. verify the Drive result;
6. record the mapping;
7. from then on, Drive is authoritative.

A mapped native Library item's subsequent content change, rename, move, or deletion does not automatically mutate Drive.

## Conflict model

When reconciliation exists, maintain a last-successful baseline for each mapped item.

- Drive changed, native mirror unchanged: refresh the mirror from Drive.
- Drive unchanged, mapped native mirror changed: do not overwrite Drive. Restore/refresh the native mirror or report drift.
- Both changed independently: conflict. Preserve both current states and report it.
- Native item is new and untracked: ingress candidate only within an authorized migration/reconciliation workflow.
- Drive item is new and unmapped: canonical immediately, mirror/adopt if reconciliation exists.

Never use newest timestamp as a general conflict-resolution rule.

## Deletion model

Deletion is asymmetric by design.

### Drive deletion

A verified canonical Drive deletion may cause the corresponding native Library mirror to be moved to Library trash after complete successful reconciliation.

Do not infer deletion from partial, failed, truncated, or ambiguous Drive enumeration.

### Native Library deletion

Deleting a native Library mirror never deletes the canonical Drive item.

The reconciler may recreate the mirror later if reconciliation is deployed.

Ordinary reconciliation must never permanently delete content from either system.

## Medical records

The `Medical records` Drive subtree is authoritative for medical-document storage.

If the user explicitly asks to store a medical document or update medical library information, write directly into this canonical subtree when possible.

A reconciliation workflow may also ingest a new untracked native Library file under `/Medical records`, but direct persistence is preferred for current authorized work.

Medical-record-specific skills may continue using native Library `/Medical records` for retrieval convenience, but when freshness or conflict matters they must respect canonical Drive.

## Cynapsa

The `Cynapsa` Drive subtree is authoritative for Cynapsa general business/project knowledge.

If the user explicitly asks to retain or update Cynapsa general knowledge, write directly into the canonical subtree when possible.

A reconciliation workflow may also ingest new untracked native Library content under `/Cynapsa`.

Operational secrets and system-operation runbooks for Cynapsa belong in the separate `Codex` root when their primary purpose is infrastructure operation.

## Codex classification boundary

Strong examples of Codex-owned content include:

- live passwords, access tokens, API keys, private keys, or secret-bearing URLs;
- SSH and production connection procedures;
- private infrastructure host details;
- container deployment/rollback runbooks;
- production configuration ownership;
- MCP connection credentials;
- recovery and incident operating procedures;
- durable instructions whose purpose is allowing an agent to operate a system.

If a newly discovered native Library file strongly appears to be Codex-owned, do not auto-copy it into SharedKnowledgeLibrary.

Do not silently move it into Codex unless the current user request or applicable operational skill authorizes that write.

## Control data

If reconciliation is deployed, keep control data under a reserved canonical Drive path such as:

`_sync/`

Recommended manifest:

`_sync/_shared_library_manifest.json`

Control files are not documentary evidence and should normally be excluded from the user-facing native Library mirror.

The root `_LIBRARY_POLICY.md` is also a policy document and does not need to appear as a normal native Library content item.

The absence of `_sync/` or a manifest is valid when no reconciliation system is deployed.

## Existing legacy manifests

The current native Library `/Medical records/_drive_sync_manifest.json` and `/Cynapsa/_drive_sync_manifest.json` contain useful identity mappings from the existing one-way jobs.

If the user performs unified cutover:

1. read and adopt those mappings into the unified manifest;
2. do not recreate mapped Library files unnecessarily;
3. preserve current Library identities and version history when possible;
4. keep the old manifests until unified reconciliation has been validated;
5. after cutover they may be ignored or retired, but not used as documentary evidence.

These legacy manifests are irrelevant on a fresh ChatGPT installation that never had those mirror jobs.

## Existing sync jobs

The existing `Medical Records Sync` and `Sync Cynapsa Drive` jobs may remain enabled during transition because they reference stable Drive folder IDs and still enforce Drive as source of truth.

Do not disable them until:

1. their mappings have been adopted;
2. the unified reconciler has completed a full no-deletion validation run;
3. the resulting Drive and native Library identities have been verified;
4. the unified task is ready to take ownership.

At cutover, disable the old jobs rather than deleting them immediately.

On a new ChatGPT installation, do not recreate these legacy per-folder tasks. They are not needed for canonical Drive access.

## Google-native Drive files

The canonical Google-native item remains the owner.

For native ChatGPT Library mirrors, use consistent exported representations unless the item requires something else:

- Docs → PDF
- Sheets → XLSX
- Slides → PDF

Do not upload that export back into Drive as a second canonical copy.

## Privacy

All library content is private unless explicitly stated otherwise.

Use the minimum necessary information for the current task.

Avoid copying credentials or operational secrets into SharedKnowledgeLibrary when they belong in Codex.

Do not expose sensitive values in summaries, logs, GitHub skill files, or synchronization reports.

## Failure behavior

For direct authorized writes:

- verify the Drive mutation before claiming persistence;
- if Drive write capability is unavailable, state that the item was not persisted rather than relying on a hypothetical sync.

For reconciliation:

- fail closed on deletion and overwrites;
- if Drive or Library inventory is incomplete, truncated, ambiguous, inaccessible, or any required mutation cannot be verified, do not perform deletion reconciliation;
- do not overwrite conflicts;
- preserve existing mappings;
- report the blocker.

Partial successful non-destructive imports may be reported separately when verified.

## No automatic installation, migration, or scheduling

The existence of this policy or skill source does not authorize:

- installing the skill;
- bulk-migrating native ChatGPT Library;
- creating a scheduled reconciliation job;
- disabling legacy jobs.

Each is a separate user-authorized action.

## Governing rule

**Google Drive `ChatGPT Library` is the single canonical general library. Google Drive `Codex` is the separate canonical operational library. Native ChatGPT Library is immediate access, cache/mirror, and optional ingress. Direct authorized Drive persistence is the correctness path; reconciliation is optional catch-up infrastructure.**
