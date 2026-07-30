---
name: drive-folder-rag
description: Generate, revise, and optionally install a folder-specific Google Drive RAG skill from a Google Drive folder URL. Use when the user wants a reusable skill that treats one Drive folder and all its descendant folders as an authoritative retrieval source. Resolve the real folder name and ID through Google Drive, generate a complete folder-named RAG SKILL.md, and show it as a draft. Never install, save, activate, upload, or publish the generated skill unless the user explicitly asks to install it.
---

# Drive Folder RAG

Generate a folder-specific Google Drive retrieval skill that uses one Drive folder and all its descendant folders as its authoritative knowledge source.

Default to draft-only behavior.

## Required input

Obtain a complete Google Drive folder URL from the user.

Example:

```text
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
```

If the user has not provided a folder URL, ask:

> What is the full Google Drive folder URL you want to use as the RAG knowledge source?

Ask only for the folder URL unless another missing value is necessary.

## Validate the folder

### 1. Parse the URL

Accept a canonical Google Drive folder URL containing:

```text
drive.google.com/drive/folders/<FOLDER_ID>
```

The URL may contain query parameters or a trailing slash.

Extract the folder ID from the URL. Do not infer or invent an ID.

Reject:

- Google Docs, Sheets, or Slides URLs.
- Direct file URLs.
- Malformed Drive URLs.
- URLs that do not identify a folder.
- Plain folder names without a URL.

If the URL is invalid, explain the expected format and ask for a valid folder URL.

### 2. Resolve the folder through Google Drive

Use the connected Google Drive connector to read the folder metadata.

Request sufficient metadata to establish:

- File ID.
- Name.
- MIME type.
- Parent IDs when available.
- Shortcut details when applicable.
- Canonical or web-view URL when available.
- Modification time when available.

Verify that the resolved MIME type represents a Google Drive folder.

If the URL identifies a folder shortcut, resolve its target folder when supported. Use the target folder ID, name, and canonical URL as the knowledge root. Do not silently use a shortcut when its target cannot be established.

Support folders in My Drive, shared folders, and shared drives when the authenticated Google account has access.

If the connector is unavailable, disconnected, or lacks permission:

1. Explain the access problem.
2. Ask the user to connect Google Drive or grant access.
3. Do not generate a folder-specific skill using guessed metadata.
4. Do not substitute a different folder.

### 3. Use authoritative metadata

Use the folder name returned by Google Drive, not a name guessed from the URL or supplied separately by the user.

Preserve the folder name's capitalization and punctuation in the generated skill's heading, descriptions, body, and source references.

Use the stable folder ID for retrieval even if the folder is renamed later.

## Generate the skill name

Create two names.

### Human-facing name

Use:

```text
<Exact Folder Name> as RAG
```

### YAML skill name

Generate:

```text
<folder-slug>-as-rag
```

Normalize the folder name as follows:

1. Convert it to lowercase.
2. Normalize accented characters when possible.
3. Replace spaces and punctuation with hyphens.
4. Remove characters other than lowercase letters, digits, and hyphens.
5. Collapse repeated hyphens.
6. Remove leading and trailing hyphens.
7. Add the suffix `-as-rag`.
8. Keep the complete name under 64 characters.
9. Preserve the `-as-rag` suffix when shortening the folder portion.

If normalization produces an empty folder slug, use:

```text
drive-folder-<first-eight-folder-id-characters>-as-rag
```

Before installation, check for an existing skill with the same YAML name. Do not overwrite an existing skill without explicit authorization.

## Generate the draft

Replace every placeholder in the template:

- `{{SKILL_NAME}}`: Valid lowercase hyphenated YAML skill name.
- `{{FOLDER_NAME}}`: Exact folder name returned by Google Drive.
- `{{FOLDER_ID}}`: Verified Google Drive folder ID.
- `{{FOLDER_URL}}`: Verified canonical folder URL.

Escape the folder name correctly if it contains Markdown-sensitive or YAML-sensitive characters. Do not leave unresolved placeholders.

## Generated SKILL.md template

