# SharedKnowledgeLibrary External Canonical Sources

> Deployment target: place this file at the root of the canonical Google Drive `ChatGPT Library` folder.

This file defines knowledge domains that are intentionally **not** stored under the general SharedKnowledgeLibrary Drive root.

It is an ownership and routing registry. It should contain pointers and synchronization direction, not copies of the external sources' substantive content.

## 1. Medical records

### Canonical source

- Name: `Medical records`
- Google Drive folder ID: `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- URL: `https://drive.google.com/drive/folders/1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`

### ChatGPT native Library mirror

- Path: `/Medical records`
- Existing scheduled task: `Medical Records Sync`
- Direction: `Google Drive -> ChatGPT native Library`

### Ownership rules

- Google Drive `Medical records` is the sole canonical source for this domain.
- Native Library `/Medical records` is a ChatGPT read mirror.
- Never copy `/Medical records/**` into `Google Drive / ChatGPT Library`.
- Never synchronize changes from native Library `/Medical records` back to its Drive source.
- Never infer a Drive deletion from a Library deletion.
- Ignore `_drive_sync_manifest.json` in this subtree as substantive medical content.

## 2. Cynapsa

### Canonical source

- Name: `Cynapsa`
- Google Drive folder ID: `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`
- URL: `https://drive.google.com/drive/folders/1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

### ChatGPT native Library mirror

- Path: `/Cynapsa`
- Existing scheduled task: `Sync Cynapsa Drive`
- Direction: `Google Drive -> ChatGPT native Library`

### Ownership rules

- Google Drive `Cynapsa` is the sole canonical source for this domain.
- Native Library `/Cynapsa` is a ChatGPT read mirror.
- Never copy `/Cynapsa/**` into `Google Drive / ChatGPT Library`.
- Never synchronize changes from native Library `/Cynapsa` back to its Drive source.
- Never infer a Drive deletion from a Library deletion.
- Ignore `_drive_sync_manifest.json` in this subtree as substantive Cynapsa content.

## 3. Codex operational knowledge

### Canonical source

- Name: `Codex`
- Google Drive folder ID: `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`
- URL: `https://drive.google.com/drive/folders/18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`
- Governing skill: `CodexAsKnowledgeReadWrite`

### Purpose

The Codex domain owns durable environment-specific operational knowledge such as:

- Credentials and tokens.
- Private infrastructure endpoints.
- Deployment and recovery runbooks.
- SSH and host connection instructions.
- Container/runtime topology.
- Production service state.
- Database operational access.
- MCP connection information.
- Cloud/network operational details.
- Configuration ownership and maintenance procedures.

### Ownership rules

- Do not mirror the Codex folder into SharedKnowledgeLibrary.
- Do not copy Codex-owned facts into SharedKnowledgeLibrary just so a different agent can read them.
- ChatGPT, Codex, and other authorized agents should read Codex directly when operational knowledge is needed.
- If native ChatGPT Library contains historical operational files, do not automatically export them to SharedKnowledgeLibrary.
- Do not automatically move such files into Codex either. Reconcile them only under an explicitly authorized task after checking existing canonical Codex owners.

## 4. Google Drive mounted Library surface

ChatGPT Library may expose a mounted Google Drive surface such as:

`/Google Drive`

This is an access/mount surface, not a native-Library source to export.

### Ownership rules

- Recursively exclude `/Google Drive/**` from every native-Library -> Drive migration or synchronization.
- Never copy a Google Drive mount back into Google Drive.
- A Drive item discovered through the mount retains the ownership of its actual Drive location.

## Native Library hard exclusions

The SharedKnowledgeLibrary Library-to-Drive migration and recurring ingestion workflow must recursively exclude at least:

```text
/Medical records/**
/Cynapsa/**
/Google Drive/**
```

These exclusions are path-based safeguards in addition to semantic ownership checks.

## Operational-candidate detection

Files outside the hard exclusions may still belong to Codex operational knowledge.

Treat a native Library file or folder as a potential Codex-routing candidate when its primary purpose is one or more of:

- Storing credentials, passwords, tokens, keys, or credential-bearing URLs.
- Explaining how to connect to a private system.
- Recording SSH, production host, database, MCP, cloud, or network access.
- Describing deployment, rollback, recovery, container, service, or infrastructure operations.
- Recording environment-specific runtime paths or private topology.

For an obvious operational candidate:

1. Do not ingest it into the general Drive library.
2. Check whether an existing Codex canonical owner already covers it when the current task permits that read.
3. If redundant, skip it.
4. If potentially unique, report it for deliberate Codex reconciliation.
5. Never create duplicate secret-bearing operational sources automatically.

## Adding another external canonical source

When another Google Drive folder becomes an independently canonical domain:

1. Add a section here with its stable folder ID and URL.
2. State its purpose.
3. State whether it has a ChatGPT native Library mirror.
4. State the allowed synchronization direction.
5. Add any required native Library hard exclusion path.
6. Do not copy its substantive content into this registry.
