# WhatsApp monitor tool contract

Read this reference when composing rules, handling errors, or troubleshooting the focused OpenWA MCP
surface. Server-advertised live schemas remain authoritative if this reference and the connected tool
metadata differ.

## Tool sequence

### Enrollment

1. `WhatsAppAuthListSessions`
2. `WhatsAppAuthGetStatus(sessionId, flowId?)`
3. `WhatsAppAuthBegin(sessionId, mode)`
4. `WhatsAppAuthGetChallenge(sessionId, flowId, phoneNumber?)`
5. `WhatsAppAuthCancel(sessionId, flowId)` when requested or abandoning an active flow
6. `WhatsAppAuthDisconnect(sessionId, confirm=true)` only after explicit confirmation

Finite states: `unconfigured`, `starting`, `challenge_ready`, `waiting_for_scan`, `connecting`,
`authenticated`, `expired`, `cancelled`, `logged_out`, `error`.

### Groups and rules

- `MonitorListAvailableGroups(sessionId, limit?, offset?)`
- `MonitorListGroups(sessionId)`
- `MonitorSetGroup(sessionId, groupJid, expectedName?)`
- `MonitorRemoveGroup(sessionId, groupJid)`
- `MonitorListRules(sessionId, groupJid?)`
- `MonitorGetRule(sessionId, ruleId)`
- `MonitorPreviewRule(sessionId, groupJid, ruleId|config, limit?)`
- `MonitorUpsertRule(sessionId, groupJid, config, ruleId?, expectedVersion?)`
- `MonitorSetRuleEnabled(sessionId, ruleId, enabled, expectedVersion)`
- `MonitorDeleteRule(sessionId, ruleId)`

Supply `ruleId` and `expectedVersion` together for updates. Preview accepts exactly one of a saved
`ruleId` or unsaved `config`.

### Matches and cursors

- `MonitorGetMatches(sessionId, state?, limit?, offset?)`
- `MonitorGetMatch(sessionId, matchId)`
- `MonitorGetDigestBatch(sessionId, cursor?, limit?)`
- `MonitorAcknowledgeMatches(sessionId, cursor, cursorVersion, batchToken, matchIds)`
- `MonitorGetHealth(sessionId)`

Digest reads are bounded and non-blocking. Preserve match-ID order during acknowledgment.

## Rule shape

```json
{
  "name": "Human label",
  "enabled": true,
  "matchMode": "all",
  "conditions": [],
  "exclusions": [],
  "priority": "normal",
  "tags": [],
  "timezone": "UTC",
  "activeHours": {
    "start": "09:00",
    "end": "18:00",
    "daysOfWeek": [1, 2, 3, 4, 5]
  },
  "quietHours": { "start": "22:00", "end": "07:00" },
  "retentionDays": 7
}
```

`matchMode` applies to positive conditions. Exclusions run afterward. Critical priority can override
quiet hours; other priorities do not.

## Conditions

```json
{ "type": "mentioned_owner" }
{ "type": "mentioned_jid", "jids": ["15551234567@c.us"] }
{ "type": "keyword", "values": ["outage"], "caseSensitive": false, "wholeWord": true }
{ "type": "phrase", "value": "need approval", "caseSensitive": false, "normalizeWhitespace": true }
{ "type": "regex", "pattern": "\\bINC-[0-9]{4,8}\\b", "flags": "i" }
{ "type": "sender", "jids": ["15551234567@c.us"], "mode": "allow" }
{ "type": "message_type", "types": ["text", "document"] }
{ "type": "has_media", "value": true }
{ "type": "is_reply", "value": true }
{ "type": "time_window", "start": "09:00", "end": "18:00", "daysOfWeek": [1, 2, 3, 4, 5] }
{ "type": "semantic_topic", "description": "production reliability incident", "threshold": 0.8 }
{ "type": "urgency", "minimumLevel": "high", "semantic": true }
```

Days use `0=Sunday` through `6=Saturday`. Times use `HH:mm` in the rule's IANA timezone. Regexes are
length-limited, syntax-validated, and rejected when unsafe. Do not work around a rejection by making a
more complex regex; use keywords, phrases, senders, or types instead.

Message types: `text`, `image`, `video`, `audio`, `voice`, `document`, `sticker`, `location`,
`contact`, `poll`, `call`, `revoked`, `masked`, `unknown`.

Priority: `low`, `normal`, `high`, `critical`. Urgency: `none`, `low`, `medium`, `high`, `critical`.

## Stable error handling

- `AUTH_REQUIRED`: use an explicitly session-scoped monitoring credential; do not broaden access.
- `SESSION_NOT_READY`: reconnect or finish enrollment.
- `GROUP_NOT_FOUND`: refresh the available-group list.
- `GROUP_RENAMED`: show the current name and reconfirm.
- `GROUP_NOT_MONITORED`: select the exact group before creating rules.
- `RULE_NOT_FOUND`: refresh rules without revealing cross-session existence.
- `RULE_INVALID`: correct the schema or reload after a version conflict.
- `RULE_LIMIT`: tighten/consolidate rules; do not bypass limits.
- `CURSOR_NOT_FOUND` / `CURSOR_CONFLICT`: fetch a fresh digest batch.
- `FLOW_NOT_FOUND` / `FLOW_EXPIRED` / `FLOW_CONFLICT`: inspect status; create only one new flow when
  the old one is terminal.
- `CHALLENGE_NOT_READY`: poll status with bounded cadence.
- `PAIRING_UNSUPPORTED`: offer QR.
- `SEMANTIC_UNAVAILABLE`: return deterministic results with a visible degraded-state note.

Do not expose raw server errors, stack traces, identifiers outside the granted session, or secret
values while explaining an error.
