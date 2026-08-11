---
name: tailscale-management
description: Manage the user's Tailscale tailnet through the Tailscale Management API. Use whenever the user asks to inspect, configure, troubleshoot, or change Tailscale devices, routes, exit nodes, DNS, policy files or ACLs, users, invites, keys, credentials, posture attributes or integrations, logs, webhooks, services, OAuth apps, tailnet settings, or other resources in tailnet Tgt5F5Pb5V91CNTRL.
---

# Tailscale Management

Manage the user's Tailscale resources through the current Management API while
protecting credentials, preserving unrelated state, and verifying every change.

## Authoritative context

1. Invoke the global `codex-drive-as-knowledge` skill before making any API call.
   Use the connected Google Drive connector to retrieve `TailScale.md` from the
   predefined `Codex` knowledge folder.
2. Pin retrieval to these stable Drive identifiers:
   - Codex folder ID: `18Woem9j4Tk-_FglrM6ZTGaNPZArUdJU0`
   - TailScale.md file ID: `13ah0WM0nlQfkKbKeGyXsdD6CrqNzi-_Q`
3. Verify from file metadata that `TailScale.md` is a child of the pinned Codex
   folder before trusting its contents. The file is the source of truth for the
   tailnet ID, credential, expiry, tested access method, endpoint map, and
   operating rules.
4. Retrieve only this relevant file. Do not load unrelated credentials or private
   documents from the Codex folder.
5. Treat the credential in that file as secret. Never reproduce it in chat,
   command output, logs, generated files, commits, process listings, or URLs.
6. Do not use a local mirror, model memory, or an unverified Drive search result
   as the credential source. If the Drive connector or pinned file is unavailable,
   stop and report that the authoritative Tailscale runbook cannot be accessed.
7. Use <https://tailscale.com/api-docs> for the current endpoint, method, request
   body, response schema, and release-stage status. Do not rely on remembered or
   stale payload shapes.
8. Use direct HTTPS requests to the Management API as the canonical interface.
   The community `tailscale` Python package is optional and covers only a subset
   of the API.

## Target boundary

- Default and authorized tailnet: `Tgt5F5Pb5V91CNTRL`.
- Keep all operations limited to this tailnet unless the user explicitly names
  another tailnet and provides or authorizes suitable credentials.
- Use the literal tailnet ID in requests instead of the `-` shorthand so the
  target remains explicit.
- Do not alter local Tailscale client state with `tailscale up`, `tailscale down`,
  or similar commands when the request concerns Management API state.

## Workflow

### 1. Understand the requested outcome

Identify the exact resource, current state needed, desired state, and expected
blast radius. Resolve ambiguous device, user, route, tag, service, or policy
identifiers with read-only API calls before changing anything.

### 2. Load and validate access

Retrieve the token from the pinned Drive file without displaying it. Keep it only
for the duration of the authorized operation. Do not persist it locally, use shell
tracing, enable verbose HTTP output, or run commands that print the environment.

If the available tools cannot transfer the credential from Drive to the API call
without exposing it in user-visible output, stop and report the secure-handling
limitation. Never ask the user to paste the token into chat as a workaround.

Run the guide's read-only preflight against the explicit tailnet. A successful
device-list response proves read access only; it does not prove permission for a
later write. If the token is expired, revoked, or rejected, stop and report the
sanitized HTTP status without repeatedly retrying.

The recorded token expires on `2026-11-09`. On or after that date, require a
replacement token and update the operator guide before attempting management
work.

### 3. Inspect current state

Read the affected resource before mutation. Retain only the fields needed to make
the decision and avoid exposing complete inventories, policies, logs, users, or
credential metadata unless the user requested them.

For a policy-file change, fetch the current policy and its `ETag`, validate the
candidate policy, and update it with `If-Match`. Never overwrite a concurrent
change blindly.

### 4. Confirm the API contract

Check the current official documentation immediately before every write. Confirm:

- HTTP method and path
- path and query identifiers
- content type and request schema
- required permission or OAuth scope
- response and error semantics
- Alpha, Beta, or other release-stage warnings

Construct JSON with a structured serializer such as `jq`; do not assemble JSON by
concatenating untrusted strings.

### 5. Execute the smallest change

Change only the fields and resources required for the user's outcome. Preserve
unrelated devices, tags, routes, settings, policy rules, and credentials.

Before an ambiguous or destructive action, state the concrete target and effect
and obtain immediate confirmation. This includes deleting devices, users, keys,
services, OAuth apps, or tailnets; expiring device keys; suspending users;
replacing policy rules; changing routes, exit-node approval, or DNS; and rotating
secrets. A clear user instruction naming the exact target and action is sufficient
authorization unless the observed state reveals a materially larger effect.

### 6. Verify the result

Re-read the affected resource and compare its relevant fields with the requested
state. Do not report success from an HTTP status alone when the resulting state is
queryable.

If a write times out or returns an ambiguous server error, inspect current state
before retrying so the operation is not duplicated. Use bounded backoff for safe
read retries and honor `Retry-After` for rate limits.

### 7. Report safely

Report the operation, sanitized target identifier, resulting state, and
verification evidence. Mention any unverified permission, partial result,
release-stage risk, or required follow-up. Never include the access token,
authorization header, webhook secret, private policy content, or unnecessary
tailnet inventory.

Unset credential variables after the operation.

## Python client boundary

Use `frenck/python-tailscale` only when its public API directly supports the
requested operation. It is asynchronous, community-maintained, and not an
official Tailscale SDK. Confirm the installed version before use and pass the
credential from the environment into the constructor.

Prefer direct REST calls for policy files, posture data and integrations, user
mutations, invites, webhooks, logs and log streaming, contacts, services, OAuth
apps, and any endpoint without a documented public client method. Do not call the
package's private `_request()` method as if it were a stable interface.

## Failure rules

- `401`: treat the token as invalid, revoked, or expired; stop without exposing it.
- `403`: report that the credential lacks the required permission; do not seek a
  broader credential unless the requested operation requires it.
- `404`: verify the explicit tailnet and resource identifiers before concluding
  that the resource does not exist.
- `409` or `412`: re-read state and reconcile the conflict; never force overwrite.
- `429`: honor `Retry-After` and apply bounded backoff.
- `5xx` or timeout: retry reads cautiously; verify write side effects before any
  retry.

Never weaken credential handling, bypass concurrency controls, or broaden the
requested operation merely to make an API call succeed.
