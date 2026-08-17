# SharedKnowledgeLibrary

A single canonical Google Drive tree for durable general knowledge shared across ChatGPT, Codex, Codex CLI, and other authorized agents.

## Canonical storage

Google Drive `ChatGPT Library`

Folder ID:

`1EQyBOpv3j_wNDW4pWtWrBq1_eukGmtRb`

Canonical subtrees include:

- `Medical records` → `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- `Cynapsa` → `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

Both were moved under the canonical root without changing their IDs.

## Separate operational library

Google Drive `Codex`, ID `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`, remains outside this tree.

It owns credentials, infrastructure, deployment and recovery runbooks, connection details, and other operational agent memory.

## Neutral Drive staging queue

Google Drive `ChatGPT Ingress Queue`

Folder ID:

`1PwNOvDU-3VQdF6uoRyS8KJS5JAP_j_an`

This folder is private staging only. It is not canonical SharedKnowledgeLibrary content and it is not Codex.

Use it only when an authorized foreground task already needs durable persistence but cannot safely determine the final canonical destination or ownership while it still has access to the original bytes.

## Final architecture

```text
Foreground task
│
├── canonical destination known
│   └── write or adopt directly in Google Drive ChatGPT Library
│
└── durable persistence authorized, destination/classification uncertain
    └── stage original file in Google Drive ChatGPT Ingress Queue

Scheduled reconciliation
└── Google Drive ChatGPT Ingress Queue
    ├── adopt verified canonical equivalent, or
    └── move same Drive file into canonical destination

Google Drive
│
├── ChatGPT Library/                 CANONICAL GENERAL KNOWLEDGE
│   ├── _LIBRARY_POLICY.md
│   ├── _sync/
│   │   └── _shared_library_ingress_manifest.json
│   ├── Medical records/
│   ├── Cynapsa/
│   └── ...
│
├── ChatGPT Ingress Queue/           PRIVATE TEMPORARY STAGING
│
└── Codex/                           CANONICAL OPERATIONAL KNOWLEDGE

Native ChatGPT Library
    = immediate foreground access + optional interactive maintenance
    ≠ canonical authority
    ≠ scheduled dependency
```

## Important reliability simplification

There is no need to mirror canonical Drive back into native ChatGPT Library.

More importantly, the scheduled reconciliation path no longer reads native ChatGPT Library at all.

The previous native-Library ingress design depended on the Files connector being addressable inside scheduled runtimes. That proved unreliable. The replacement design makes the scheduled critical path Google Drive only.

Foreground conversations persist durable items while they still have reliable access to the original upload or generated artifact:

- write directly to canonical Drive when the destination is known;
- otherwise stage the file in `ChatGPT Ingress Queue` with manifest metadata.

The scheduled task then performs only Drive-to-Drive adoption or moves.

## One skill for the whole library

`SharedKnowledgeLibrary/` is one complete Skill package.

`SKILL.md` is the entry point, but it is not the only useful file in this Skill. Keep the supporting files with it when installing, updating, exporting, or moving the Skill to another ChatGPT/Codex installation.

The package includes domain-specific behavior for `Medical records` and covers `Cynapsa` and all future subfolders under the canonical Drive root. Adding another folder under `ChatGPT Library` does not require another skill or another Drive-to-Library sync task.

The old `ChatgptLibrary/MedicalRecords` and `ChatgptLibrary/DriveLibraryMetaSkill` sources are retired by this architecture.

## Package contents and roles

Install or transfer the complete `SharedKnowledgeLibrary/` package with these files together:

- `SKILL.md`: required Skill entry point and normal runtime behavior.
- `_LIBRARY_POLICY.md`: version-controlled policy source and fallback/reference. The live copy in canonical Google Drive remains authoritative during operation.
- `scheduledprompt.md`: authoritative template for creating or updating the optional Drive-only `Library Ingress Queue` scheduled task. It is not automatically executed merely because the Skill is installed.
- `bootstrap_migration.md`: one-time installation/cutover procedure for a new environment or major architecture migration. It is not part of normal per-request execution.
- `manifest.example.json`: schema/example used when initializing or repairing `_sync/_shared_library_ingress_manifest.json`.
- `README.md`: architecture, packaging, installation, update, verification, and deployment documentation.

