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

It owns credentials, infrastructure, deployment/recovery runbooks, connection details, and other operational agent memory.

## Final architecture

```text
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
└── Codex/                           CANONICAL OPERATIONAL KNOWLEDGE

Native ChatGPT Library
    = immediate access + optional ingress
    ≠ canonical authority
```

## Important simplification

There is no need to mirror canonical Drive back into native ChatGPT Library.

ChatGPT can read the connected Drive directly. Removing Drive→Library mirroring eliminates transfer failures, stale-copy problems, and duplicate-authority risk from the older per-folder jobs.

The only optional automation is **native ChatGPT Library → canonical Drive ingress** for files that ChatGPT auto-saved locally but that were not directly persisted by the handling agent.

## One skill for the whole library

`SharedKnowledgeLibrary/SKILL.md` is the only general Library skill required.

It includes domain-specific behavior for `Medical records` and covers `Cynapsa` and all future subfolders under the canonical Drive root. Adding another folder under `ChatGPT Library` does not require another skill or another Drive-to-Library sync task.

The old `ChatgptLibrary/MedicalRecords` and `ChatgptLibrary/DriveLibraryMetaSkill` sources are retired by this architecture.

## Skill behavior without a scheduled job

`SKILL.md` works independently of automation:

- read canonical knowledge directly from Drive;
- save authorized durable knowledge directly to Drive;
- interpret `save this to my Library` as canonical Drive;
- treat current-turn uploads as immediate sources while persisting them to Drive when requested;
- keep `Codex` semantically separate.

## Optional recurring ingress

`scheduledprompt.md` defines the catch-up task that:

- inventories native Library;
- ignores `/Google Drive/**`;
- recognizes pre-cutover `/Medical records` and `/Cynapsa` native trees as legacy Drive-backed copies;
- ingests new durable native-Library-only content into Drive;
- adopts existing Drive equivalents rather than duplicating them;
- refuses to overwrite/delete canonical Drive from native Library changes;
- holds operational/credential-bearing items for classification instead of copying them into both roots.

## Legacy jobs

The older `Medical Records Sync` and `Sync Cynapsa Drive` jobs mirrored Drive into native Library. They are disabled and no longer needed because Drive itself is the canonical retrieval surface.

## Files

- `SKILL.md`: install this skill.
- `_LIBRARY_POLICY.md`: version-controlled source for the live policy stored in canonical Drive.
- `bootstrap_migration.md`: one-time safe cutover procedure and reference.
- `scheduledprompt.md`: optional recurring native-Library ingress job.
- `manifest.example.json`: ingress state schema.
- `README.md`: architecture and deployment guide.

## Installation

Install only:

`SharedKnowledgeLibrary/SKILL.md`

The live `_LIBRARY_POLICY.md` exists separately at the canonical Drive root so every installation reads the same policy.

Installing the skill does not itself create the optional ingress task.

## Governing principle

**One canonical general Drive library, one separate Codex operational library, native ChatGPT Library only as immediate access and optional ingress.**