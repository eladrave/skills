---
name: shared-knowledge-library
description: 'Use the Google Drive folder "ChatGPT Library" as the single canonical shared general-knowledge library for ChatGPT, Codex, Codex CLI, and other authorized agents. Read and write durable general knowledge directly in Drive. Treat native ChatGPT Library only as immediate-access storage and an ingress source for uploads or generated files that have not yet been persisted to Drive. Never require Drive content to be mirrored back into native ChatGPT Library. Keep the separate Google Drive "Codex" folder outside this library for credentials, infrastructure, deployment runbooks, private connection details, and other operational agent memory. Use one durable item, one canonical owner, and never create competing copies across SharedKnowledgeLibrary and Codex.'
---

# Shared Knowledge Library

Use the Google Drive `ChatGPT Library` tree as the single canonical durable general knowledge base shared across authorized agents.

## Canonical root

- Name: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`
- URL: `https://drive.google.com/drive/folders/1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Treat the folder ID as stable.

Canonical subtrees include:

- `Medical records`, folder ID `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa`, folder ID `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

These folders were moved under the canonical root without changing their Drive IDs.

## Separate Codex operational root

The Google Drive folder `Codex`, ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`, remains deliberately separate.

Use `CodexAsKnowledgeReadWrite` for operational knowledge such as credentials, private infrastructure connections, deployment and recovery runbooks, MCP connection details, production configuration, and instructions whose purpose is operating systems.

SharedKnowledgeLibrary answers: **what durable general information do we know?**

Codex answers: **how do authorized agents operate the user's systems?**

The consumer does not determine ownership. Do not duplicate an item across both roots merely because multiple agents may need it.

## Transport independence

This skill defines storage and ownership semantics, not the connector implementation.

Use whatever authorized Google Drive capability exists in the current environment. Do not require a custom MCP server.

If Drive access is unavailable, state that limitation and do not invent private library content.

## Live policy

Before a non-trivial write, migration, or reconciliation operation, read `_LIBRARY_POLICY.md` from the canonical Drive root when available.

The Drive copy is the live shared policy. The GitHub copy is version-controlled source.

Current explicit user instructions override older policy text.

## Core source-of-truth rule

Google Drive is canonical.

Native ChatGPT Library is **not** a mirror that must be kept synchronized from Drive. It serves only:

1. immediate access to uploads and ChatGPT-generated artifacts;
2. legacy local copies that may already exist;
3. ingress/staging for durable files that have not yet been persisted to canonical Drive.

There is intentionally no requirement to copy canonical Drive changes back into native ChatGPT Library.

This removes duplicate authorities and avoids Drive-to-Library transfer limitations.

## ChatGPT Web behavior

ChatGPT Web may naturally surface native Library results first. That is acceptable for immediate access.

Ownership still follows these rules:

1. A current-turn upload is the user's newest supplied source and may be used immediately.
2. If the same logical item exists in canonical Drive, Drive owns durable state.
3. When freshness or conflict matters, read the canonical Drive item.
4. If the user asks to persist a current upload or generated artifact, write/adopt it into Drive now.
5. Native Library auto-retention does not create a second source of truth.

For durable-library questions, prefer Drive whenever practical. Native Library may supplement discovery but must not silently override a canonical Drive item.

## Direct persistence works without scheduling

A scheduled reconciliation job is optional.

If the current authorized task creates or changes durable general knowledge, persist it directly to Drive whenever possible.

Examples:

- `save this to my Library`;
- `add this to Medical records`;
- `keep this in Cynapsa`;
- update a canonical project/reference document;
- save a durable generated report meant to be available across agents.

Do not defer a save by assuming a future sync job exists.

Installing the skill does not authorize bulk migration of an existing native ChatGPT Library.

## Meaning of “save to my Library”

When this skill applies, `save this to my Library` means save the durable item under canonical Google Drive `ChatGPT Library`, unless the user explicitly asks for native/built-in ChatGPT Library.

ChatGPT may also retain an automatic native Library copy. That copy is non-authoritative.

## Read behavior

When a request may depend on SharedKnowledgeLibrary:

1. Identify the likely canonical Drive subtree.
2. Search the smallest relevant area of the canonical Drive root.
3. Read the actual source file needed for the answer.
4. Use native Library only when it materially helps, such as a current-turn upload or a file that has not yet been ingested.
5. Do not load the entire library when targeted retrieval is sufficient.

## Write behavior

For durable general knowledge:

1. Determine the correct canonical Drive subtree.
2. Search for an existing logical owner.
3. Update the existing canonical item when appropriate rather than creating a duplicate.
4. Preserve Drive IDs when moving or updating existing items.
5. Avoid `new`, `v2`, `updated`, or dated parallel copies unless they are genuinely separate artifacts.
6. Re-read or inspect metadata after the mutation and verify success.

Do not automatically store every answer, temporary artifact, or incidental upload.

## Native Library ingress

