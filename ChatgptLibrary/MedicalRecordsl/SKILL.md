---
name: use-medical-records-library
description: Use the user's synchronized ChatGPT Library folder "/Medical records" as the documentary source for questions and tasks involving the user's medical history, surgeries, diagnoses, treatments, medications, examinations, office notes, hospitalizations, rehabilitation, test results, insurance records, disability documentation, or medical-record-based letters and summaries. Trigger when the user asks what their records say, requests a health-history summary or timeline, asks to locate a documented medical fact, compare records, identify contradictions, or create an artifact grounded in their personal medical records.
---

# Medical Records Library

Use the ChatGPT Library folder `/Medical records` as the primary documentary source.

Treat the folder contents as sensitive personal medical information. Access only the information needed for the user's request.

## Source rules

- Search only within `/Medical records` unless the user requests additional sources.
- Search the folder recursively, including all subfolders.
- Ignore `_drive_sync_manifest.json` as medical evidence. Use it only when checking synchronization status or source mappings.
- Treat each document as evidence of what was recorded on its document date, not necessarily the user's current condition.
- Treat the user's current message as authoritative for current circumstances when it clearly updates an older record.
- Keep record-derived facts, user-provided facts, medical interpretation, and general medical knowledge clearly separated.
- Do not use web search unless the user requests current external information or the task requires current medical guidance beyond the records.

## Retrieval workflow

1. Identify the exact medical question, requested date range, person, procedure, condition, or document type.
2. Search ChatGPT Library with the scope restricted to `/Medical records`.
3. For a targeted question, locate the most relevant files using filenames and extracted content.
4. For a comprehensive history, timeline, or records review:
   - Inventory the folder recursively.
   - Paginate until the complete folder inventory is retrieved.
   - Review every potentially relevant file.
5. Read the actual contents of every file used to support the answer. Never treat filenames or search snippets as sufficient evidence.
6. Use exact-text search when locating a named condition, anatomical level, medication, provider, procedure, or date.
7. Inspect relevant PDF pages or images visually when layout, handwriting, tables, scans, diagrams, signatures, or OCR quality may affect the answer.
8. Mark unreadable or ambiguous content rather than guessing.
9. Check for conflicting dates, diagnoses, medication lists, anatomical descriptions, or treatment plans across documents.
10. Answer only after the relevant source files have been reviewed.

## Evidence requirements

- Cite each material medical claim using the filename and page number when available.
- Use this citation format: `(Source: filename, page 12)`.
- If page numbers are unavailable, cite the filename and the relevant section, date, or heading.
- Never invent page numbers, dates, providers, diagnoses, procedures, or quotations.
- Use short quotations only when exact wording materially matters.
- State explicitly when the available records do not establish the requested fact.
- Identify contradictions rather than silently choosing one version.
- For inferred conclusions, label them clearly as inference and explain the supporting evidence.

## Response structure

For simple questions, lead with the direct answer, followed by supporting evidence and any uncertainty.

For comprehensive reviews, use this structure:

1. Executive summary
2. Chronological timeline
3. Diagnoses and documented findings
4. Procedures and hospitalizations
5. Medications and treatments
6. Rehabilitation and follow-up
7. Current or most recently documented status
8. Conflicts, gaps, and unresolved questions
9. Sources reviewed

Include exact dates whenever available.

## Medical boundaries

- Do not present an unsupported diagnosis or treatment recommendation as established fact.
- Do not assume that an old diagnosis, medication, insurance policy, or treatment plan remains current.
- For current symptoms, medication decisions, treatment choices, or urgent health concerns, use the connected Health source when available and distinguish its information from Library documents.
- If potentially urgent symptoms are described, prioritize appropriate safety guidance instead of relying only on historical records.
- Do not claim professional medical credentials.

## Privacy

- Do not repeat full insurance identifiers, addresses, account numbers, phone numbers, dates of birth, or other sensitive identifiers unless they are essential to the requested task.
- Do not expose Library file IDs, Drive IDs, synchronization metadata, connector details, or internal references.
- Do not include unrelated medical information merely because it appears in the records.
- Treat all outputs as private medical information.

## Document creation

When creating a letter, summary, timeline, form, or report from the records:

- Follow the user's requested scope and date range exactly.
- Preserve documented terminology where precision matters.
- Separate documented findings from interpretation.
- Include a concise source list.
- Include limitations when records are incomplete, contradictory, outdated, or unreadable.
- Validate the finished artifact against the source records before presenting it.

## Failure handling

If `/Medical records` is unavailable, empty, incomplete, or cannot be searched:

- State the access or coverage limitation clearly.
- Do not answer from memory as though the records were reviewed.
- Ask the user to verify Library access or synchronization when necessary.

If a relevant document cannot be read:

- Identify the affected filename.
- Explain what could not be verified.
- Continue with unaffected evidence when doing so would not create a misleading conclusion.
