# SharedKnowledgeLibrary Canonical Policy

This policy governs the canonical Google Drive `ChatGPT Library` tree.

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

## Ownership model

There are two durable knowledge domains:

1. `ChatGPT Library`: general durable knowledge.
2. `Codex`: operational agent knowledge.

The consumer does not determine ownership. Store each durable item according to its purpose.

## Native ChatGPT Library

Native ChatGPT Library is not canonical and does not need to be a mirror of Drive.

It may contain:

- current uploads;
- ChatGPT-generated files;
- legacy copies created by older sync jobs;
- content that has not yet been persisted to Drive.

Use it for immediate access when useful, but once a logical item exists in canonical Drive, Drive owns durable state.

There is intentionally no requirement to copy Drive changes back into native ChatGPT Library.

## ChatGPT Web

ChatGPT Web may naturally surface native Library results first. Retrieval order does not determine ownership.

Rules:

1. A current-turn upload may be used immediately as the user's newest supplied source.
2. If the same logical item exists in Drive, Drive owns durable state.
3. When freshness or conflict matters, verify against Drive.
4. If the user asks to persist a current upload or generated artifact, save/adopt it into Drive directly.
5. Native Library auto-retention does not create a second authority.

## Direct persistence

A scheduled job is not required for SharedKnowledgeLibrary to work.

When the current authorized task creates or changes durable general knowledge, persist it directly to canonical Drive whenever possible.

Examples include:

- `save this to my Library`;
- `add this to Medical records`;
- `keep this in Cynapsa`;
- update an existing canonical library document;
- create a durable report/artifact that must remain available across agents.

Do not defer a save by assuming a future sync will handle it.

Installing the skill does not authorize bulk migration of a pre-existing native ChatGPT Library.

## Meaning of “save to my Library”

When SharedKnowledgeLibrary applies, `save this to my Library` means save under canonical Google Drive `ChatGPT Library`, unless the user explicitly asks for native/built-in ChatGPT Library.

## One item, one canonical owner

Before creating a Drive item:

1. search for an existing canonical owner;
2. update or move the existing item when appropriate;
3. preserve Drive IDs when possible;
4. avoid parallel `new`, `v2`, `updated`, or date-stamped copies unless they are genuinely separate artifacts;
5. verify the completed write.

## Ordinary reads do not migrate data

Reading or searching native ChatGPT Library does not itself authorize copying those files into Drive.

Bulk migration requires an explicitly authorized bootstrap workflow. Per-item persistence requires a user request or authorized workflow that calls for durable storage.

## Optional ingress reconciliation

A scheduled reconciliation task may be deployed as catch-up insurance for native-Library-only files that were created in unrelated chats.

It is **ingress-only** from native Library into canonical Drive.

It does not mirror Drive back into native Library.

For each untracked native Library item considered by the authorized job:

1. exclude `/Google Drive/**` and protected/connector-backed surfaces;
2. determine whether it is durable general knowledge;
3. classify SharedKnowledgeLibrary versus Codex;
4. search Drive for an existing logical equivalent;
5. adopt an equivalent instead of duplicating it;
6. otherwise create it in the correct canonical Drive path;
7. verify the Drive result;
8. record an ingress mapping;
9. from then on, Drive is authoritative.

A changed native copy of an already-mapped item does not automatically overwrite Drive.

## Legacy Medical Records and Cynapsa native copies

The native Library `/Medical records` and `/Cynapsa` trees were created by older Drive-to-Library jobs.

They are legacy convenience copies only.

During cutover, use their legacy `_drive_sync_manifest.json` files solely to recognize those Library identities as existing Drive-backed copies so the new ingress job does not upload them back into Drive as duplicates.

Once those mappings are adopted, the old per-folder Drive-to-Library jobs are unnecessary and should remain disabled.

On a new ChatGPT installation, do not recreate those legacy jobs.

## Medical records

`ChatGPT Library/Medical records` in Drive is authoritative.

When explicitly asked to save or update medical records, write directly there.

Freshness-sensitive retrieval should verify Drive rather than relying solely on a legacy native Library copy.

## Cynapsa

`ChatGPT Library/Cynapsa` in Drive is authoritative for general Cynapsa business, investor, product, market, and project knowledge.

Operational credentials and infrastructure runbooks belong in `Codex` when their primary purpose is operating systems.

## Codex classification boundary

Strong Codex-owned examples include:

- live passwords, tokens, API keys, private keys, secret-bearing URLs;
- SSH and production connection procedures;
- private infrastructure host details;
- deployment/rollback/recovery runbooks;
- MCP connection credentials;
- production configuration ownership;
- durable instructions whose purpose is allowing agents to operate a system.

Do not ingest such items into SharedKnowledgeLibrary. Do not silently copy them into Codex unless the user or applicable operational workflow authorizes that write.

## Ingress control data

If catch-up reconciliation is deployed, keep control data under:

`_sync/`

Recommended manifest:

`_sync/_shared_library_ingress_manifest.json`

Track native Library identity, canonical Drive identity/path, origin, last verified state, and status. The manifest is control metadata, not documentary evidence.

The absence of `_sync/` is valid when no reconciliation job exists.

## Deletion model

The ingress job must never delete canonical Drive content.

Native Library deletion, move, rename, or edit never authorizes deleting, moving, renaming, or overwriting canonical Drive.

Canonical Drive deletion does not need to propagate to native Library because native Library is not maintained as a canonical mirror.

Ordinary ingress should not permanently delete anything from either surface.

## Duplicate and conflict handling

Never use newest timestamp as a general conflict-resolution rule.

Before ingress creation:

1. check the manifest by native Library ID;
2. search the canonical destination;
3. compare path/name, size, MIME/type, and available content/hash/revision evidence;
4. adopt an equivalent instead of duplicating it;
5. if equivalence is ambiguous, mark/report a conflict rather than guessing.

## Privacy

Treat all library content as private unless explicitly designated otherwise.

Use the minimum necessary information. Avoid copying credentials or operational secrets into SharedKnowledgeLibrary when they belong in Codex.

## Failure behavior

For direct authorized writes, verify Drive before claiming persistence.

For optional ingress reconciliation, fail closed on ambiguous classification or duplicate identity. Do not overwrite canonical Drive from native Library drift.

## Governing rule

**Google Drive `ChatGPT Library` is the single canonical general library. Google Drive `Codex` is the separate canonical operational library. Native ChatGPT Library is immediate access and optional ingress only. Direct authorized Drive persistence is the correctness path; reconciliation is catch-up insurance, never a competing sync authority.**