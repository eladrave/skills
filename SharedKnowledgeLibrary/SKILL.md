---
name: shared-knowledge-library
description: 'Use the Google Drive folder "ChatGPT Library" as the single canonical shared general-knowledge library for ChatGPT, Codex, Codex CLI, and other authorized agents. Read and write durable general knowledge directly in Drive. When an authorized foreground task needs durable persistence but the final canonical destination or classification is not yet known, stage the original file in the private Google Drive "ChatGPT Ingress Queue" and record queue metadata for later Drive-only reconciliation. Native ChatGPT Library is immediate-access storage only and must never be a scheduled dependency. Keep the separate Google Drive "Codex" folder outside this library for credentials, infrastructure, deployment runbooks, private connection details, and other operational agent memory. Use one durable item, one canonical owner, and never create competing copies across SharedKnowledgeLibrary and Codex.'
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

## Neutral Drive ingress queue

A private Google Drive staging folder exists for authorized durable files whose final canonical destination or classification is not yet known at foreground execution time.

- Name: `ChatGPT Ingress Queue`
- Folder ID: `1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`
- URL: `https://drive.google.com/drive/folders/1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`

The queue is **not canonical general knowledge** and is **not Codex**. It is temporary Drive staging so foreground tasks can persist original bytes while they still have reliable access to the file.

Do not use the queue as a dumping ground. Use it only when the current task is already authorized to durably persist the item, but the canonical destination or ownership classification cannot yet be safely determined.

## Transport independence

This skill defines storage and ownership semantics, not a specific connector implementation.

Use whatever authorized Google Drive capability exists in the current environment. Do not require a custom MCP server.

If Drive access is unavailable, state that limitation and do not invent private library content or claim persistence.

## Live policy

Before a non-trivial write, migration, queue reconciliation, or ownership decision, read `_LIBRARY_POLICY.md` from the canonical Drive root when available.

The Drive copy is the live shared policy. The GitHub copy is version-controlled source.

Current explicit user instructions override older policy text.

## Core source-of-truth rule

Google Drive is canonical.

Native ChatGPT Library is **not** a mirror and is **not** part of the scheduled reconciliation path.

It may contain:

1. current uploads;
2. ChatGPT-generated files;
3. legacy convenience copies from older sync jobs;
4. files automatically retained by ChatGPT.

Use native Library for immediate foreground access when useful. Once a logical item exists in canonical Drive, Drive owns durable state.

There is intentionally no requirement to copy canonical Drive changes back into native ChatGPT Library.

## Reliability model

The correctness path is foreground write-through to Google Drive.

Use this order:

1. If the canonical destination is known, persist directly to that canonical Drive location now.
2. If durable persistence is authorized but the canonical destination or classification is genuinely uncertain, stage the original file in `ChatGPT Ingress Queue` and record queue metadata in the ingress manifest.
3. A recurring queue processor may later reconcile staged Drive files into canonical Drive using Google Drive only.
4. Native ChatGPT Library is never required for scheduled correctness.

Do not defer an authorized durable save because a future scheduled task might exist.

## ChatGPT Web behavior

ChatGPT Web may naturally surface native Library results first. That is acceptable for immediate access.

Ownership still follows these rules:

1. A current-turn upload is the user's newest supplied source and may be used immediately.
2. If the same logical item exists in canonical Drive, Drive owns durable state.
3. When freshness or conflict matters, read the canonical Drive item.
4. If the user asks to persist a current upload or generated artifact and the destination is known, write or adopt it into Drive immediately.
5. If durable persistence is authorized but destination or ownership is uncertain, stage it in the Drive ingress queue rather than relying on native Library retention.
6. Native Library auto-retention does not create a second source of truth.

For durable-library questions, prefer Drive whenever practical. Native Library may supplement foreground discovery but must not silently override a canonical Drive item.

## Meaning of “save to my Library”

When this skill applies, `save this to my Library` means save the durable item under canonical Google Drive `ChatGPT Library`, unless the user explicitly asks for native or built-in ChatGPT Library.

ChatGPT may also retain an automatic native Library copy. That copy is non-authoritative.

## Read behavior

When a request may depend on SharedKnowledgeLibrary:

1. Identify the likely canonical Drive subtree.
2. Search the smallest relevant area of the canonical Drive root.
3. Read the actual source file needed for the answer.
4. Use current-turn uploads immediately when they are the newest supplied source.
5. Use native Library only when it materially helps foreground discovery or the user explicitly asks for it.
6. Do not load the entire library when targeted retrieval is sufficient.

## Direct write behavior

For authorized durable general knowledge when the destination is known:

1. Determine the correct canonical Drive subtree.
2. Search for an existing logical owner before creating anything.
3. Update or adopt the existing canonical item when appropriate instead of creating a duplicate.
4. Preserve Drive IDs when moving or updating existing items.
5. Avoid `new`, `v2`, `updated`, or dated parallel copies unless they are genuinely separate artifacts.
6. Preserve filename and MIME type when practical for stored files.
7. Re-read or inspect Drive metadata after the mutation and verify success.