An optional reconciliation job may catch native-Library-only files that were created outside a task that directly persisted them.

For a new untracked native Library item:

1. Exclude `/Google Drive/**` and other connector-backed/protected surfaces.
2. Determine whether it is durable general knowledge.
3. Determine whether it belongs in SharedKnowledgeLibrary or the separate Codex operational domain.
4. Search canonical Drive for an existing logical equivalent.
5. If an equivalent exists, adopt/map it and do not upload a duplicate.
6. Otherwise upload it into the correct canonical Drive path.
7. Verify the Drive result.
8. Record an ingress mapping so the same native item is not uploaded again.

After ingress, Drive is canonical. The native copy may remain, but no reverse synchronization is required.

## Legacy Medical Records and Cynapsa Library copies

Existing native Library `/Medical records` and `/Cynapsa` trees were created by older Drive-to-Library jobs.

They are legacy convenience copies, not canonical storage.

During cutover, adopt their legacy manifest mappings into the ingress manifest solely to prevent those existing Library copies from being mistaken for new uploads and re-ingested into Drive.

Do not recreate missing Drive files from legacy Library mirrors merely because the mirror exists. Drive owns those trees.

Once the ingress manifest safely recognizes those legacy mirrors, the old per-folder Drive-to-Library jobs are unnecessary and should remain disabled.

On a fresh ChatGPT installation, do not create those legacy jobs.

## Medical records

`ChatGPT Library/Medical records` in Drive is authoritative for medical-document storage.

When the user asks to save or update medical records, write directly there.

A legacy/native Library copy may be used for immediate retrieval, but freshness-sensitive answers should verify against Drive.

## Cynapsa

`ChatGPT Library/Cynapsa` in Drive is authoritative for Cynapsa general business, investor, product, market, and project knowledge.

Operational credentials and infrastructure runbooks still belong in `Codex` when their primary purpose is operating systems.

## Codex classification boundary

Strong Codex-owned examples include:

- live passwords, tokens, API keys, private keys, secret-bearing URLs;
- SSH and production connection procedures;
- private infrastructure host details;
- deployment/rollback/recovery runbooks;
- MCP connection credentials;
- production configuration ownership;
- durable instructions whose purpose is allowing agents to operate a system.

If a native Library file strongly appears operational or credential-bearing, do not ingest it into SharedKnowledgeLibrary and do not silently copy it to Codex. Mark/report it for classification unless the current user request independently authorizes the Codex write.

## Ingress manifest

If catch-up reconciliation is deployed, keep control data under:

`ChatGPT Library/_sync/`

Recommended manifest:

`_sync/_shared_library_ingress_manifest.json`

Track enough information to prevent repeated ingress:

- native Library file ID and path;
- native Library version when available;
- canonical Drive file ID and relative path;
- origin such as upload/generated/legacy-mirror-adopted;
- last verified state;
- status such as managed, pending-classification, conflict, or skipped.

The manifest is control metadata, not documentary evidence.

## Deletion semantics

Native Library deletion, move, rename, or content drift never deletes, moves, renames, or overwrites canonical Drive.

The ingress job must never delete canonical Drive content.

Canonical Drive deletion does not need to propagate to native Library because native Library is not maintained as an authoritative mirror.

Ordinary ingress should not permanently delete anything from either surface.

## Duplicate and conflict prevention

Never use newest timestamp as a general conflict-resolution rule.

Before creating a Drive item from native Library:

1. check the manifest by native Library ID;
2. search the canonical destination;
3. compare filename, path, size, MIME/type, and available content/hash/revision evidence;
4. adopt an equivalent instead of creating a duplicate;
5. if equivalence is ambiguous, mark a conflict rather than guessing.

A changed native copy of an already-mapped item does not automatically overwrite Drive.

## Privacy and secrets

Treat library content as private unless explicitly designated otherwise.

Use only information needed for the current task. Do not expose medical, financial, personal, company, credential, or operational secrets unnecessarily.

Do not copy operational secrets into SharedKnowledgeLibrary when they belong in Codex.

## No automatic installation, migration, or scheduling

The existence of this source does not authorize installation, bulk migration, task creation, or task disablement. Those are separately authorized actions.

## Final verification

Before completing a task that uses this skill, verify as applicable:

1. Canonical facts came from the correct Drive root.
2. Codex-owned operational information was not duplicated into SharedKnowledgeLibrary.
3. Existing canonical Drive items were updated instead of duplicated.
4. Native Library did not silently outrank canonical Drive.
5. Authorized durable content was written directly to Drive when possible.
6. New native ingress was verified before being marked managed.
7. No native Library mutation propagated destructively to Drive.
8. Medical records and Cynapsa remained under the canonical Drive root with their stable IDs.
9. Any Drive write was re-read or metadata-verified.

**Governing principle: one canonical general library in Google Drive, one separate operational library in Codex, and native ChatGPT Library only as immediate access and optional ingress.**