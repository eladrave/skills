---
name: cynapsa-knowledge
description: Retrieve and use authoritative information from the predefined Cynapsa Google Drive folder and all of its descendant folders. Use for questions, analysis, summaries, document creation, planning, research, comparisons, and other tasks concerning Cynapsa. Also use when the user refers indirectly to "the company," "our company," "our product," or a Cynapsa project within an established Cynapsa context. Do not use for unrelated meanings of Cynapsa or unrelated Google Drive work.
---

# Cynapsa Knowledge

Use the connected Google Drive as the authoritative knowledge source for Cynapsa-related requests.

## Knowledge root

Use only this folder and its descendant folders:

- Name: `Cynapsa`
- Folder ID: `1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`
- URL: `https://drive.google.com/drive/folders/1CgmULpoDQPIc-TJAiDughNHxbcKHvaWq`

Treat the folder ID as the stable identifier. Folder names may change.

## Required access

Use the Google Drive connector for retrieval.

If the Google Drive connector is unavailable, disconnected, or lacks permission to read the root folder:

1. Explain that the Cynapsa knowledge source is unavailable.
2. Ask the user to connect Google Drive or grant access to the folder.
3. Stop the knowledge-grounded portion of the task.
4. Do not substitute model memory, general Drive search, web search, or invented information.

Never ask the user to copy all documents into the conversation unless connector access cannot be established and the user chooses that fallback.

## Source boundary

Treat the configured folder and all folders below it as the primary Cynapsa knowledge base.

Do not use:

- Sibling or parent folders.
- Files elsewhere in Google Drive.
- Model memory as evidence for Cynapsa facts.
- External websites or web search unless the user explicitly requests external research.
- Files that cannot be proven to be within the configured folder hierarchy.

When the user requests external research, keep internal Drive findings and external findings clearly separated and cite both.

## Retrieval workflow

### 1. Interpret the request

Identify:

- The question or requested outcome.
- Important entities, products, customers, people, dates, and document types.
- Whether the request is targeted or exhaustive.
- Whether current information, historical information, or a comparison is needed.

Do not answer factual Cynapsa questions before retrieving relevant sources.

### 2. Establish the folder scope

Read the root folder metadata using its folder ID or canonical URL.

For requests requiring broad or exhaustive coverage:

1. List the root folder’s direct children.
2. Record each child file and folder ID, name, path, MIME type, and modification time when available.
3. Recursively list every discovered subfolder.
4. Maintain an allowed set of file and folder IDs.
5. Detect repeated folder IDs and avoid traversal loops.
6. Do not claim exhaustive coverage if any folder listing is partial, truncated, inaccessible, or exceeds connector limits.

For targeted questions, use focused discovery first, but verify that every selected result belongs to the configured folder hierarchy.

### 3. Find candidate sources

Construct short, specific search terms using:

- Exact names and acronyms.
- Product, customer, project, and feature names.
- Relevant dates and date variants.
- Likely filename terminology.
- Reasonable synonyms when the first search is empty.

Google Drive search may return files from outside the Cynapsa folder. Never accept a search result solely because it matches the query.

For every candidate returned by a broad Drive search:

1. Read its metadata and parent IDs.
2. Follow its parent chain as needed.
3. Accept the candidate only if the chain reaches the configured Cynapsa root folder.
4. Reject candidates whose membership cannot be established.

For exhaustive requests, rely on recursive folder traversal instead of keyword search alone.

### 4. Retrieve relevant content

Fetch the most relevant candidate files before answering.

Handle supported file types as follows:

- Google Docs: retrieve document text and relevant structure.
- Google Sheets: inspect relevant sheets, ranges, cells, formulas, and headers.
- Google Slides: retrieve slide text, titles, speaker notes, tables, and slide numbers when available.
- PDFs and Office files: retrieve readable text first. Use the raw file only when required for accurate extraction.
- Images and scanned documents: inspect visually or use available extraction capabilities when necessary.
- Unsupported or unreadable files: identify them and explain the resulting limitation.