Do not automatically store every answer, temporary artifact, incidental upload, screenshot, or generated preview.

Installing this skill does not authorize bulk migration of a pre-existing native ChatGPT Library.

## Foreground staging behavior

Use `ChatGPT Ingress Queue` only when all of these are true:

1. the current user request or authorized workflow calls for durable persistence;
2. the original file bytes are available in the current foreground runtime;
3. the final canonical destination or SharedKnowledgeLibrary-versus-Codex ownership cannot yet be determined safely.

When staging:

1. Search the queue for an existing equivalent first when practical.
2. Upload the original file into `ChatGPT Ingress Queue`, preserving filename and MIME type when practical.
3. Verify the staged Drive file ID, title, MIME type, and queue parent.
4. Update `_sync/_shared_library_ingress_manifest.json` only after verification.
5. Record a `drive_ingress_queue.items` entry containing at least:
   - queued Drive file ID;
   - original filename;
   - source, such as current upload or generated artifact;
   - requested domain/path when known;
   - classification when known;
   - staged time;
   - status.
6. Do not mark the item canonical merely because it is in the queue.

Recommended queue statuses include:

- `queued`;
- `managed`;
- `adopted`;
- `pending-operational`;
- `pending-ambiguous`;
- `orphan-pending`;
- `conflict`;
- `failure`.

## Scheduled reconciliation

Scheduled reconciliation must be **Google Drive only**.

The recurring job may read:

- canonical Drive `ChatGPT Library`;
- `_LIBRARY_POLICY.md`;
- `_sync/_shared_library_ingress_manifest.json`;
- Google Drive `ChatGPT Ingress Queue`.

It must **not** depend on native ChatGPT Library, `files.list`, `files.search`, or `files.materialize`.

For each staged queue item:

1. Read its queue metadata from the manifest.
2. If metadata is missing, mark it `orphan-pending` and do not guess its destination.
3. If it is durable general knowledge with a verified canonical destination, search the destination for an existing logical equivalent.
4. If an equivalent exists, record `adopted` with the canonical Drive file ID and do not create a duplicate.
5. If no equivalent exists, move the queued Drive file into the canonical destination using Drive parent metadata so the same Drive file ID is preserved when possible.
6. Verify file ID, title, MIME type, and destination parent before recording `managed`.
7. If it is operational or credential-bearing, leave it in the neutral queue as `pending-operational`. Do not move it into SharedKnowledgeLibrary.
8. Do not move operational content into Codex unless the current user request or an applicable operational workflow explicitly authorizes that write.
9. If classification or destination remains uncertain, leave it in the queue as `pending-ambiguous` rather than guessing.
10. Never delete queued or canonical Drive files as part of ordinary reconciliation.

The scheduled queue processor is a cleanup and classification path, not the primary persistence path.

## Native ChatGPT Library audits

Native ChatGPT Library may be audited interactively in a foreground conversation when explicitly useful, for example to find a suspected stranded file.

Such an audit is maintenance, not the scheduled architecture.

For a native Library file found during an authorized interactive audit:

1. Determine whether durable persistence is actually authorized or required.
2. Classify SharedKnowledgeLibrary versus Codex versus temporary/ambiguous.
3. Search canonical Drive for an existing logical equivalent.
4. If an equivalent exists, adopt the Drive item and do not duplicate it.
5. If eligible durable general knowledge must be persisted and the destination is known, materialize the native file and write it directly to canonical Drive.
6. If persistence is authorized but the destination remains uncertain, materialize and stage it in the Drive ingress queue.
7. Verify the Drive result before updating control state.
8. Never let native Library drift overwrite canonical Drive.

Do not schedule native Library audits and do not bulk-migrate native Library without explicit authorization.

## Legacy Medical Records and Cynapsa Library copies

Existing native Library `/Medical records` and `/Cynapsa` trees were created by older Drive-to-Library jobs.

They are legacy convenience copies, not canonical storage.

Do not recreate missing Drive files from legacy native mirrors merely because the mirror exists. Drive owns those trees.

The old per-folder Drive-to-Library jobs are unnecessary and should remain disabled.

On a fresh ChatGPT installation, do not create those legacy jobs.

## Medical records

`ChatGPT Library/Medical records` in Drive is the canonical documentary source for the user's medical records.

Use it for requests involving medical history, surgeries, diagnoses, treatments, medications, examinations, hospitalizations, rehabilitation, test results, insurance records, disability documentation, or source-grounded medical summaries and letters.

### Medical retrieval rules

