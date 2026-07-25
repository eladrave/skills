# Plivo Python SDK and WhatsApp Reference

Use this reference for copyable helper commands, direct SDK work, read-only WABA
template discovery, complex components, or error diagnosis. Prefer
`../scripts/plivo_whatsapp.py` for normal profile, send, and status operations.
The helper never creates, updates, deletes, or selects a persistent default
template. A synchronized catalog is derived cache data, and a no-WABA
definition exists only for its single confirmed send.

## Copyable helper workflows

Explain the isolated SDK destination and obtain explicit consent before
creating it or installing anything. Do not install globally or into the project
environment.

```bash
# Consent-gated isolated SDK installation
python3 -m venv ~/.local/share/plivo-whatsapp/venv
~/.local/share/plivo-whatsapp/venv/bin/python -m pip install \
  --disable-pip-version-check plivo
~/.local/share/plivo-whatsapp/venv/bin/python -c 'import plivo'

# Configure
python3 <skill-dir>/scripts/plivo_whatsapp.py configure

# WABA discovery
python3 <skill-dir>/scripts/plivo_whatsapp.py template sync --profile NAME
python3 <skill-dir>/scripts/plivo_whatsapp.py template search \
  --profile NAME --query task
python3 <skill-dir>/scripts/plivo_whatsapp.py template show \
  --profile NAME --name task_completes

# Offline parameter inference
python3 <skill-dir>/scripts/plivo_whatsapp.py template inspect-text \
  --text 'The task {{1}} was completed. Result: {{2}}.'

# Synchronized-template send
python3 <skill-dir>/scripts/plivo_whatsapp.py send-template \
  --profile NAME --to +15551234567 --template task_completes

# No-WABA ephemeral send
python3 <skill-dir>/scripts/plivo_whatsapp.py send-template \
  --profile NAME --to +15551234567 \
  --template task_completes --language en_US \
  --template-text 'The task {{1}} was completed. Result: {{2}}.'

# Freeform send
python3 <skill-dir>/scripts/plivo_whatsapp.py send-text \
  --profile NAME --to +15551234567 --text 'Hello from Plivo'

# Status
python3 <skill-dir>/scripts/plivo_whatsapp.py status \
  --profile NAME --message-uuid UUID --message-kind template
```

`configure` reads the Auth Token with hidden input and stores a redacted
profile. For a synchronized send, the helper accepts only the exact cached
template name and language when its provider status is `APPROVED`. For the
no-WABA path, `--language` and `--template-text` describe an existing approved
provider template only; the text is used for offline placeholder inference and
preview, never uploaded or saved.

The helper prompts for any omitted destination, definition, or inferred
parameter value. It previews the resolved destination, exact language,
approval source, and complete content; requires typed confirmation; sends once;
and reports every returned message UUID with its retrieved state. The
ephemeral confirmation also requires the user to attest that the exact
template name and language already exist and are approved by the provider.

## Authentication and private profiles

Never embed an Auth Token in code, command arguments, logs, or displayed
output. Direct SDK examples accept credentials from environment variables or
hidden input:

```python
import getpass
import os

import plivo

auth_id = os.environ.get("PLIVO_AUTH_ID") or input("Plivo Auth ID: ").strip()
auth_token = os.environ.get("PLIVO_AUTH_TOKEN") or getpass.getpass(
    "Plivo Auth Token: "
)
if not auth_id or not auth_token:
    raise SystemExit("Plivo credentials are required")

client = plivo.RestClient(auth_id, auth_token)
```

Reusable helper profiles live at
`~/.config/plivo-whatsapp/profiles.json`; its directory is mode `0700`, the
file is mode `0600`, and updates use atomic replacement. Helper output redacts
the token. Offline validation requires a 20-character Plivo Auth ID beginning
with `MA`; an optional WABA ID must be the numeric WhatsApp Business Account
ID shown by the provider.

## Complete freeform SDK example

Run this only while the destination has an eligible open WhatsApp customer
conversation window (normally 24 hours from the customer's most recent
message). Outside that window, use an approved template.

```python
import getpass
import os

import plivo

auth_id = os.environ.get("PLIVO_AUTH_ID") or input("Plivo Auth ID: ").strip()
auth_token = os.environ.get("PLIVO_AUTH_TOKEN") or getpass.getpass(
    "Plivo Auth Token: "
)
client = plivo.RestClient(auth_id, auth_token)

response = client.messages.create(
    src="+15551230001",
    dst="+15551234567",
    type_="whatsapp",
    text="Hello from Plivo",
)
print(response.message_uuid)
```

Preview the source, destination, and text and obtain explicit confirmation
before the single `messages.create` call.

## Complete template SDK example

The `language` value must be the exact provider language code for the existing
approved template. Preserve BCP-47 forms such as `en-US` and provider locale
forms such as `en_US`. Do not translate it, shorten it, infer it from
"English," or replace regional variants. The parameter count, order, names,
types, and formatting must exactly match the provider definition.