```md
---
name: {{SKILL_NAME}}
description: Retrieve and use authoritative information from the predefined "{{FOLDER_NAME}}" Google Drive folder and all of its descendant folders. Use for questions, analysis, summaries, document creation, planning, research, comparisons, and other tasks concerning {{FOLDER_NAME}} or the information maintained in that folder. Also use for indirect references to the folder's subject when the current conversation clearly establishes a {{FOLDER_NAME}} context. Do not use for unrelated meanings of {{FOLDER_NAME}} or unrelated Google Drive work.
---

# {{FOLDER_NAME}} as RAG

Use the connected Google Drive as the authoritative knowledge source for requests concerning {{FOLDER_NAME}}.

## Knowledge root

Use only this folder and its descendant folders:

- Name: `{{FOLDER_NAME}}`
- Folder ID: `{{FOLDER_ID}}`
- URL: `{{FOLDER_URL}}`

Treat the folder ID as the stable identifier. The folder name may change.

## Required access

Use the Google Drive connector for retrieval.

If the Google Drive connector is unavailable, disconnected, or lacks permission to read the root folder:

1. Explain that the {{FOLDER_NAME}} knowledge source is unavailable.
2. Ask the user to connect Google Drive or grant access to the folder.
3. Stop the knowledge-grounded portion of the task.
4. Do not substitute model memory, general Drive search, web search, or invented information.

Never ask the user to copy all documents into the conversation unless connector access cannot be established and the user chooses that fallback.

## Source boundary

Treat the configured folder and all folders below it as the primary {{FOLDER_NAME}} knowledge base.

Do not use:

- Sibling or parent folders.
- Files elsewhere in Google Drive.
- Model memory as evidence for folder-specific facts.
- External websites or web search unless the user explicitly requests external research.
- Files that cannot be proven to be within the configured folder hierarchy.

When the user requests external research, keep internal Drive findings and external findings clearly separated and cite both.

## Retrieval workflow

### 1. Interpret the request

Identify the requested outcome, important entities, dates, document types, desired time period, and whether the request is targeted or exhaustive.

Do not answer factual questions about {{FOLDER_NAME}} before retrieving relevant sources.

### 2. Establish the folder scope

Read the root folder metadata using its folder ID or canonical URL.

For broad or exhaustive requests:

1. List the root folder's direct children.
2. Record each child's ID, name, path, MIME type, and modification time when available.
3. Recursively list every discovered subfolder.
4. Maintain an allowed set of file and folder IDs.
5. Detect repeated folder IDs and avoid traversal loops.
6. Do not claim exhaustive coverage if any listing is partial, truncated, inaccessible, or exceeds connector limits.

For targeted questions, use focused discovery first, but verify that every selected result belongs to the configured folder hierarchy.

### 3. Find candidate sources

Construct short, specific searches using exact names, acronyms, dates, likely filename terminology, and reasonable synonyms.

Google Drive search may return files from outside the configured folder. Never accept a result solely because it matches the query.

For every candidate returned by broad Drive search:

1. Read its metadata and parent IDs.
2. Follow its parent chain as needed.
3. Accept it only if the chain reaches the configured root folder.
4. Reject it if membership cannot be established.

For exhaustive requests, rely on recursive traversal instead of keyword search alone.

### 4. Retrieve relevant content

Fetch the most relevant candidate files before answering:

- Google Docs: retrieve text and relevant structure.
- Google Sheets: inspect relevant sheets, ranges, cells, formulas, and headers.
- Google Slides: retrieve slide text, titles, notes, tables, and slide numbers when available.
- PDFs and Office files: retrieve readable text first, then raw files when accurate extraction requires it.
- Images and scans: inspect visually or use available extraction capabilities.
- Unsupported files: identify them and disclose the limitation.

Avoid loading every file when a smaller grounded set is sufficient. Expand retrieval when evidence is incomplete, contradictory, or ambiguous.

### 5. Evaluate the evidence

Distinguish direct facts, multi-source conclusions, reasonable inferences, and missing information. Never present an inference as if a source stated it directly.

For conflicting or duplicate sources:

1. Identify the conflict.
2. Check status, ownership, modification time, and contextual authority.
3. Prefer approved, final, executed, or authoritative documents over drafts.
4. Do not automatically treat the newest file as authoritative.
5. Explain unresolved conflicts.

### 6. Complete the task

Use the retrieved evidence to answer the question or produce the requested artifact.

- Preserve qualifications and uncertainty.
- Separate documented facts from recommendations.
- State applicable dates or source periods.
- Ground created content in retrieved sources.
- Do not add unsupported claims to make an output appear complete.
- For calculations, identify source sheets, ranges, units, periods, and assumptions, then recalculate when possible.

## Citation requirements

Reference the underlying Drive sources for every material factual claim.

Use:

`[Document title](Google Drive URL)`

Add the most precise locator available:

- Google Doc heading or section.
- PDF page.
- Google Slides slide number and title.
- Google Sheets sheet name and cell range.
- Table, appendix, or named section.

Finish substantial responses with a compact `Sources` section. Never cite a file that was not retrieved or a locator that was not verified.

## Missing information

If sufficient evidence is not found:

1. Say that the accessible {{FOLDER_NAME}} folder did not contain enough evidence.
2. State which folders, terms, and file types were checked.
3. Mention inaccessible, partial, truncated, or unreadable areas.
4. Ask one targeted follow-up question when it could improve retrieval.
5. Do not fill gaps with assumptions unless the user explicitly requests an estimate.

## Freshness and completeness

For current status, plans, pricing, personnel, schedules, financial data, or contractual terms:

- Inspect modification times and document status.
- State source dates when material.
- Look for later revisions or superseding documents.
- Do not call information current without supporting evidence.

Disclose incomplete traversal or search coverage in the same response. Never describe partial retrieval as complete.

## Privacy and access controls

Use only content available through the authenticated Google Drive connection.

Do not bypass Drive permissions, change sharing, move or modify files without explicit authorization, or reveal unrelated sensitive information.

Treat retrieval as read-only unless the user clearly authorizes a specific write operation.

## Final verification

Before responding, verify that:

1. Relevant sources were retrieved.
2. Every cited file belongs to the configured hierarchy.
3. Material claims are supported.
4. Inferences are labeled.
5. Conflicts and coverage limitations are disclosed.
6. Citations contain verified Drive URLs and precise locators when available.
7. No outside source was silently mixed into the folder-specific evidence.
```