Do not separate `SKILL.md` from these support files when distributing this Skill. A minimal `SKILL.md`-only copy may still contain the core runtime instructions, but it is an incomplete package and loses the deployment, reconciliation, bootstrap, and manifest resources.

### GitHub is not a runtime dependency

The installed Skill should contain its supporting resources. **Do not expect ChatGPT, Codex, or another agent to automatically fetch sibling files from this GitHub repository merely because `SKILL.md` came from here.**

GitHub `eladrave/skills/SharedKnowledgeLibrary` is the source and update channel for the package. Normal runtime execution should use the files bundled with the installed Skill plus the live Google Drive policy and control state.

If a supporting file is missing from an installed Skill, treat that installation as incomplete. Fetch from GitHub only as an explicit repair/update action when the user requests it and authorized GitHub access is available. Do not make normal Skill operation depend on GitHub being connected or reachable.

## Skill behavior without a scheduled job

`SKILL.md` works independently of automation:

- read canonical knowledge directly from Drive;
- save authorized durable knowledge directly to Drive;
- interpret `save this to my Library` as canonical Drive;
- treat current-turn uploads as immediate sources;
- stage authorized durable files in the Drive queue only when final destination or ownership is uncertain;
- keep `Codex` semantically separate;
- verify every Drive mutation before claiming persistence.

The scheduled job is cleanup and reconciliation, not the correctness path.

## Foreground persistence rules

When a current task is authorized to durably persist a file:

1. Determine whether it belongs in SharedKnowledgeLibrary, Codex, or is still ambiguous.
2. If the canonical SharedKnowledgeLibrary destination is known, search for an existing logical owner and write or adopt directly there.
3. If durable persistence is authorized but destination or ownership is uncertain, upload the original file to `ChatGPT Ingress Queue` while the bytes are available.
4. Verify the staged Drive file.
5. Record queue metadata under `drive_ingress_queue.items` in `_shared_library_ingress_manifest.json`.
6. Do not use native Library retention as a persistence guarantee.

Do not automatically persist every upload, answer, screenshot, or generated preview.

## Optional recurring reconciliation

`scheduledprompt.md` defines a **Drive-only** queue processor.

It:

- reads the live Drive policy and manifest;
- inventories `ChatGPT Ingress Queue`;
- uses manifest queue metadata to determine classification and destination;
- searches canonical Drive for logical equivalents;
- adopts verified equivalents rather than duplicating them;
- otherwise moves the same queued Drive file into the canonical destination, preserving its Drive ID when possible;
- verifies the result before updating the manifest;
- leaves operational items in the neutral queue as `pending-operational`;
- leaves unresolved items as `pending-ambiguous` or `orphan-pending`;
- never overwrites or deletes canonical Drive;
- never calls native ChatGPT Library or Files connector actions.

## Native ChatGPT Library audits

Native ChatGPT Library can still be inspected manually in an interactive foreground conversation when useful, for example to find a suspected stranded historical file.

That is maintenance only.

It is not the scheduled architecture and should not be used as the normal persistence path.

Bulk native-Library migration still requires explicit authorization.

## Legacy jobs

The older `Medical Records Sync` and `Sync Cynapsa Drive` jobs mirrored Drive into native Library. They are disabled and no longer needed because Drive itself is the canonical retrieval surface.

Do not recreate them on a fresh installation.

## Install the skill in ChatGPT

GitHub is the source repository. Updating GitHub does **not** automatically update an already installed Personal Skill in ChatGPT.

OpenAI Skills support instructions plus supporting resources. Install this as the complete `SharedKnowledgeLibrary/` Skill package rather than uploading an isolated `SKILL.md` and discarding the sibling files.

Current ChatGPT navigation is:

`Plugins` → `Skills`

For a new installation:

