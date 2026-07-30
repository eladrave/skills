# Medical Records Sync Scheduled Task

Schedule: Every day at 12:00 AM, `America/New_York`.

## Prompt

Synchronize the Google Drive folder "Medical records" at https://drive.google.com/drive/folders/1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3 into the ChatGPT Library folder `/Medical records`.

Treat Google Drive as the sole source of truth. Recursively enumerate every file and subfolder and mirror the complete relative folder hierarchy in Library. Create the Library root folder if it does not exist.

For stored, non-native Drive files, preserve the original filename and bytes. Export native Google Docs as PDF, Google Sheets as XLSX, and Google Slides as PDF, adding the corresponding extension. Comments, suggestions, permissions, and revision history are out of scope.

Maintain `_drive_sync_manifest.json` inside the Library folder. Record each source Drive file ID, source relative path, MIME type, modified time, available checksum or revision metadata, chosen export format, destination Library file ID, and Library version. Use stable Drive IDs to detect moves and renames. Preserve existing Library identity and version history when content changes by replacing the same Library file. Move or rename the existing Library item when the Drive item moves or is renamed.

For a new source file, prefer creating the Library file directly from a materialized workspace path. If Drive instead returns a secure connector `file_uri` without a workspace path, create a temporary placeholder Library identity in the correct destination folder, immediately replace it through the Library update operation using the Drive `file_uri`, correct target filename, MIME type, and expected current version, then verify the final byte size and MIME type. Count the item as created only after that replacement verifies. If replacement fails, move the placeholder to Library trash, record a failure, and suppress all deletion reconciliation for that run. Never leave placeholder content as the current version.

Apply changes in this safe order: create folders; create, replace, move, and rename files; verify every successful transfer and mutation; update the manifest; only then move Library files and folders absent from Drive to Library trash. Any non-manifest item added manually under `/Medical records` but absent from Drive must be removed because the Drive tree is authoritative.

Fail closed. If Drive access fails, recursive enumeration may be incomplete, any folder listing is truncated or ambiguous, duplicate source paths cannot be safely resolved, any required source export or download fails, any upload or replacement cannot be verified, or any mutation has an unresolved failure, do not perform deletions during that run. Never modify or delete anything in Google Drive. Never permanently delete Library data. Do not mutate protected Library artifacts.

Report a concise sync summary in ChatGPT with counts for discovered, created, updated, moved or renamed, deleted to trash, unchanged, skipped, conflicts, and failures. Explicitly state whether deletion was enabled or suppressed and why.
