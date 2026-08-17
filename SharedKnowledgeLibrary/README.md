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

`SharedKnowledgeLibrary/SKILL.md` is the only general Library skill required.

It includes domain-specific behavior for `Medical records` and covers `Cynapsa` and all future subfolders under the canonical Drive root. Adding another folder under `ChatGPT Library` does not require another skill or another Drive-to-Library sync task.

The old `ChatgptLibrary/MedicalRecords` and `ChatgptLibrary/DriveLibraryMetaSkill` sources are retired by this architecture.

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

`scheduledprompt.md` now defines a **Drive-only** queue processor.

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

## Files

- `SKILL.md`: install this skill.
- `_LIBRARY_POLICY.md`: version-controlled source for the live policy stored in canonical Drive.
- `bootstrap_migration.md`: historical one-time cutover procedure and reference, not a recurring architecture.
- `scheduledprompt.md`: optional recurring Drive-only ingress queue processor.
- `manifest.example.json`: control-state schema including the Drive queue.
- `README.md`: architecture and deployment guide.

## Installation

Install only:

`SharedKnowledgeLibrary/SKILL.md`

The live `_LIBRARY_POLICY.md` exists separately at the canonical Drive root so every installation reads the same policy.

Installing the skill does not itself create the optional queue folder or recurring task. Those are separately authorized actions.

## Governing principle

**One canonical general Drive library, one separate Codex operational library, foreground write-through to Drive as the correctness path, a private Drive queue for uncertain durable items, Drive-only scheduled reconciliation, and native ChatGPT Library only as immediate foreground access or optional interactive maintenance.**