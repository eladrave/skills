# SimpleFIN protocol notes

Authoritative sources:

- Developer guide: https://beta-bridge.simplefin.org/info/developers
- Protocol: https://www.simplefin.org/protocol.html

## Setup and authentication

- A Setup Token is a Base64-encoded claim URL.
- Decode the Setup Token and make one empty HTTPS `POST` to the claim URL with
  `Content-Length: 0`.
- A successful claim returns the long-lived Access URL as plain text and
  invalidates the Setup Token.
- The Access URL contains HTTP Basic Auth credentials. Store it securely and
  never print it.
- Request account data with `GET <ACCESS_URL>/accounts?version=2`.
- Verify TLS certificates. Never send credentials to a redirected host.

## Query parameters

- `version=2`: request protocol version 2.
- `start-date=<unix-seconds>`: inclusive transaction start.
- `end-date=<unix-seconds>`: exclusive transaction end.
- `pending=1`: include pending transactions when available.
- `balances-only=1`: request balances without transaction history.
- `account=<id>`: restrict results to an account. Repeat for multiple accounts.

SimpleFIN expects clients to make no more than 24 requests per day and to keep a
single requested date range within 90 days. For incremental synchronization,
the protocol recommends overlapping the prior range by about five days, then
deduplicating by stable identifiers.

## Response semantics

- `accounts` contains account metadata, balances, timestamps, and transactions.
- `connections` describes the institution connections referenced by accounts.
- `errlist` contains structured errors that must be surfaced to the user.
- Amounts are decimal strings. Positive amounts are deposits/inflows; negative
  amounts are withdrawals/outflows.
- `start-date` is inclusive and `end-date` is exclusive.
- Institutions may return less history than requested. No error does not prove
  that all historical transactions are present.
- `act.missingdata` means transaction coverage is incomplete for an account.
- Pending transactions may later disappear and be replaced by posted
  transactions with different identifiers.

## Error handling

- A 403 while claiming a Setup Token can mean it was already claimed. If the
  user did not claim it, advise disabling it and creating a new token.
- A 403 from the accounts endpoint means the Access URL is invalid or revoked.
- A 402 indicates a SimpleFIN payment problem.
- A 429 indicates rate limiting.

Sanitize all remote strings before displaying them, including descriptions,
institution names, errors, and arbitrary `extra` fields.
