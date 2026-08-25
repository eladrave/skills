---
name: landing-page-creator
description: Create, refine, validate, and publish complete landing pages with ChatGPT Sites, including persuasive content, responsive visual design, one or more forms, durable D1 submission storage, protected admin dashboards, CSV export, configurable webhooks, webhook testing and retry, authentication, accessibility, privacy, and deployment. Use when a user asks for a landing page, lead-capture page, campaign page, waitlist, contact page, demo-request page, event-registration page, or another public page that collects form submissions and needs an administrative interface.
---

# Landing Page Creator

Create a production-ready landing page, not a static mockup. Use ChatGPT Sites for hosting, D1 for
durable structured data, and Sign in with ChatGPT plus a server-side allowlist for the admin surface.

Load and follow `sites:sites-building` before creating or editing any Site. Its lifecycle, source,
validation, deployment, access, image-generation, checkpoint, and approval rules remain authoritative.
Use `sites:sites-hosting` only for the hosting operations that skill assigns to it.

Read [references/implementation-contract.md](references/implementation-contract.md) before defining
the D1 schema, submission endpoint, admin API, or webhook payload.

## Non-negotiable form identity contract

Every user-submittable form MUST include and submit both fields below:

```html
<input type="hidden" name="form_id" value="contact-main" />
<input type="hidden" name="form_name" value="Main contact form" />
```

Apply all of these rules:

- Give every form a stable, unique `form_id` in lowercase kebab-case.
- Give every form a concise human-readable `form_name`.
- Keep both inputs hidden from the rendered interface, but include them in the browser submission.
- Include both values in the server request, D1 row, admin list/detail view, CSV export, webhook event,
  logs, tests, and retry operations.
- Define the canonical `form_id` to `form_name` mapping in server-owned code.
- Reject unknown `form_id` values. Reject a missing or mismatched `form_name`, or replace it with the
  canonical server value while recording the mismatch. Never trust the browser to select a webhook,
  table, administrator, or authorization rule.
- For multiple forms, keep one canonical definition per form and allow admin filtering by form.
- Do not use a random value as `form_id`. It identifies the form definition, not one submission.
- Give each submission its own separate UUID.

Do not consider the Site complete until automated or inspected evidence confirms that both hidden
fields are emitted and persist through the complete submission pipeline.

## 1. Discover the page before building

Ask a concise discovery group before creating the Site. Use `sites:answers-ask-user-input` when
available. Do not ask questions already answered in the request or a supplied reference. Limit each
round to one to three focused questions, then ask a second round only if a material decision remains.

### Required discovery topics

Ask for these topics, grouping related details naturally:

1. **Purpose and content**
   - What is being offered, announced, sold, or collected?
   - Who is the intended visitor?
   - What single action should the visitor take?
   - What page sections, claims, proof, testimonials, customer logos, pricing, FAQs, contact details,
     legal links, and calls to action should appear?
   - Should the agent write draft copy from the user's facts, preserve supplied copy exactly, or both?

2. **Brand and visual direction**
   - Ask for preferred colors, typography, mood, logo, icons, photos, illustrations, and existing
     brand assets.
   - Alternatively, ask for a public website whose visual system should inform the page.
   - When a reference website is supplied, inspect its current public pages. Extract practical cues
     such as palette, type scale, spacing, shapes, image treatment, and tone.
   - Ask whether the user owns the reference site or has permission to reuse its images and logos.
     If not, use it only as inspiration. Retrieve licensed or user-provided assets, or generate new
     original imagery when useful.
   - Never copy protected text, branding, or imagery merely because it is publicly visible.

3. **Forms and operations**
   - Ask which forms are needed and which fields each form should contain.
   - Ask which fields are required, optional, conditional, or consent-related.
   - Ask for the administrator email address or addresses allowed to open `/admin`.
   - Ask whether a webhook already exists. If it does, collect the HTTPS endpoint and authentication
     expectation through an approved secret-handling path. If it does not, build the admin
     configuration page so the user can add it later.
   - Ask whether the final Site should remain owner-only, be shared with selected users, be workspace
     accessible, or become public. Treat public deployment approval according to the Sites workflow.

### Suggest form fields instead of making the user design the schema alone

Recommend the smallest field set that supports the stated decision or follow-up. Explain why any
high-friction field is necessary.

- General contact: name, email, company optional, phone optional, message.
- Demo request: name, work email, company, role optional, use case, team size optional.
- Waitlist: email, name optional, role or intended use optional.
- Newsletter: email and any legally required consent. Avoid extra qualification fields.
- Lead qualification: name, email, company, role, use case, timeline optional, budget only if it will
  actually change routing.
- Event registration: name, email, organization optional, attendance choice, accessibility or dietary
  needs only when operationally necessary and handled appropriately.

