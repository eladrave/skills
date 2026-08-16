---
name: use-medical-records-library
description: Use the user's canonical Google Drive Medical records folder for requests grounded in the user's medical documents, including summaries, timelines, locating documented facts, comparing records, and creating source-grounded artifacts.
---

# Medical Records Knowledge

Use the connected Google Drive folder below as the canonical source:

- Folder: `ChatGPT Library/Medical records`
- Folder ID: `1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`
- URL: `https://drive.google.com/drive/folders/1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`

This folder is a canonical subtree of `SharedKnowledgeLibrary`.

Do not treat native ChatGPT Library `/Medical records` as authoritative. It is a legacy convenience copy from the retired synchronization job and may be stale.

For medical-record tasks:

1. Search or traverse the canonical Drive folder and descendants.
2. Retrieve the actual relevant documents before answering.
3. Treat records as evidence of what was documented at the time, not automatically as current state.
4. Identify conflicts or missing evidence rather than guessing.
5. Use precise source citations and page or section locators when available.
6. Keep unrelated sensitive information out of the response.
7. If the user asks to save or update a durable medical document, write directly into the canonical Drive subtree and verify the write.
8. Do not depend on a Drive-to-native-Library synchronization job.

A current-turn upload may be used immediately as the user's newly supplied source. Persist it into Drive only when the user or authorized workflow calls for durable storage.

If canonical Drive access is unavailable, state that limitation rather than presenting the legacy native Library mirror as current authoritative evidence.
