---
name: shared-knowledge-library
description: 'Use and maintain the user shared durable knowledge library across ChatGPT, Codex, Codex CLI, and other authorized agents. The canonical general-purpose library is the Google Drive folder "ChatGPT Library" with folder ID 1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb. Treat ChatGPT native Library as an ingress, convenience, and discovery surface rather than a competing source of truth. Preserve separate canonical domains for Cynapsa, Medical records, and Codex operational knowledge. Use proactively when the user asks to find, save, update, organize, or reuse durable personal, business, project, research, writing, reference, or generated-file knowledge that should be shared across agents. Do not duplicate externally owned or operational knowledge into this library.'
---

# SharedKnowledgeLibrary

Use the user's Google Drive `ChatGPT Library` folder as the canonical general-purpose shared knowledge library for ChatGPT, Codex, Codex CLI, and other authorized agents.

This skill defines storage and ownership semantics. It does not require or prescribe MCP.

Use whatever authorized Google Drive capability is available in the current environment. ChatGPT may use its connected Google Drive app. Codex may use its connected Drive capability. Another agent is responsible for having its own authorized Drive access.

## Canonical root

- Name: `ChatGPT Library`
- Folder ID: `1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`
- URL: `https://drive.google.com/drive/folders/1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Treat the folder ID as the stable identifier.

The canonical Drive root is the source of truth for general SharedKnowledgeLibrary content after an item has been ingested or intentionally written there.

## Governing files

At the canonical Drive root, prefer these governance files:

- `_LIBRARY_POLICY.md`
- `_EXTERNAL_SOURCES.md`
- `_shared_knowledge_library_manifest.json`

When `_LIBRARY_POLICY.md` and `_EXTERNAL_SOURCES.md` exist in Drive, read them before a material write or ownership decision. Their Drive copies are authoritative governance for the live library.

The copies bundled beside this skill are bootstrap templates only. Do not silently overwrite the live Drive policies from the bundled copies.

## The four knowledge domains

Do not treat every file visible to ChatGPT as belonging to the same storage domain.

### 1. SharedKnowledgeLibrary, canonical Google Drive

Use `Google Drive / ChatGPT Library` for durable general knowledge such as:

- Personal reference material.
- Business and project documents that do not have another canonical owner.
- Research.
- Writing and manuscripts.
- Generated reports and artifacts worth retaining.
- User uploads intended for durable reuse.
- General technical reference that is not environment-specific operational memory.
- Documents ChatGPT or another agent creates and the user wants available across agents.

Once an item is present here, this Drive copy is canonical.

### 2. Medical records, external canonical source

The Google Drive `Medical records` folder remains its own canonical source.

- Source folder ID: `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- ChatGPT native Library mirror: `/Medical records`
- Existing task: `Medical Records Sync`
- Direction: Google Drive -> ChatGPT native Library only.

Do not copy this subtree into `Google Drive / ChatGPT Library`.

Do not sync changes from native Library `/Medical records` back to Google Drive.

When reading in ChatGPT, the native Library mirror may be used for efficient retrieval when it is current, but its source Drive folder remains authoritative.

### 3. Cynapsa, external canonical source

The Google Drive `Cynapsa` folder remains its own canonical source.

- Source folder ID: `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`
- ChatGPT native Library mirror: `/Cynapsa`
- Existing task: `Sync Cynapsa Drive`
- Direction: Google Drive -> ChatGPT native Library only.

Do not copy this subtree into `Google Drive / ChatGPT Library`.

Do not sync changes from native Library `/Cynapsa` back to Google Drive.

When reading in ChatGPT, the native Library mirror may be used for efficient retrieval when it is current, but the source Drive folder remains authoritative.

### 4. Codex operational knowledge, separate canonical source

The Google Drive `Codex` folder is a separate operational memory domain.

- Folder ID: `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`
- Governing skill: `CodexAsKnowledgeReadWrite`

It owns environment-specific operational knowledge such as:

- Credentials and API keys.
- Private service endpoints.
- SSH and connection instructions.
- Deployment runbooks.
- Container and infrastructure topology.
- Runtime paths.
- Production configuration ownership.
- Database credentials and operational procedures.
- MCP connection information.
- Recovery and incident procedures for the user's systems.

Do not mirror `Codex` into SharedKnowledgeLibrary.

Do not copy operational facts into SharedKnowledgeLibrary merely because ChatGPT or another agent also needs to read them. Consumers do not determine ownership.