Always add hidden `form_id` and `form_name`, even when the visible form has only one field.

Avoid collecting health information, payment-card data, government identifiers, passwords, or other
sensitive data in Sites. If the requested workflow needs sensitive or regulated data, stop and explain
that a different architecture and compliance review are required.

## 2. Define the experience

Turn the discovery answers into a compact internal specification before source changes:

- Page title, metadata description, canonical primary CTA, audience, and success event.
- Ordered sections and final copy ownership, user-supplied, drafted, or placeholder requiring review.
- Design tokens: background, text, accent, muted colors, fonts, spacing, borders, radius, icon style,
  imagery, and motion.
- Responsive behavior for desktop, tablet, and mobile.
- Form definitions with canonical IDs, names, field types, validation, autocomplete values, required
  flags, maximum lengths, consent language, and success/error messages.
- D1 persistence, admin allowlist, webhook policy, access mode, analytics, and custom-domain needs.

Prefer one clear conversion path. Do not add generic marketing sections, dashboards, authentication,
or fields that do not serve the user's goal. The admin surface is the exception because this skill's
contract requires operational access to submissions and webhook settings.

## 3. Create the public landing experience

Follow the Sites lifecycle exactly. For a new Site, create it once with the recommended Vinext starter.
For an existing Site, edit the existing project and preserve its architecture, package manager,
bindings, metadata, and access policy.

Build a coherent, recognizable design rather than a generic template:

- Put the value proposition and primary CTA in the first viewport.
- Use concrete copy tied to the user's product and audience.
- Make the form easy to reach without obscuring the narrative.
- Include loading, validation, error, submission-in-progress, and success states.
- Preserve entered values after recoverable validation or network failures.
- Use explicit labels, useful help text, accessible error associations, logical tab order, visible
  focus, adequate contrast, touch-friendly targets, and reduced-motion support.
- Set appropriate `autocomplete`, input modes, keyboard types, minimum and maximum lengths, and
  semantic field types.
- Do not rely on placeholder text as the only label.
- Do not expose internal record IDs, webhook configuration, bearer tokens, admin addresses, or error
  stack traces on the public page.
- Add a concise privacy statement near the form and link to a fuller privacy page when required.
- Include a meaningful favicon, title, description, Open Graph metadata, and social card according to
  the Sites skill.
- Keep public pages indexable unless the user requests otherwise. Keep admin pages `noindex`.

### Form submission behavior

Use a server route for each form or a shared route with a strict canonical form registry. Never write
directly to D1 or call the webhook from browser code.

For every submission:

1. Parse a bounded JSON or form-encoded body.
2. Confirm same-origin browser requests when practical.
3. Validate `form_id` and `form_name` against the server registry.
4. Allow only declared fields. Normalize whitespace and email casing without changing user meaning.
5. Enforce server-side types, required fields, allowed values, maximum lengths, and total payload size.
6. Apply a hidden honeypot and reasonable abuse controls. Return a generic success response for obvious
   bots when that prevents adaptive spam.
7. Create a submission UUID and timestamp.
8. Save the canonical submission to D1 first.
9. Attempt the webhook only after the D1 write succeeds.
10. Record webhook status, attempt time, response code, and a bounded sanitized error.
11. Return success to the visitor after the durable write even when webhook delivery fails. The admin
    dashboard must show the failure and allow retry.

Do not store IP addresses, full user-agent strings, or tracking identifiers by default. Add them only
when the user has a legitimate operational need, appropriate disclosure, a retention policy, and a
privacy-preserving implementation.

## 4. Persist submissions in D1

Declare the Sites D1 binding as `DB`. Define the schema in `db/schema.ts`, keep database access behind
a server-only helper, generate a Drizzle migration, and inspect the SQL before checkpointing.

Use the generic submission model in the implementation contract unless the project needs a justified
extension. At minimum, persist:

- Submission UUID
- Canonical `form_id`
- Canonical `form_name`
- Submission timestamp
- Validated field payload as JSON
- Optional normalized display name and email for admin search
- Webhook status, attempt time, response code, and error

Use separate D1 configuration storage for admin-editable webhook settings. Do not put secrets in
`.openai/hosting.json`, source files, client bundles, prompts, or logs.

## 5. Build the protected admin dashboard

Create `/admin` as a dynamic server-rendered route. Use dispatch-owned Sign in with ChatGPT from the
Sites starter, then enforce an explicit email allowlist in server-side code for every page and API
request. Authentication identifies the user, but authorization decides whether the user is an admin.

Store the allowlist in a hosted `ADMIN_EMAILS` environment value, not in browser code. Configure it
before deployment and redeploy so the new environment revision is active. Never expose the allowlist
to ordinary visitors.

