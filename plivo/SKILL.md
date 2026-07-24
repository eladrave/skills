---
name: plivo
description: Use when the user asks to use or manage Plivo, find owned phone numbers, select or change a default sender, send SMS or MMS, or place text-to-speech or audio calls through a connected Plivo MCP server.
---

# Plivo

Operate Plivo only through the connected Plivo MCP. Treat live action schemas and dynamic values as authoritative.

## Discover capabilities

1. Confirm that Plivo MCP tools are connected and usable.
2. List enabled Plivo actions before every read or write.
3. Retrieve the exact action schema before execution. Resolve dependent fields and dynamic enums with required parent parameters, searching or paginating until complete.
4. Match actions by capability and schema. Never guess action keys, tool names, parameters, enum values, or response fields.
5. If Plivo actions are not enabled, use the MCP's action-discovery and enablement flow. Stop for connection or authentication when requested.

Never request credentials in chat, call Plivo REST directly, use browser automation, or substitute another provider.

## Select one persistent sender

Use one account-wide default Plivo number for SMS, MMS, and voice.

1. Retrieve the user's saved Plivo sender from connected persistent memory.
2. Enumerate every live sender-number choice exposed by Plivo actions. Inspect source/from dynamic enums across actions, follow pagination, and build a capability matrix. Use read-only number lookup for status or details when available.
3. If no default exists:
   - With one available number, save it as the default.
   - With multiple numbers, show every number and its SMS, MMS, and voice capabilities. Ask the user to choose before performing the requested write.
4. Save the selection as user-specific persistent memory, for example `Default Plivo sender: <E.164 number>`. Never store it in this skill or repository.
5. Before each write, verify that the saved number remains available and supports the requested action. Use it without asking again when valid.

Never create capability-specific defaults. Never switch numbers or use a temporary alternative. If the saved number is missing, inactive, or incompatible, explain why and ask the user to explicitly choose a new default. Replace persistent memory only after that selection.

When the user explicitly asks to change the sender, enumerate the choices again, ask them to select, save the replacement, and use it thereafter.

If persistent memory cannot be read or written, state that cross-conversation reuse is unavailable. Keep the selection only for the current conversation and do not claim it was saved.

## Execute an action

For number discovery and capability inspection, proceed without confirmation.

For SMS, MMS, or calls:

1. Resolve the exact destination and normalize it to E.164 when the country code is known.
2. Resolve the exact message, media URL, spoken text, or audio URL.
3. Treat an explicit request containing the destination and content as authorization for one execution. Ask one targeted question only when required data is missing or ambiguous.
4. For a potentially surprising multi-recipient action, state the resolved recipient count before execution.
5. Resolve the live write schema using the valid saved sender, then execute exactly once.

Never send to a guessed destination. Never automatically retry a timeout, malformed response, or uncertain write because it could duplicate a message or call.

## Report results

Report the action, sender, destination, and returned message or call identifier when available.

Use exact state language:

| Tool evidence | Report |
|---|---|
| Request accepted, no final status | Accepted by Plivo, delivery or completion unconfirmed |
| Delivered or completed state returned | Delivered or completed |
| Explicit failure returned | Failed, with a safe concise reason |
| Timeout or ambiguous result | Outcome uncertain, no automatic retry |

Never claim SMS or MMS delivery, audio playback, or call completion from acceptance alone. Do not expose credentials, internal connector identifiers, raw authentication errors, or unnecessary account metadata.

## Common mistakes

- Selecting the first of several numbers instead of asking.
- Saving separate SMS and voice defaults.
- Silently falling back when the saved sender cannot perform an action.
- Reusing cached schemas instead of live MCP schemas.
- Reporting `accepted=true` as delivered.
- Retrying an uncertain external action.
