# Landing Page Implementation Contract

Use this reference when defining the form registry, D1 schema, submission route, webhook service,
admin APIs, CSV export, and tests. Adapt names to the project, but preserve the security and durability
properties.

## Contents

1. Canonical form registry
2. D1 schema
3. Submission request and response
4. Submission transaction order
5. Webhook configuration and payload
6. Admin authorization and APIs
7. CSV export
8. Status model
9. Testing fixtures

## 1. Canonical form registry

Define forms in server-owned code. The browser submits `form_id` and `form_name`, but the registry is
authoritative.

```ts
type FieldDefinition = {
  key: string;
  label: string;
  type: "text" | "email" | "tel" | "textarea" | "select" | "checkbox";
  required: boolean;
  maxLength?: number;
  allowedValues?: readonly string[];
};

type FormDefinition = {
  id: string;
  name: string;
  fields: readonly FieldDefinition[];
  primaryNameField?: string;
  primaryEmailField?: string;
};

export const FORMS: Record<string, FormDefinition> = {
  "contact-main": {
    id: "contact-main",
    name: "Main contact form",
    primaryNameField: "name",
    primaryEmailField: "email",
    fields: [
      { key: "name", label: "Name", type: "text", required: true, maxLength: 120 },
      { key: "email", label: "Email", type: "email", required: true, maxLength: 254 },
      { key: "company", label: "Company", type: "text", required: false, maxLength: 160 },
      { key: "message", label: "Message", type: "textarea", required: true, maxLength: 4000 },
    ],
  },
};
```

Render both hidden fields in every form:

```tsx
<input type="hidden" name="form_id" value={definition.id} />
<input type="hidden" name="form_name" value={definition.name} />
```

Server policy:

1. Look up the submitted `form_id` in `FORMS`.
2. Reject an unknown ID.
3. Require submitted `form_name` to equal `FORMS[form_id].name`, or replace it with the canonical name
   and record a validation warning. Prefer rejection when diagnosing integration mistakes matters.
4. Accept only declared field keys plus explicitly allowed operational keys such as a honeypot.
5. Persist and forward only canonical identity values.

## 2. D1 schema

Use a generic payload column so one admin dashboard can support several forms. Keep common search fields
normalized. Add form-specific normalized columns only when filtering or reporting requires them.

```ts
import { sql } from "drizzle-orm";
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const formSubmissions = sqliteTable("form_submissions", {
  id: text("id").primaryKey(),
  formId: text("form_id").notNull(),
  formName: text("form_name").notNull(),
  payloadJson: text("payload_json").notNull(),
  displayName: text("display_name"),
  email: text("email"),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  webhookStatus: text("webhook_status").notNull().default("pending"),
  webhookAttemptedAt: text("webhook_attempted_at"),
  webhookResponseCode: integer("webhook_response_code"),
  webhookError: text("webhook_error"),
});

export const webhookConfig = sqliteTable("webhook_config", {
  id: integer("id").primaryKey(),
  enabled: integer("enabled", { mode: "boolean" }).notNull().default(false),
  url: text("url"),
  bearerToken: text("bearer_token"),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedBy: text("updated_by"),
});
```

Recommended indexes:

```sql
CREATE INDEX form_submissions_created_at_idx
ON form_submissions(created_at DESC);

CREATE INDEX form_submissions_form_id_created_at_idx
ON form_submissions(form_id, created_at DESC);

CREATE INDEX form_submissions_webhook_status_idx
ON form_submissions(webhook_status);
```

Use one `webhook_config` row with `id = 1` when all forms share an endpoint. If forms require different
destinations, use a composite or per-form primary key and require an explicit user decision. Never let
the submitted browser payload select an arbitrary endpoint.

JSON payload rules:

- Store a JSON object containing only validated visible fields.
- Do not duplicate `form_id`, `form_name`, bearer tokens, admin emails, or internal errors inside
  `payload_json`.
- Preserve checkbox booleans and declared numeric values as their logical JSON types.
- Avoid storing empty optional values unless downstream consumers need the distinction.
- Cap the serialized payload size.

## 3. Submission request and response

Example browser request:

```json
{
  "form_id": "contact-main",
  "form_name": "Main contact form",
  "fields": {
    "name": "Taylor Example",
    "email": "taylor@example.com",
    "company": "Example Co",
    "message": "I would like to discuss a project."
  },
  "website": ""
}
```

`website` is an example honeypot, not a stored form field.

Successful visitor response:

```json
{
  "saved": true,
  "submission_id": "<uuid>"
}
```

Return HTTP 201 only after D1 confirms the insert. Do not include webhook configuration or detailed
delivery errors in the visitor response. Webhook delivery failure after a successful insert should
still return the durable-write success response.

Validation response:

```json
{
  "saved": false,
  "error": "Please enter a valid email address.",
  "field": "email"
}
```

Use safe user-facing messages. Log only bounded operational context and never log the full payload or
secret values by default.

## 4. Submission transaction order

Preserve this order:

```text
validate request
  -> create canonical record
  -> insert into D1
  -> attempt webhook
  -> update delivery metadata
  -> return durable success
```

