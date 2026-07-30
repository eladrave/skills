---
name: drive-library-skill
description: Generate, revise, and, only after explicit user approval, install a folder-specific ChatGPT Library reference skill and a scheduled Google Drive-to-Library synchronization task from a full Google Drive folder URL. Use when a user wants to use a Google Drive folder and its subfolders as a reusable ChatGPT data source, create a "<folder name> as Reference" skill, generate its SKILL.md and scheduledprompt.md drafts, revise those drafts, or install the approved skill and scheduled task.
---

# Drive Library Skill

Create two folder-specific drafts from a Google Drive folder:

1. A ChatGPT Library reference `SKILL.md`
2. A Google Drive-to-Library `scheduledprompt.md`

Always generate and display the drafts first. Do not install either draft and do not create a scheduled task until the user explicitly authorizes the corresponding installation.

## Canonical templates

Use these files as the current reference implementations:

- Reference skill:
  `https://github.com/eladrave/skills/blob/main/ChatgptLibrary/MedicalRecords/SKILL.md`
- Scheduled prompt:
  `https://github.com/eladrave/skills/blob/main/ChatgptLibrary/MedicalRecords/scheduledprompt.md`

Fetch and read both files from GitHub before generating new drafts when the connected GitHub source is available.

Use them as structural and safety references. Do not blindly replace the phrase "Medical records." Remove medical-specific instructions unless the new folder is itself a medical-record folder or the user explicitly requests those instructions.

## Required input

Ask the user for the complete Google Drive folder URL if it was not provided.

Accept URLs such as:

`https://drive.google.com/drive/folders/FOLDER_ID`

Do not accept a folder name alone when the Drive URL or folder ID is still unknown.

If the URL includes query parameters, preserve the original URL for display but extract the folder ID from the `/folders/` path component.

## Validate the source folder

Before generating the drafts:

1. Extract the Google Drive folder ID.
2. Use the connected Google Drive source to read the folder metadata.
3. Confirm that:
   - The item exists.
   - The item is a folder.
   - It is not trashed.
   - The current user can access it.
   - Its direct children can be listed.
4. Use the folder name returned by Google Drive as the authoritative folder name.
5. Never infer the folder name from the URL or ask the user to type it when Drive metadata is available.
6. If authentication or access is unavailable, stop and explain the problem. Do not fabricate folder metadata or generate a supposedly final draft.

Use read-only Google Drive actions during this drafting phase. Do not modify the Drive folder or its contents.

## Determine the destination name

Use the authoritative Google Drive folder name to derive:

- Display name: `<Folder Name> as Reference`
- YAML skill name: a lowercase hyphenated form, such as `cynapsa-as-reference`
- ChatGPT Library path: `/<Folder Name>`
- Scheduled task title: `<Folder Name> Drive Library Sync`

Normalize the YAML skill name as follows:

1. Convert to lowercase.
2. Replace spaces and unsupported characters with hyphens.
3. Collapse repeated hyphens.
4. Remove leading and trailing hyphens.
5. Append `-as-reference`.
6. Keep the result under 64 characters.
7. If truncation could create a collision, append a short suffix derived from the Drive folder ID.

YAML skill names may not contain spaces. The human-facing heading may retain spaces and capitalization.

Preserve the Drive folder name for display whenever possible. If it contains `/`, `\`, control characters, or another character that cannot safely represent one Library path component, create a safe Library folder name and clearly show the mapping to the user.

## Schedule defaults

Default to:

- Frequency: Daily
- Time: 12:00 AM
- Timing mode: Exact schedule
- Time zone: The user's personal IANA time zone

If the user's time zone cannot be determined reliably, ask for it.

If the user provides another schedule, use it instead. Resolve ambiguous expressions such as "morning" before producing an exact scheduled-task configuration.

Do not create the scheduled task during the drafting phase.

## Drafting phase

Generate exactly two complete drafts:

1. `SKILL.md`
2. `scheduledprompt.md`

Display both drafts in separate Markdown code blocks.

After the drafts, state:

- The authoritative Drive folder name
- The extracted Drive folder ID
- The proposed Library folder path
- The proposed skill display name
- The normalized YAML skill name
- The proposed schedule and time zone
- That nothing has been installed or scheduled

Do not write to ChatGPT Library, install a skill, create an automation, synchronize files, or modify Google Drive during this phase.

## Generated SKILL.md requirements

Create a domain-neutral reference skill unless the user supplies domain-specific requirements.

The generated `SKILL.md` must:

1. Contain only `name` and `description` in YAML frontmatter.
2. Use the normalized `<folder-name>-as-reference` name.
3. Trigger when:
   - The user mentions the folder or its subject by name.
   - The user asks to use that Library folder as a source.
   - The user requests a summary, comparison, search, analysis, report, or artifact grounded in that folder.
4. Use the exact proposed Library path.
5. Search the Library folder recursively.
6. Paginate until the relevant inventory is complete.
7. Ignore `_drive_sync_manifest.json` as content evidence.
8. Use the manifest only for synchronization status and source mapping.
9. Read every file used to support a material claim.
10. Never treat a filename or search snippet as sufficient evidence.
11. Inspect relevant PDF pages, images, spreadsheets, presentations, or document structures when text extraction alone is insufficient.
12. Mark unreadable or ambiguous content rather than guessing.
13. Cite filenames and page numbers when available.
14. Cite the relevant filename and section when page numbers are unavailable.
15. Separate:
    - Source-documented facts
    - User-provided facts
    - Inferences
    - External knowledge
16. Identify contradictions and missing evidence.
17. Avoid web search unless the user asks for external information or the task materially requires current external facts.
18. Treat folder content as private.
19. Avoid exposing Drive IDs, Library IDs, manifest internals, connector details, or unnecessary personal information.
20. Validate generated reports, documents, spreadsheets, or presentations against the source files before presenting them.
21. Fail clearly when the Library folder is unavailable, empty, incomplete, or unreadable.

Do not include medical, financial, legal, or other domain-specific rules unless they match the source folder or the user explicitly requests them.

## Generated SKILL.md structure

Use a structure similar to:

```text
---
name: <normalized-folder-name>-as-reference
description: <complete trigger description>
---