```python
import getpass
import os

import plivo
from plivo.utils.template import Template

auth_id = os.environ.get("PLIVO_AUTH_ID") or input("Plivo Auth ID: ").strip()
auth_token = os.environ.get("PLIVO_AUTH_TOKEN") or getpass.getpass(
    "Plivo Auth Token: "
)
client = plivo.RestClient(auth_id, auth_token)

template = Template(
    name="task_completes",
    language="en_US",
    components=[
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "Newsletter setup"},
                {"type": "text", "text": "Completed"},
            ],
        }
    ],
)
response = client.messages.create(
    src="+15551230001",
    dst="+15551234567",
    type_="whatsapp",
    template=template,
)
print(response.message_uuid)
```

Preview the destination, exact template name and language, approval basis, and
all resolved parameter values before the single send. When WABA discovery is
unavailable, independently verify that the exact name and language already
exist and are approved, then explicitly attest to that fact before sending.
This `Template` object is a message payload; it does not create or upload a
provider template.

Named parameters add `"parameter_name": "<exact-name>"` to each parameter.
Never mix named and positional body parameters. Positional definitions must be
contiguous from `{{1}}`, and every supplied value must be a non-empty string;
blank, whitespace-only, and non-string values are rejected before gateway
creation.

## Read-only WABA template discovery

WABA ID is optional for sending. It is required only for remote catalog reads:

```text
GET https://api.plivo.com/v1/Account/{auth_id}/WhatsApp/Template/{waba_id}/
GET https://api.plivo.com/v1/Account/{auth_id}/WhatsApp/Template/{waba_id}/{template_id}/
```

Use HTTP Basic authentication with Auth ID and Auth Token over HTTPS. The first
endpoint lists and paginates template summaries; the second retrieves each
complete template. Preserve the returned name, exact provider language code,
approval status, components, category, quality score, and parameter order.
Follow pagination only to trusted `https://api.plivo.com` URLs under the same
account/WABA path.

The helper's `template sync` performs only these read-only list/get operations
and replaces the normalized local synchronized cache. WABA reads use a bounded
10-second read timeout, reject redirect targets before resending Basic Auth,
detect pagination cycles, and stop after 100 pages or 1,000 template
summaries. `template search` searches cached names and text; `template show`
displays exact provider details and inferred body parameters.

Only synchronized templates with status `APPROVED` may send. Legacy local
manual definitions may remain readable for backward compatibility, but the
helper does not automatically select them and provides no way to change them.

## Ephemeral no-WABA inference

When a synchronized template is unavailable, supply the exact existing
template name, exact provider language, and complete approved body text.
`template inspect-text` performs the same placeholder extraction offline,
without profile changes, network access, or a send.

The helper accepts contiguous positional placeholders beginning with `{{1}}`
or named placeholders such as `{{customer_name}}`, never both. It rejects
gaps, duplicates, malformed markers, and empty values. The definition used by
`send-template --language en_US --template-text TEXT` is held only in memory
for that command and cannot be persisted to either the profile store or
synchronized cache.

Because the helper cannot query approval without WABA access, its preview
labels approval as user-attested rather than provider-verified. The exact
typed confirmation requires the user to attest that the template exists and
is approved before authorizing one send.

## Complex template components

The helper supports dynamic body-text parameters. Dynamic header media,
dynamic buttons, and carousel components require their complete
provider-defined inputs:

- header document, image, or video media and any dynamic header text;
- every dynamic button value, such as a URL suffix or quick-reply payload;
- every carousel card and all required card header, body, and button inputs.

The helper rejects these structures before sending. Do not discard an
unsupported component or construct a partial body-only message. Use the direct
SDK only after obtaining the exact approved template structure and every
dynamic value.

## Message states and verification

Plivo acceptance or HTTP `202` is not delivery. Read each returned message
UUID:

```python
for message_uuid in response.message_uuid:
    record = client.messages.get(message_uuid)
    print(message_uuid, record.message_state, record.error_code)
```

Treat states accurately:

| State | Meaning |
|---|---|
| `queued` | Accepted for processing; not delivered |
| `sent` | Sent onward; not proof of handset delivery |
| `delivered` | Delivered |
| `read` | Delivered and read |
| `failed` / `undelivered` | Not delivered; inspect the error |

If status retrieval fails, preserve every UUID and report the status failure.
Use `status --message-uuid UUID --message-kind freeform` or
`status --message-uuid UUID --message-kind template` for later checks so
error guidance retains the original send mode.

## Errors and no-retry rule

- **340, template:** confirm the synchronized template is `APPROVED` and its
  exact name and provider language code are used.
- **340, freeform:** confirm the destination has an eligible open WhatsApp
  customer conversation; otherwise use an approved template.
- **350, template:** verify every parameter's number, order, name, type, and
  formatting against the approved template.

Never automatically retry a send after a timeout, transport exception,
missing response, empty/blank/malformed UUID result, or other ambiguous
outcome: the first request may have succeeded. The helper exits nonzero and
preserves this no-auto-retry guidance. If a UUID is known, query it. If none is
available, reconcile the Plivo message record before asking for a separately
confirmed new send.