## Validate the generated draft

Before presenting it, verify:

1. The YAML frontmatter contains only `name` and `description`.
2. The YAML name is valid and under 64 characters.
3. The folder name, ID, and URL match verified Drive metadata.
4. No placeholder remains.
5. Recursive subfolders and folder-membership verification are covered.
6. The generated skill is read-only by default.
7. Installation is not performed or implied.

Correct validation problems before showing the draft.

## Present the generated draft

Return:

1. The resolved folder name and verified URL.
2. The proposed human-facing and YAML skill names.
3. The complete generated `SKILL.md` in one Markdown code block.
4. A statement that it is a draft and has not been installed.

Do not return a partial excerpt unless explicitly requested.

## Revision workflow

Treat the most recent generated version in the conversation as the active draft.

When the user requests changes:

1. Update the active draft.
2. Preserve the verified folder ID and source boundary unless the user changes the source folder.
3. Revalidate it.
4. Show the complete revised text.
5. State that it remains uninstalled.

Do not treat approval, a request to save locally, or a request to push to GitHub as installation authorization.

## Installation boundary

Install only after an explicit instruction such as:

- "Install this skill."
- "Install the generated skill."
- "Add this skill to my ChatGPT skills."
- "Activate this as a personal skill."

If the instruction is ambiguous, ask whether the user wants installation.

## Installation workflow

After explicit authorization:

1. Use the latest complete draft.
2. Reconfirm the intended source folder ID and URL.
3. Check for a personal skill with the same YAML name.
4. Ask before replacing or updating an existing skill.
5. Use the official skill-creation workflow.
6. Write the approved text as `SKILL.md`.
7. Generate matching interface metadata.
8. Validate, install, and verify the personal skill.
9. Report success only after verification.

Do not substantively modify the approved draft during installation without showing the correction and obtaining approval.

Installing the generated skill does not authorize modifying Drive files, changing Drive permissions, publishing it, pushing it to GitHub, replacing another skill, or installing this meta-skill itself.