If a task needs both general library knowledge and operational knowledge, retrieve each fact from its canonical domain.

## Source-of-truth precedence

Use this precedence for durable knowledge.

### Current-turn explicit user input

The user's current explicit instructions and a file explicitly uploaded or generated in the current task may be newer than stored knowledge and may be used immediately for the current task.

A current-turn file is not automatically the durable canonical version until it is written or ingested into the correct canonical Drive domain.

### General durable knowledge

For general SharedKnowledgeLibrary content:

1. Current explicit user instruction for the current task.
2. Canonical `Google Drive / ChatGPT Library` file.
3. A current ChatGPT native Library item that has not yet been ingested, treated as pending ingress.
4. Older cached or duplicate representations only as supporting evidence, never as a competing source of truth.

### Medical records

1. Current explicit user update where appropriate.
2. Canonical Google Drive `Medical records` source.
3. Synchronized native Library `/Medical records` mirror when current.

### Cynapsa

1. Current explicit user instruction.
2. Canonical Google Drive `Cynapsa` source.
3. Synchronized native Library `/Cynapsa` mirror when current.

### Operational knowledge

1. Current explicit user instruction.
2. Canonical Google Drive `Codex` knowledge under the rules of `CodexAsKnowledgeReadWrite`.

Never resolve a conflict merely by choosing whichever retrieval result appeared first.

## ChatGPT native Library role

ChatGPT native Library is useful but is not the canonical general shared store.

Treat it as:

- Automatic ingress for files uploaded to ChatGPT.
- Automatic ingress for files created by ChatGPT.
- A convenient retrieval surface on ChatGPT Web.
- A read mirror for the existing `/Medical records` and `/Cynapsa` one-way synchronization jobs.
- A cache or convenience copy when the same general artifact is already canonical in Drive.

Do not treat it as a peer database that must be kept bidirectionally identical with Google Drive.

## ChatGPT Web behavior

ChatGPT Web may naturally surface native Library results before a Drive result. Retrieval order does not change ownership.

When using this skill on ChatGPT Web:

1. If the user is referring to a file in the current conversation, use that exact current file for the task.
2. If the request concerns older general shared knowledge, resolve the canonical version in `Google Drive / ChatGPT Library` when correctness, freshness, or modification matters.
3. If ChatGPT native Library returns a matching general file first, do not automatically assume it is canonical. Check whether the canonical Drive file exists when the distinction can affect the answer or a write.
4. If the relevant general file exists only in native Library, treat it as `pending ingress`. It may be used for the current task, but durable updates should ultimately land in the canonical Drive library.
5. For `/Medical records` and `/Cynapsa`, native Library is an intentional read mirror. Use it for efficient reading when appropriate, but never write its changes back through this skill.
6. Never export the mounted `/Google Drive` Library surface back into Google Drive.

The goal is not to prevent ChatGPT Web from using Library. The goal is to prevent convenient retrieval from silently changing source-of-truth semantics.

## Meaning of "Library"

When this skill is active and the user says phrases such as:

- "save this to my Library"
- "put this in the shared library"
- "remember this in the library"
- "make this available to all agents"

interpret `Library` as the canonical `SharedKnowledgeLibrary` in Google Drive unless the user explicitly says `ChatGPT native Library`, `built-in Library`, or otherwise clearly asks for the product-local Library only.

Do not ask a clarification question merely because ChatGPT also has a native Library if the user's intent is durable cross-agent access.

A file ChatGPT creates may still be automatically retained by the product in native Library. That automatic retention does not change the canonical destination requested by this skill.

## Reading workflow

### 1. Classify the knowledge domain

Before searching broadly, determine whether the request belongs to:

- SharedKnowledgeLibrary.
- Medical records.
- Cynapsa.
- Codex operational knowledge.
- Current conversation only.

Use the content and intended purpose, not the name of the agent performing the task.

For example, a Codex agent editing an investor brief still uses SharedKnowledgeLibrary if the brief is general business knowledge. A ChatGPT Web task deploying a service still uses Codex operational knowledge for the deployment facts.

### 2. Use the narrowest canonical source

Search the relevant canonical source first when practical.

Do not search or load credentials, health records, or unrelated private material merely because it is accessible.

### 3. Use native Library deliberately

Native Library can be used when:

- The file is current-turn input.
- The item is newly uploaded or generated and has not yet been ingested.
- The item belongs to an intentional read mirror such as `/Medical records` or `/Cynapsa`.
- The task is discovery and the canonical location is not yet known.

If a durable write follows, resolve canonical ownership before writing.

## Writing workflow

### 1. Classify before writing

Determine which canonical domain owns the item.

Do not use SharedKnowledgeLibrary as a dumping ground for everything an agent creates.

### 2. Search for an existing canonical artifact

Before creating a new Drive file, look for an existing file with the same purpose, path, stable identity, or content.

Prefer updating the existing canonical file over creating:

- `foo-new`
- `foo-v2`
- `foo-final-final`
- date-stamped duplicates

unless the user actually requested a new versioned artifact.

### 3. Preserve one canonical artifact

For general knowledge, one logical artifact should have one canonical Drive file.

A native Library copy may continue to exist because ChatGPT created or retained it. Treat that as an ingress/cache copy, not a second canonical owner.

### 4. Preserve Drive identity on updates

When updating an existing stored file, prefer updating it in place and preserving the Drive file ID.

For Google-native documents, use appropriate document actions and concurrency controls when available.

For raw files, re-read current metadata/content before replacing bytes when concurrent edits are possible.

### 5. Verify writes

After creating or updating a canonical Drive file:

- Re-read or re-list it.
- Verify filename, parent, size or content where applicable.
- Confirm no duplicate file was accidentally created.
- Confirm the write did not land in an external canonical source unless that was explicitly intended.

## Newly uploaded or ChatGPT-created files

Files uploaded to or generated in ChatGPT may automatically appear in native Library before they exist in Google Drive.

For a new native Library item that should be durable general knowledge:

1. Treat the native Library object as the ingress source.
2. Export/copy its original bytes or best supported representation to `Google Drive / ChatGPT Library`.
3. Preserve the relative folder path when meaningful.
4. Record the Library-to-Drive identity mapping in `_shared_knowledge_library_manifest.json` when the synchronization workflow is active.
5. After successful ingestion, treat the Drive file as canonical.
6. Do not delete the native Library object merely because ingestion succeeded.

If a ChatGPT-created artifact was also written directly to Drive during the same task, the later synchronization workflow must adopt that existing identical Drive file instead of creating a duplicate.

## Drive changes do not sync back to native Library

Do not maintain a general Drive -> native Library mirror for SharedKnowledgeLibrary.

ChatGPT can use its Google Drive connection for canonical Drive content.

If a canonical Drive file changes after ingestion:

- Drive remains authoritative.
- Do not overwrite it from an older native Library copy.
- Do not create a second native Library copy merely to mirror the Drive change.

This rule is different from the dedicated Medical Records and Cynapsa jobs, whose intentional direction is Drive -> native Library.

## Deletion semantics

The native Library is not authoritative for deletion of canonical general knowledge.

If a source native Library item disappears after it has been ingested:

- Do not delete the canonical Drive file.
- Mark the source mapping as missing or detached if maintaining a manifest.

If a canonical Drive item is deleted intentionally, do not recreate it from an old native Library copy unless the user explicitly restores it or there is clear evidence that the deletion was accidental and restoration is authorized.

Do not automatically delete files from Medical records, Cynapsa, Codex, native Library, or SharedKnowledgeLibrary as a cleanup side effect.

## Conflict handling

For a Library-originated general artifact tracked in the manifest:

### Source changed, Drive unchanged since last sync

Update the same canonical Drive file in place and advance the manifest.

### Source unchanged, Drive changed since last sync

Drive wins. Do not sync Drive back to native Library. Update observed destination metadata in the manifest if useful.

### Both source and Drive changed since last sync

Do not overwrite either side automatically.

Report a conflict with the filenames/paths and enough non-sensitive metadata to resolve it. Treat Drive as canonical until the user or a task-specific merge explicitly resolves the content.

### New native Library item collides with an existing Drive path

- If content is identical, adopt the existing Drive file and record the mapping.
- If content differs and there is no proven identity relationship, do not overwrite the canonical Drive file. Report the collision.

## Routing operational-looking Library content

Native ChatGPT Library may contain older files whose content looks operational, for example credentials, MCP endpoints, infrastructure runbooks, deployment notes, or service configuration.

Do not automatically copy such material into SharedKnowledgeLibrary.

Do not automatically move it into Codex either.

Instead:

1. Determine whether an existing canonical Codex owner already contains the same knowledge.
2. If clearly redundant, skip SharedKnowledgeLibrary ingestion.
3. If it appears to contain unique operational knowledge, report it as a Codex-routing candidate unless the current user request authorizes reconciling it into Codex.
4. Never duplicate secret-bearing operational material in both domains.

When uncertain, skip the automatic migration and report the item for review rather than creating two sources of truth.

## Hard native-Library exclusions for general ingestion

Never ingest these native Library trees into `Google Drive / ChatGPT Library`:

- `/Medical records/**`
- `/Cynapsa/**`
- `/Google Drive/**`

Also ignore synchronization manifests inside excluded trees as content.

These exclusions apply recursively.

Additional exclusions may be defined in the authoritative Drive `_EXTERNAL_SOURCES.md`.

## Manifest semantics

When the Library-to-Drive ingestion workflow is in use, maintain:

`_shared_knowledge_library_manifest.json`

in the canonical Drive root.

The manifest is synchronization metadata, not knowledge evidence.

For each tracked Library-originated artifact, record when available:

- Native Library stable file ID.
- Native Library path.
- Native Library version ID.
- Native Library created and modified timestamps.
- Whether it was user-uploaded or model-generated when known.
- MIME type and byte size.
- Content hash or fingerprint when available.
- Canonical Drive file ID.
- Canonical Drive path.
- Drive MIME type.
- Drive modified time or revision observed at last successful synchronization.
- Last successfully synchronized source version/fingerprint.
- Last successfully synchronized destination fingerprint/revision.
- State such as `synced`, `source_missing`, `conflict`, `excluded`, or `skipped_operational_candidate`.
- Last synchronization timestamp.

Never use the manifest as a source for the substantive contents of a document.

## External-source protection

Do not let the SharedKnowledgeLibrary synchronization workflow mutate:

- Google Drive `Medical records`.
- Google Drive `Cynapsa`.
- Google Drive `Codex`.

The existing Medical Records and Cynapsa scheduled tasks remain independently responsible for their one-way Drive -> native Library mirrors.

SharedKnowledgeLibrary must not modify those tasks or reverse their direction.

## Sensitive information

SharedKnowledgeLibrary can contain private user information, but do not intentionally use it as a duplicate secret store for operational credentials owned by Codex.

For sensitive general documents:

- Retrieve only what the task needs.
- Avoid unnecessary reproduction in responses.
- Do not expose internal file IDs or synchronization metadata unless needed for troubleshooting.
- Do not send private data to web search or unrelated external services.

For medical content, use the Medical records domain and its dedicated handling rules rather than duplicating it here.

## Failure handling

If canonical Drive access is unavailable:

- Current-turn or native Library content may still be used for the immediate task when appropriate.
- Do not claim a durable SharedKnowledgeLibrary write succeeded.
- Do not invent Drive state.
- State that canonical persistence or verification could not be completed.

If native Library access is unavailable:

- Continue using canonical Drive for general shared knowledge.
- Do not claim newly uploaded/generated native Library items were ingested.

If an external source or its mirror is unavailable, report that domain-specific limitation without changing another domain to compensate.

## No transport assumption

Do not require MCP for this architecture.

The current agent may use any authorized Drive integration available in its environment.

Do not tell the user to create a new MCP or OAuth integration if the current environment already has sufficient Drive access.

## No automatic installation or publication

This skill does not authorize installing itself or another skill.

Do not install, enable globally, or deploy this skill unless the user explicitly requests installation.

Do not modify the skills Git repository unless the user explicitly requests that repository operation.

## Final verification

Before completing a task that used SharedKnowledgeLibrary, verify as applicable:

1. The correct knowledge domain was selected.
2. General durable knowledge was read from or written to the canonical Drive library when appropriate.
3. Native ChatGPT Library was treated as ingress/cache/read mirror, not a competing general source of truth.
4. Medical Records and Cynapsa one-way sync boundaries were preserved.
5. Codex operational knowledge was not duplicated into the general library.
6. A write preserved or established one canonical artifact.
7. A newly ingested file was verified in Drive.
8. Existing Drive content was not overwritten from a stale Library copy.
9. Native Library deletion was not propagated to canonical Drive.
10. The `/Google Drive` mounted Library surface was never exported back into Drive.
11. Conflicts and skipped operational candidates were reported instead of guessed through.
12. No installation occurred unless explicitly authorized.

The governing principle is:

**One logical knowledge item, one canonical owner, many authorized consumers.**