1. Search or traverse only the relevant portion of the canonical `Medical records` subtree unless the user asks for additional sources.
2. Read the actual contents of every document used to support the answer. Do not treat filenames or search snippets as sufficient evidence.
3. For a comprehensive timeline or history, inventory the relevant subtree recursively and review every potentially relevant file.
4. Use exact-term searches when locating a named diagnosis, anatomical level, medication, provider, procedure, or date.
5. Inspect relevant PDF pages or embedded images visually when layout, scans, handwriting, tables, diagrams, signatures, or extraction quality may affect interpretation.
6. Mark unreadable or ambiguous content rather than guessing.
7. Treat each record as evidence of what was documented at that time, not automatically as the user's current condition.
8. Treat a newer explicit user statement as current context when it clearly updates an older record, while keeping record-derived facts distinct from user-provided updates.
9. Identify conflicting dates, diagnoses, medication lists, anatomical descriptions, or treatment plans rather than silently choosing one version.
10. If the records do not establish a requested fact, say so explicitly.

### Medical evidence and citations

- Cite material record-derived claims using the source filename and precise page, section, date, or heading when available.
- Never invent page numbers, dates, providers, diagnoses, procedures, or quotations.
- Use short quotations only when exact wording materially matters.
- Label inferences clearly and explain the supporting record evidence.
- For generated medical summaries, letters, timelines, or forms, validate the finished content against the underlying records before presenting it.

### Medical privacy

- Retrieve and disclose only what the current task requires.
- Do not unnecessarily repeat insurance identifiers, account numbers, addresses, phone numbers, dates of birth, or unrelated diagnoses.
- Do not expose Drive IDs, synchronization metadata, connector internals, or control manifests as medical evidence.
- Treat all medical outputs as private.

### Medical writes

When the user asks to save or update medical records, write directly to the canonical Drive `Medical records` subtree, preserve a single canonical owner, and verify the write.

A current-turn medical upload may be used immediately as the user's newest supplied source. Persist it into Drive only when the user or an authorized workflow calls for durable storage.

If canonical Drive access is unavailable, state that limitation rather than presenting a legacy native Library copy as current authoritative evidence.

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

If an item strongly appears operational or credential-bearing, do not ingest it into SharedKnowledgeLibrary and do not silently copy it to Codex. Leave it in the neutral queue as `pending-operational` when it was already staged, or report it for classification unless the current user request independently authorizes the Codex write.

Never expose secret values in queue reports or classification notifications.

## Ingress manifest

Keep queue and reconciliation control data under:

`ChatGPT Library/_sync/`

Recommended manifest:

`_sync/_shared_library_ingress_manifest.json`

The manifest should track:

- canonical root metadata;
- historical native-Library migration/adoption mappings when needed for legacy protection;
- `drive_ingress_queue.folder_id`;
- `drive_ingress_queue.items` with queued Drive identity, source, requested destination, classification, status, and canonical mapping when resolved;
- conflicts and failures;
- last verified run state.

The manifest is control metadata, not documentary evidence.

## Deletion semantics

Native Library deletion, move, rename, or content drift never deletes, moves, renames, or overwrites canonical Drive.

Queue reconciliation must never delete canonical Drive content.

Ordinary queue processing must not permanently delete queue items either. A managed queue item should normally be moved into canonical Drive while preserving its Drive identity.

Canonical Drive deletion does not need to propagate to native Library because native Library is not maintained as an authoritative mirror.

## Duplicate and conflict prevention

Never use newest timestamp as a general conflict-resolution rule.

Before moving or adopting a queued item:

1. check the manifest by queued Drive file ID;
2. search the canonical destination;
3. compare filename, path, size, MIME/type, and available content/hash/revision evidence;
4. adopt an equivalent instead of creating or moving a competing copy;
5. if equivalence is ambiguous, mark a conflict rather than guessing.

A native Library copy or queue item does not automatically overwrite Drive.

## Privacy and secrets

Treat library and queue content as private unless explicitly designated otherwise.

Use only information needed for the current task. Do not expose medical, financial, personal, company, credential, or operational secrets unnecessarily.

Do not copy operational secrets into SharedKnowledgeLibrary when they belong in Codex.

## No automatic installation, migration, or scheduling

The existence of this source does not authorize installation, bulk migration, task creation, queue creation, or task enablement/disablement. Those are separately authorized actions.

## Final verification

Before completing a task that uses this skill, verify as applicable:

1. Canonical facts came from the correct Drive root.
2. Codex-owned operational information was not duplicated into SharedKnowledgeLibrary.
3. Existing canonical Drive items were updated or adopted instead of duplicated.
4. Native Library did not silently outrank canonical Drive.
5. Authorized durable content was written directly to canonical Drive when the destination was known.
6. Authorized uncertain durable content was staged in the Drive ingress queue only when necessary and only after verifying the staged Drive file.
7. Queue reconciliation used Google Drive only and verified each move/adoption before updating the manifest.
8. No native Library or queue mutation propagated destructively to canonical Drive.
9. Medical records and Cynapsa remained under the canonical Drive root with their stable IDs.
10. Any Drive write or move was re-read or metadata-verified.

**Governing principle: one canonical general library in Google Drive, one separate operational library in Codex, foreground write-through to Drive as the correctness path, a Drive-only ingress queue for uncertain durable items, and native ChatGPT Library only as immediate foreground access or optional interactive maintenance.**