The admin dashboard must provide:

- Total submission count and useful delivery counts.
- A paginated or bounded newest-first submission list.
- Search across the safe normalized fields and payload values.
- Filters for form ID/name, date range, and webhook status.
- A detail view showing every submitted field, canonical form identity, timestamp, and delivery state.
- CSV export containing all authorized submission data, including `form_id` and `form_name`.
- Webhook enable/disable control.
- HTTPS webhook endpoint configuration.
- Optional bearer-token configuration. Do not return the stored token to the browser after saving it.
- A clear-token action that is distinct from leaving the token input blank.
- A test-webhook action that emits a recognizable `contact.test` or `<form>.test` event.
- Retry for failed, disabled, or not-configured submissions after configuration is corrected.
- Sign-out and a clear unauthorized state.

Protect every admin API independently. Do not assume that hiding a link, protecting only the page, or
checking authorization in client code protects the data. Return `Cache-Control: no-store` for admin
data and exports. Render user content as text, never as untrusted HTML. Do not add destructive delete
or bulk operations unless the user requests them and the flow includes confirmation and recovery.

## 6. Make webhook delivery reliable and configurable

Default webhook behavior:

- Use HTTPS only.
- Send `POST application/json`.
- Use a bounded timeout, normally 7 to 10 seconds.
- Include event name, source, send timestamp, submission UUID, `form_id`, `form_name`, canonical
  submission timestamp, and validated fields.
- Add `Authorization: Bearer <token>` only when an admin configured a token.
- Never include the token in the payload, browser response, D1 export, logs, or error text.
- Save before sending. Webhook failure must never erase or roll back the submission.
- Treat only HTTP 2xx as delivered.
- Record a bounded error and expose retry from the admin dashboard.
- Make retries idempotency-friendly by preserving the submission UUID and sending it in an
  `Idempotency-Key` header or documented payload field.
- A manual test event must be clearly marked as a test and must not create a fake form submission.

If the endpoint requires HMAC signatures, custom headers, mTLS, a private network, or another special
mechanism, adapt only after confirming Sites supports the required connection. Keep all credentials
server-side.

## 7. Validate before publishing

Always complete source-level validation even when the user did not request visual browser QA:

- Generate and inspect every D1 migration.
- Run lint and strict type checking when available.
- Run the production build through the Sites checkpoint workflow.
- Confirm the artifact contains the Worker entry point, Sites manifest, D1 binding, and migrations.
- Check that public metadata and social previews still match the page.
- Confirm admin pages are dynamic and `noindex`.
- Confirm every admin route performs server-side allowlist authorization.
- Confirm webhook credentials never enter the client bundle or serialized admin props.

Add focused tests for the form contract and operational failure modes:

1. A valid submission stores the canonical `form_id` and `form_name`.
2. Every rendered form contains both hidden inputs.
3. Missing, unknown, or mismatched form identity is rejected or canonicalized according to the stated
   server policy.
4. Required-field, email, enum, length, and payload-size validation rejects invalid input.
5. A valid D1 write followed by webhook failure still returns visitor success and records failure.
6. A delivered webhook records status and response code.
7. Test delivery does not create a submission row.
8. Retry preserves submission UUID, `form_id`, and `form_name`.
9. Anonymous and non-admin users cannot open admin data, configuration, export, test, or retry APIs.
10. CSV output escapes commas, quotes, and newlines and includes form identity columns.
11. Blank token input preserves the existing token, while explicit clear removes it.

Run agent preview or browser interaction testing only when the user explicitly requests browser,
visual, or end-to-end QA, as required by the Sites skill. When authorized, exercise desktop and mobile
layouts, keyboard navigation, one valid submission, one validation failure, admin sign-in, filtering,
CSV export, webhook save/test, and retry. Do not claim a real webhook test succeeded without a real
endpoint response.

## 8. Publish and hand off

Keep the Site owner-only while building unless the user already requested and approved a broader
audience. Use Sites checkpoints for validated production deployments. Obtain explicit approval before
deploying a shared or public Site and before widening access.

After authoritative deployment success, provide:

- Public landing-page URL.
- Admin URL, normally `/admin`.
- Current access mode.
- Which admin account or accounts are authorized, without unnecessarily repeating private addresses.
- Forms created, with their `form_id` and `form_name` values.
- D1 persistence confirmation.
- Webhook configuration state and how to send a test.
- Validation performed, including what passed and what was not tested.
- Any remaining user action, such as entering a webhook endpoint, adding a custom domain, approving
  public access, supplying final copy, or providing a privacy policy.

Never claim the admin, webhook, D1 migration, custom domain, public access, or end-to-end submission
flow works unless the corresponding validation or authoritative platform response supports the claim.
