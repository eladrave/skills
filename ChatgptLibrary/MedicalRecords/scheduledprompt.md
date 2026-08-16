# DEPRECATED: Medical Records Drive-to-Library Sync

Do not create or re-enable this legacy synchronization task.

The canonical medical source is now Google Drive:

`ChatGPT Library/Medical records`

Folder ID:

`1MppW8kw3fUFFa2d2IwtkJBGNn1W8KnM3`

ChatGPT and other authorized agents should read that Drive folder directly.

The previous task that mirrored Drive into native ChatGPT Library `/Medical records` is no longer required. Native ChatGPT Library is not the canonical medical source.

New native-Library-only files may be caught by the unified `SharedKnowledgeLibrary` ingress task and persisted into canonical Drive when appropriate.

For rollback history, the previous scheduled task may remain disabled in ChatGPT, but it should not run during normal operation.
