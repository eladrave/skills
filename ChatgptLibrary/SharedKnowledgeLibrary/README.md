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

There is no longer any need to mirror canonical Drive back into native ChatGPT Library.

ChatGPT can read the connected Drive directly. Removing Drive→Library mirroring eliminates the transfer failures, stale-copy problems, and duplicate-authority risk that affected the older Cynapsa and Medical Records jobs.

The only optional automation is **native ChatGPT Library → canonical Drive ingress** for files that ChatGPT auto-saved locally but that were not directly persisted by the handling agent.

## Skill behavior without a scheduled job

`SKILL.md` works independently of automation:

- read canonical knowledge directly from Drive;
- save authorized durable knowledge directly to Drive;
- interpret `save this to my Library` as canonical Drive;
- treat current-turn uploads as immediate sources while persisting them to Drive when requested;
- keep `Codex` semantically separate.

## Optional recurring ingress

`scheduledprompt.md` defines an hourly-style catch-up task that:

- inventories native Library;
- ignores `/Google Drive/**`;
- recognizes pre-cutover `/Medical records` and `/Cynapsa` native trees as legacy Drive-backed copies;
- ingests new durable native-Library-only content into Drive;
- adopts existing Drive equivalents rather than duplicating them;
- refuses to overwrite/delete canonical Drive from native Library changes;
- holds operational/credential-bearing items for classification instead of copying them into both roots.

## Legacy jobs

The older jobs:

- `Medical Records Sync`
- `Sync Cynapsa Drive`

were designed to mirror Drive into native Library. They are unnecessary after the ingress-only cutover because Drive itself is now the canonical retrieval surface.

They should be disabled after direct Drive read/write and ingress-control validation, then kept disabled temporarily for rollback rather than immediately deleted.

## Files

- `SKILL.md`: cross-agent behavior and ownership rules.
- `_LIBRARY_POLICY.md`: live policy source, intended to live in canonical Drive.
- `bootstrap_migration.md`: one-time safe cutover procedure.
- `scheduledprompt.md`: optional recurring native-Library ingress job.
- `manifest.example.json`: ingress state schema.
- `README.md`: this architecture and deployment guide.

## Installation

Only `SKILL.md` needs to be installed as the skill.

The live `_LIBRARY_POLICY.md` must exist separately at the canonical Drive root so every installation reads the same policy.

Installing the skill does not itself create the optional ingress task.

## Governing principle

**One canonical general Drive library, one separate Codex operational library, native ChatGPT Library only as immediate access and optional ingress.**