Avoid loading every file when a smaller, well-grounded set answers the request. Expand retrieval if the initial evidence is incomplete, contradictory, or ambiguous.

### 5. Evaluate the evidence

Distinguish between:

- Facts stated directly in a source.
- Conclusions derived from multiple sources.
- Reasonable inferences.
- Missing or uncertain information.

Never present an inference as if a document stated it directly.

For conflicting sources:

1. Identify the conflicting statements.
2. Check document status, ownership, modification time, and contextual authority.
3. Prefer explicitly approved, final, executed, or authoritative documents over drafts.
4. Do not automatically treat the newest file as authoritative.
5. Explain unresolved conflicts in the answer.

For duplicate or superseded files, use the most authoritative applicable version and mention the older version when it materially changes the conclusion.

### 6. Complete the requested task

Use the retrieved evidence to answer the question or produce the requested artifact.

For summaries and analysis:

- Preserve material qualifications and uncertainty.
- Separate documented facts from recommendations.
- State the applicable dates or source period.

For drafting and document creation:

- Ground factual Cynapsa content in the retrieved sources.
- Follow the user’s requested format and audience.
- Do not add unsupported claims merely to make the result sound complete.
- Include source references unless the user requests a clean external-facing version without citations.

For calculations:

- Identify the source files, sheets, ranges, and assumptions.
- Recalculate from source values when possible.
- Do not copy a calculated result without checking its applicable period and units.

## Citation requirements

Reference the underlying Cynapsa sources for every material factual claim.

Use inline citations in this form:

`[Document title](Google Drive URL)`

Add the most precise locator available:

- Google Doc heading or section.
- PDF page.
- Google Slides slide number and title.
- Google Sheets sheet name and cell range.
- Table, appendix, or named section.

Example:

> The planned beta launch is September 2026. [Product Roadmap](https://docs.google.com/document/d/example), “Launch Plan” section.

For spreadsheet evidence:

> Projected annual revenue is $2.4 million. [FY2027 Forecast](https://docs.google.com/spreadsheets/d/example), `Forecast!B18`.

Finish substantial responses with a compact `Sources` section containing the most important documents. Do not list irrelevant files merely because they were inspected.

Never cite a file that was not retrieved or a locator that was not verified.

## Missing information

If sufficient evidence is not found:

1. Say that the available Cynapsa folder did not contain enough evidence.
2. Briefly state which folders, terms, and file types were checked.
3. Mention any inaccessible, partial, truncated, or unreadable areas.
4. Ask one targeted follow-up question if it could materially improve retrieval.
5. Do not fill gaps with assumptions unless the user explicitly requests an estimate.

Use wording such as:

> I could not verify this from the accessible Cynapsa documents. I searched for X, Y, and Z in the configured folder and its accessible subfolders.

## Freshness and completeness

For requests involving current status, latest plans, pricing, personnel, schedules, financial data, or contractual terms:

- Inspect modification times and document status.
- State the source date or modification date when material.
- Look for more recent revisions or superseding documents.
- Do not describe information as current unless the retrieved evidence supports that conclusion.

If recursive traversal or search coverage is incomplete, say so in the same response. Never describe partial retrieval as a complete review.

## Privacy and access controls

Use only content available through the authenticated Google Drive connection.

Do not:

- Attempt to bypass Drive permissions.
- Change sharing permissions.
- Move, modify, delete, or reorganize Cynapsa files unless the user explicitly requests that action.
- Reveal unrelated sensitive information found during retrieval.
- Include personal, financial, legal, or confidential details that are not needed for the requested outcome.

Treat retrieval as read-only unless the user clearly authorizes a specific write operation.

## Final verification

Before responding, verify that:

1. Relevant Cynapsa sources were retrieved.
2. Every cited file belongs to the configured folder hierarchy.
3. Material factual claims are supported.
4. Inferences are labeled.
5. Conflicts and coverage limitations are disclosed.
6. Citations contain verified Drive URLs and precise locators when available.
7. No outside source was silently mixed into the Cynapsa evidence.