1. Obtain the complete `SharedKnowledgeLibrary/` package from this repository, preserving the filenames and relative layout.
2. Open ChatGPT.
3. In the sidebar, open `Plugins`.
4. Open the `Skills` tab.
5. Choose `Create`.
6. Choose `Upload from your computer`, or use the Skills editor/skill-creator workflow.
7. Import the complete Skill package so `SKILL.md` and its supporting resources belong to the same Skill.
8. Review the scan result. If ChatGPT marks the upload `Needs Review`, review it before enabling it.
9. Install or save the Skill when prompted.
10. Confirm that `shared-knowledge-library` appears in your installed or created Skills.

If the particular uploader you are using only exposes one-file-at-a-time selection, use the Skills editor or skill-creator workflow to create the Skill from `SKILL.md` and add the remaining package files as supporting resources. Do not intentionally reduce the installed package to `SKILL.md` alone.

Personal Skills are surface-specific in ChatGPT. If you use both ChatGPT desktop and web/mobile and need the skill on both, install it separately on each applicable surface. Do not assume a Personal Skill installation automatically syncs between surfaces.

## Update an already installed skill

An installed Personal Skill does not track GitHub automatically. When any file in `SharedKnowledgeLibrary/` changes, update the installed Skill package deliberately.

Preferred update procedure:

1. Open `Plugins` → `Skills`.
2. Find `shared-knowledge-library` under `Installed` or `Created by me`.
3. Open it in the Skills editor if editing is available.
4. Replace/update `SKILL.md` and every supporting resource that changed in the repository.
5. Ensure `_LIBRARY_POLICY.md`, `scheduledprompt.md`, `bootstrap_migration.md`, `manifest.example.json`, and `README.md` remain attached to the same Skill package.
6. Save/update the Skill.
7. If the installed/uploaded copy cannot be edited in place, create/import a fresh copy of the complete package, verify it, then remove, disable, or stop using the old copy if the UI offers that control.
8. Repeat the update separately on each ChatGPT surface where you installed the Personal Skill.

ChatGPT can also help modify a Skill through the built-in skill-creator workflow. If you use that route, provide the complete package and explicitly require it to preserve the skill name `shared-knowledge-library`, the supporting resources, and the Drive IDs in this repository.

## Verify the installed version

After installing or updating, start a fresh chat and ask the installed Skill to describe its persistence architecture without making changes.

A correct current version should state all of the following:

- Google Drive `ChatGPT Library` is canonical general knowledge.
- Google Drive `Codex` is a separate operational domain.
- Known durable destinations are written directly to canonical Drive in the foreground.
- Uncertain but authorized durable files are staged in Google Drive `ChatGPT Ingress Queue`.
- Scheduled reconciliation is Google Drive only.
- Native ChatGPT Library is not a scheduled dependency.

Also ask it which supporting resources are bundled. It should recognize `scheduledprompt.md`, `bootstrap_migration.md`, `_LIBRARY_POLICY.md`, and `manifest.example.json` as part of the package and explain their roles.

If it still describes an hourly native-Library scan using `files.list` or `files.materialize`, or cannot see the supporting resources, the old or incomplete Skill version is still installed.

## Scheduled task deployment

Installing the Skill package does not itself create or update the optional recurring queue processor.

If deploying this architecture on a new ChatGPT installation:

1. Install the complete `SharedKnowledgeLibrary/` Skill package.
2. Verify access to canonical Google Drive `ChatGPT Library`.
3. Verify the live Drive `_LIBRARY_POLICY.md`.
4. Verify or create `ChatGPT Ingress Queue` and record its folder ID in the manifest.
5. Initialize or validate the manifest using `manifest.example.json` when needed.
6. Use `bootstrap_migration.md` for a first-time cutover or migration when applicable.
7. Create the optional recurring task from `scheduledprompt.md` only if queue reconciliation is desired.
8. Keep old Drive-to-native-Library sync jobs disabled.
9. Do not create a scheduled native ChatGPT Library inventory job.

## Governing principle

**One canonical general Drive library, one separate Codex operational library, foreground write-through to Drive as the correctness path, a private Drive queue for uncertain durable items, Drive-only scheduled reconciliation, and native ChatGPT Library only as immediate foreground access or optional interactive maintenance.**