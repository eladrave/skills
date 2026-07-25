---
name: plivo-whatsapp
description: Use when configuring Plivo WhatsApp access, sending or checking WhatsApp messages through Plivo, working with WhatsApp templates, synchronizing or searching a Plivo WABA template catalog, or troubleshooting Plivo WhatsApp delivery and template errors.
---

# Plivo WhatsApp

## Overview

Use the bundled helper for secure profiles, read-only template discovery,
guarded sends, and delivery checks:

```bash
python3 <skill-dir>/scripts/plivo_whatsapp.py <command>
```

Never place an Auth Token in arguments, displayed output, logs, or errors.
Templates are never created, updated, removed, or assigned a persistent
default. Synchronization refreshes only a local cache derived from existing
provider templates.

## Required Workflow

In every response, explicitly cover all eight steps below, including exact
paths and permissions, even when the request focuses on only one message mode.

1. Run `show-config --profile NAME` to validate configuration formats offline,
   without network access or a live send. If the profile does not exist, run
   `configure`; it reads the token with hidden input and stores only redacted
   output. Profiles and synchronized template data are schema-checked before
   display or gateway creation. The private store is
   `~/.config/plivo-whatsapp/profiles.json` (directory `0700`, file `0600`,
   atomic replacement).
2. A gateway command checks for the official `plivo` SDK. If absent, explain
   that it will create `~/.local/share/plivo-whatsapp/venv`, obtain explicit
   consent, and only then run that environment's
   `python -m pip install --disable-pip-version-check plivo`. Declining must
   stop the operation.
3. Choose one mode:
   - **Freeform:** only for an eligible open WhatsApp customer conversation
     window.
   - **Template:** use an approved template outside that window or whenever
     template content is requested.
4. Treat WABA ID as optional. With one, use read-only `template sync`,
   `template search`, and `template show`; only an exact synchronized
   `APPROVED` name and provider language may send. Without a synchronized
   match, collect the exact existing template name, provider language, and
   complete approved text for an ephemeral send. Infer placeholders with
   `template inspect-text`; never guess the language or persist the supplied
   definition.
5. For a template send, collect a non-empty value for every inferred body
   parameter. Positional keys must be contiguous from `1`; named and
   positional keys cannot be mixed. Dynamic header media, buttons, and
   carousel components need their complete inputs, so this body-only helper
   rejects them instead of partially sending.
6. Show the helper's destination and complete content/template preview. For an
   ephemeral template, the user must attest that the exact named template
   already exists and is provider-approved. Obtain the helper's typed `yes`
   confirmation for exactly one send.
7. Invoke one `send-text` or `send-template` command. Never automatically
   retry a timeout, transport failure, missing/blank/malformed UUID response,
   or other ambiguous send result. Reconcile the Plivo message record first.
8. Read every returned message UUID and the immediately retrieved state.
   Report `queued` as queued, never as delivered. Only `delivered` or `read`
   proves delivery/read. Use
   `status --message-uuid UUID --message-kind freeform|template` for a later
   check, selecting the original send mode.

## Template Discovery Quick Start

```bash
python3 <skill-dir>/scripts/plivo_whatsapp.py template sync --profile NAME
python3 <skill-dir>/scripts/plivo_whatsapp.py template search \
  --profile NAME --query task
python3 <skill-dir>/scripts/plivo_whatsapp.py template show \
  --profile NAME --name task_completes
python3 <skill-dir>/scripts/plivo_whatsapp.py template inspect-text \
  --text 'The task {{1}} was completed. Result: {{2}}.'
```

Use the
[copyable helper workflows](references/plivo-python.md#copyable-helper-workflows)
for synchronized, ephemeral, freeform, status, and isolated SDK setup commands.
For direct SDK usage, see the
[complete freeform SDK example](references/plivo-python.md#complete-freeform-sdk-example)
and
[complete template SDK example](references/plivo-python.md#complete-template-sdk-example).

## Command Reference

`--profile NAME` selects a profile; `--config PATH` is an advanced store
override. Omitted send content and destinations are prompted.

| Command | Purpose |
|---|---|
| `configure [--config PATH]` | Create or update a profile with hidden token input |
| `show-config [--profile NAME]` | Show a redacted profile |
| `delete-profile [--profile NAME]` | Delete a profile after typed confirmation |
| `template sync [--profile NAME]` | Refresh the read-only WABA-derived cache |
| `template list [--profile NAME]` | List cached synchronized templates |
| `template search [--profile NAME] --query QUERY` | Search cached names and text |
| `template show [--profile NAME] --name NAME` | Show exact provider details and inferred parameters |
| `template inspect-text --text TEXT` | Infer placeholders offline without persistence |
| `send-text [--to E164] [--text TEXT]` | Preview, confirm, send once, and check UUID state |
| `send-template [--to E164] [--template N] [--language L] [--template-text TEXT]` | Use an approved synchronized or ephemeral template |
| `status --message-uuid UUID --message-kind freeform\|template` | Read state with mode-specific error guidance |

Run any command with `--help` for its complete options. See
[references/plivo-python.md](references/plivo-python.md) for complete examples,
raw read-only API details, complex components, and error diagnosis.