# <Folder Name> as Reference

## Source rules
## Retrieval workflow
## Evidence requirements
## Response behavior
## Privacy
## Artifact creation
## Failure handling
```

Adapt the details to the folder's apparent purpose only when supported by the folder name, contents, or user instructions. Do not invent the folder's purpose.

## Generated scheduledprompt.md requirements

Create a complete scheduled-task draft that mirrors the Google Drive folder into the corresponding ChatGPT Library folder.

Include:

- Task title
- Schedule
- Time zone
- Timing mode
- Complete automation prompt

The automation prompt must include the authoritative:

- Drive folder name
- Drive folder ID
- Full Drive folder URL
- Library folder path

## Synchronization behavior

The generated automation prompt must instruct the task to:

1. Treat Google Drive as the sole source of truth.
2. Recursively enumerate every file and subfolder.
3. Preserve the relative folder hierarchy.
4. Create the Library root folder if it does not exist.
5. Preserve original filenames and bytes for stored, non-native Drive files.
6. Export native Google files using these defaults:
   - Google Docs to PDF
   - Google Sheets to XLSX
   - Google Slides to PDF
7. Add the corresponding extension to exported filenames.
8. Exclude comments, suggestions, permissions, and revision history unless the user requests another policy.
9. Maintain `_drive_sync_manifest.json` in the Library folder.
10. Record for each source item:
    - Drive file ID
    - Source relative path
    - MIME type
    - Modified time
    - Available checksum or revision metadata
    - Export format
    - Library relative path
    - Library file ID
    - Library version
11. Use stable Drive IDs to detect file moves and renames.
12. Preserve existing Library file identities and version history when updating files.
13. Move or rename Library items when corresponding Drive items move or are renamed.
14. Move Library items absent from Drive to Library trash only after a complete and successful source inventory.
15. Never permanently delete Library content.
16. Never modify or delete anything in Google Drive.

## New-file transfer behavior

Prefer creating a new Library file from a materialized workspace path.

If Drive returns a secure connector `file_uri` without a workspace path:

1. Create a temporary Library placeholder identity in the correct destination folder.
2. Immediately replace it using the Drive `file_uri`.
3. Supply the correct target filename, MIME type, and expected Library version.
4. Verify the resulting MIME type and byte size.
5. Count the item as created only after verification succeeds.
6. If replacement fails:
   - Move the placeholder to Library trash.
   - Record a failure.
   - Suppress all deletion reconciliation for that run.
7. Never leave placeholder content as the current version.

## Existing Library-folder protection

Before treating an existing Library folder as a mirror:

1. Look for `_drive_sync_manifest.json`.
2. Confirm that its source Drive folder ID matches the requested Drive folder ID.
3. If the folder exists without a manifest, stop and report a destination conflict.
4. If the manifest references another Drive folder, stop and report a source-mapping conflict.
5. Do not overwrite or delete existing Library content during a conflict.
6. Require explicit user direction before adopting or replacing an unrecognized destination folder.

## Safe mutation order

Use this order:

1. Validate Drive and Library access.
2. Complete the recursive Drive inventory.
3. Complete the recursive Library inventory.
4. Create required Library folders.
5. Create new files.
6. Replace modified files.
7. Move or rename existing files and folders.
8. Verify every successful transfer and mutation.
9. Update the synchronization manifest.
10. Move obsolete Library files to trash.
11. Remove empty obsolete Library folders only after their contents are safely reconciled.
12. Verify the final destination inventory.

## Fail-closed requirements

Suppress deletion reconciliation when:

- Drive access fails.
- Library access fails.
- Authentication is required.
- Source enumeration may be incomplete.
- A folder listing is truncated.
- Pagination cannot be completed.
- Duplicate paths are ambiguous.
- A source export or download fails.
- A Library upload or replacement cannot be verified.
- A mutation returns an unresolved failure.
- The manifest is missing or conflicts with the intended source.
- A protected Library artifact would be affected.
- Any other condition makes the source or destination inventory unreliable.

Independent safe creates or updates may continue only when doing so cannot create ambiguity. Deletion must remain suppressed for the entire run after any completeness or verification failure.

## Native Google export limits

Read Drive metadata before exporting a native Google file.

Use the normal Drive export operation when supported. If a native export exceeds the provider's export-size limit, use a supported streaming download with the requested export MIME type.

If neither export route succeeds:

- Record the affected file as failed.
- Do not create a partial or truncated destination file.
- Suppress deletion reconciliation for that run.

## Root-folder rename behavior

Use the Drive folder ID as the stable source identity.

If the Google Drive root folder name changes after installation:

- Do not silently change the Library root path.
- Report the detected rename.
- Continue using the existing mapped Library path only when the manifest confirms the same Drive folder ID.
- Recommend regenerating or updating the reference skill so its Library path remains accurate.
- Never create a second mirror solely because the source folder's display name changed.

## Run report

Require a concise report containing:

- Discovered source files
- Discovered source folders
- Created files
- Updated files
- Moved or renamed items
- Deleted-to-trash items
- Unchanged items
- Skipped items
- Conflicts
- Failures
- Whether deletion reconciliation was enabled or suppressed
- The reason deletion was suppressed, when applicable

## Draft output format

Display:

### `<Folder Name> as Reference/SKILL.md`

```markdown
<complete generated SKILL.md>
```

### `<Folder Name> as Reference/scheduledprompt.md`

```markdown
<complete generated scheduledprompt.md>
```

Then display a compact configuration summary.

## Revision phase

Allow the user to request changes to either draft.

During revisions:

- Update only the drafts.
- Preserve the validated Drive folder ID and authoritative folder name unless the user supplies another folder URL.
- Revalidate a new folder URL before using it.
- Recalculate names and paths when the source folder changes.
- Show the complete revised file, not only a patch, unless the user explicitly requests a diff.
- Do not install anything merely because the user says "looks good," "approved," or requests another change.

## Installation authorization

Treat installation as a separate phase.

Examples that authorize the generated skill installation:

- "Install the generated skill."
- "Add this reference skill to ChatGPT."
- "Install `<Folder Name> as Reference`."

Examples that authorize scheduled-task creation:

- "Create the scheduled task."
- "Install the synchronization task."
- "Schedule this sync."

Examples that authorize both:

- "Install both the generated skill and scheduled task."
- "Install everything we just reviewed."

Do not treat general approval, praise, or a revision request as installation authorization.

If the user authorizes only one artifact, install only that artifact.

## Installing the generated reference skill

After explicit authorization:

1. Use the platform's skill-creation and installation workflow.
2. Create the skill using the final approved `SKILL.md`.
3. Generate required UI metadata from the approved skill.
4. Validate the skill before installation.
5. Install only the approved version.
6. Verify that the skill is available.
7. Do not install the scheduled task unless separately authorized.

Do not silently alter the approved skill during installation. If validation requires a material change, show the corrected draft and obtain approval again.

## Creating the scheduled task

After explicit authorization:

1. Confirm the final schedule and time zone.
2. Perform harmless read-only checks against:
   - The source Google Drive folder
   - ChatGPT Library
3. Stop if either source requires connection, reconnection, or authorization.
4. Create an exact-schedule automation using the final approved prompt.
5. Verify:
   - Task title
   - Enabled status
   - Schedule
   - Time zone
   - Source folder ID
   - Destination Library path
6. Do not run the initial synchronization unless the user explicitly asks to run it.

## Initial synchronization

Run the task immediately only when the user explicitly requests an initial run or asks to verify the synchronization.

Before the run:

- Revalidate Drive and Library access.
- Reconfirm the source folder ID.
- Enumerate the complete Drive source tree.
- Inspect the Library destination and manifest state.

After the run:

- Verify filenames, relative paths, MIME types, and byte sizes.
- Confirm native export formats.
- Confirm that the manifest exists and maps the correct Drive folder ID.
- Confirm that no unexpected Library items remain.
- Report all changes and failures.
- State whether deletion reconciliation ran or was suppressed.

## Optional GitHub saving

Do not write generated drafts to GitHub unless the user explicitly requests it.

When requested:

1. Ask for or resolve the target repository and folder.
2. Check whether the destination files already exist.
3. Create or update only:
   - `SKILL.md`
   - `scheduledprompt.md`
4. Preserve unrelated repository content.
5. Read both files back from GitHub and verify their contents.
6. Do not treat saving drafts to GitHub as permission to install them.