If the D1 insert fails, return an error and do not call the webhook.

If webhook delivery or the delivery-metadata update fails:

- Keep the submission row.
- Record `failed` when possible.
- Return success for the durable submission.
- Surface the failure in `/admin`.
- Allow an authorized retry using the same submission UUID and form identity.

If the webhook was delivered but the status update failed, avoid an automatic blind retry. An admin
may retry with the same idempotency key after assessing the endpoint's behavior.

## 5. Webhook configuration and payload

Admin-editable configuration belongs in D1 and is never returned with the bearer token. A blank token
field means "preserve existing token." Use a separate `clearToken` boolean to remove it.

Validate configuration:

- Require HTTPS.
- Reject credentials embedded in the URL when a bearer token or another header can be used instead.
- Require a URL before enabling.
- Cap URL and token lengths.
- Record updated timestamp and authenticated administrator.

Example event:

```json
{
  "event": "form.submitted",
  "source": "landing-page",
  "sent_at": "2026-08-25T17:00:00.000Z",
  "submission": {
    "id": "e6c4fc41-6eb0-4a73-b087-b729b3b076f7",
    "form_id": "contact-main",
    "form_name": "Main contact form",
    "created_at": "2026-08-25T16:59:58.000Z",
    "fields": {
      "name": "Taylor Example",
      "email": "taylor@example.com",
      "company": "Example Co",
      "message": "I would like to discuss a project."
    }
  }
}
```

Recommended request headers:

```text
Content-Type: application/json
User-Agent: landing-page-webhook/1.0
X-Webhook-Event: form.submitted
Idempotency-Key: <submission UUID>
Authorization: Bearer <configured token>   # only when configured
```

Test event rules:

- Use `form.test` or `<form_id>.test` as the event.
- Use a generated test ID that is visibly non-production.
- Include `form_id` and `form_name`.
- Do not insert the test into `form_submissions`.
- Return the HTTP status or a bounded sanitized error to the authorized admin UI.

## 6. Admin authorization and APIs

Use the starter's Sign in with ChatGPT helpers. Protect `/admin` with `requireChatGPTUser("/admin")`,
then enforce a server-side allowlist from `ADMIN_EMAILS`.

```ts
const allowed = new Set(
  env.ADMIN_EMAILS.split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean),
);

if (!user || !allowed.has(user.email.toLowerCase())) {
  return Response.json({ error: "Unauthorized" }, { status: 401 });
}
```

Do this separately inside every API handler. Client-side gating is never authorization.

Suggested routes:

| Route | Method | Purpose |
| --- | --- | --- |
| `/admin` | GET | Protected dashboard |
| `/api/admin/submissions` | GET | Paginated list and filters |
| `/api/admin/submissions/export` | GET | Full authorized CSV export |
| `/api/admin/submissions/:id/retry` | POST | Retry one stored submission |
| `/api/admin/webhook-config` | GET | Return URL, enabled state, and `tokenConfigured` only |
| `/api/admin/webhook-config` | PUT | Save enable state, URL, token replacement, or explicit clear |
| `/api/admin/webhook-test` | POST | Send a non-persisted test event |

Add pagination when rows can exceed the dashboard's bounded initial list. Use opaque cursors or stable
`created_at` plus `id` ordering. Do not load an unbounded table into a client component.

Return `Cache-Control: no-store` on authenticated pages, JSON APIs, and exports. Set admin metadata to
`robots: { index: false, follow: false }`.

## 7. CSV export

Include at least:

```text
id,form_id,form_name,created_at,display_name,email,payload_json,
webhook_status,webhook_attempted_at,webhook_response_code,webhook_error
```

For a more user-friendly export, expand known form fields into stable columns. Always retain
`form_id` and `form_name`.

CSV safety:

- Quote every cell.
- Double embedded quotes.
- Preserve embedded newlines inside quoted cells.
- Prevent spreadsheet formula execution by prefixing cells beginning with `=`, `+`, `-`, or `@`
  when the export may be opened in spreadsheet software.
- Use UTF-8 and a deterministic filename with the date.

## 8. Status model

Use a bounded status vocabulary:

| Status | Meaning |
| --- | --- |
| `pending` | D1 insert succeeded, delivery state not finalized |
| `delivered` | Endpoint returned HTTP 2xx |
| `failed` | Attempt failed or returned non-2xx |
| `disabled` | Webhook exists but delivery was disabled |
| `not_configured` | No endpoint was saved |

Never represent `disabled` or `not_configured` as `delivered`. Show all five states distinctly in the
admin UI and CSV export.

## 9. Testing fixtures

Create at least two form definitions when testing multiple-form behavior:

```text
form_id: contact-main
form_name: Main contact form

form_id: demo-request
form_name: Demo request form
```

Test that a `demo-request` payload cannot claim `Main contact form`, and that an unknown form cannot
select a webhook destination. Include field content containing commas, quotes, newlines, HTML tags,
Unicode, and spreadsheet-formula prefixes to validate safe rendering and CSV export.
