---
name: amazon-transaction-mcp
description: Use the private Amazon Transaction MCP to retrieve Amazon orders, item prices, shipments, and payment transactions. Apply when a user asks about their Amazon purchases or transaction history, including login recovery, MFA device selection, one-time codes, timeout-safe pagination, and bounded retries.
---

# Amazon Transaction MCP

Use the Amazon tools to answer read-only questions about the connected account. Keep every
call bounded because clients may enforce a 10-second tool budget and the server serializes
Amazon access.

## Run the requested read first

Do not perform a live authentication check before every request. Call the tool that directly
serves the user's intent. Persisted cookies normally make this the fastest path.

- Use `amazon_list_orders` for a bounded order period.
- Use `amazon_get_order` for item prices or full details for one known order.
- Use `amazon_search_orders` to locate matching item titles.
- Use `amazon_list_transactions` for charges and refunds.

Keep `all_pages=false` on every tool. Keep list-level `full_details=false`. Keep recipient,
payment, and link fields false unless the user explicitly requests that private information.

## Retrieve orders and item prices

For requests such as “get last week's orders and the price for each item”:

1. Call `amazon_list_orders` with `time_filter="last7"`, `start_index=0`, `limit=10`,
   `all_pages=false`, and `full_details=false`.
2. Collect the returned order numbers.
3. If `period_complete=false`, call the same tool again with
   `start_index=next_start_index`. Continue one page at a time until
   `period_complete=true` or the user-requested limit is reached.
4. Call `amazon_get_order` once per collected order number, sequentially. Extract each item’s
   title, price, and quantity. Do not submit a large parallel batch because queued calls can
   exceed the client timeout.
5. Report missing prices as unavailable. Do not infer an item price from the order total.

Use `time_filter="last30"` for the last 30 days and `time_filter="months-3"` for the last
three months. For an older calendar year, use `year` and omit `time_filter`.

Do not describe a result as complete until `period_complete=true`. If stopping early, state
that the answer is partial.

## Recover authentication

If a read reports an expired session, login requirement, or other authentication failure:

1. Call `amazon_auth_status(check_live=false)` for a cheap local-state check.
2. If a persisted cookie exists but live state is unknown, call
   `amazon_auth_status(check_live=true)` once.
3. If live authentication is still false, call `amazon_authenticate` with no arguments.
4. Follow exactly one of the returned states:
   - `authenticated`: retry the original read once.
   - `device_choice_required`: show the numbered, masked choices; ask the user for one choice;
     then call `amazon_authenticate(device_choice=<one-based number>)`.
   - `otp_required`: ask the user for the current Amazon one-time code; then call
     `amazon_authenticate(otp_code=<code>)` once. Never quote, retain, log, or reuse the code.
   - `operator_required`: stop the automatic flow. Explain that Amazon presented a visual or
     browser challenge that requires the server operator. Do not loop or claim success.

If device selection leads to an OTP request, ask for the new code and submit it once. Never
ask for the Amazon password; credentials are already stored server-side.

## Retry without loops

- Retry the original read at most once after successful authentication.
- Never immediately repeat the same timed-out broad call. Reduce the scope, use the next
  page, or switch from list details to one `amazon_get_order` call.
- For a transient Amazon/network failure, retry the same bounded read once. If it fails again,
  report the error and stop.
- Do not repeatedly call `amazon_authenticate`; Amazon login attempts are rate-limited and
  repeated MFA attempts may invalidate a code.
- Do not retry validation errors. Correct the arguments using the tool guidance.

## Search and transactions

For a title search, call `amazon_search_orders` with a bounded period and paginate through
`next_start_index` only while `period_complete=false`. Call `amazon_get_order` for matching
orders when prices are needed.

For charges or refunds, call `amazon_list_transactions` with the smallest useful `days` value
or a specific `order_id`, `all_pages=false`, and an explicit `limit`. Treat positive values as
refunds only when `is_refund=true`.

## Protect private data

Never expose the MCP bearer token, tokenized URL, Amazon credentials, persisted cookies, or
OTP values. Summarize only the account data needed for the user's request. If the user asks
for addresses, payment details, or links, confirm the scope in the request and enable only the
matching opt-in field.
