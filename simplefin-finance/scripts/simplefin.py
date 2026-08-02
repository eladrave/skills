#!/usr/bin/env python3
"""Secure, zero-dependency SimpleFIN Bridge command-line client."""

from __future__ import annotations

import argparse
import base64
import binascii
import getpass
import json
import os
import re
import ssl
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_ALLOWED_HOST_SUFFIXES = (".simplefin.org",)
DEFAULT_SECRET_RELATIVE_PATH = Path(".simplefin") / "access-url"
MAX_WINDOW_DAYS = 90
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 30.0
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class SimpleFINError(RuntimeError):
    """A safe, user-displayable SimpleFIN client error."""


@dataclass(frozen=True)
class AccessDetails:
    accounts_url: str
    username: str
    password: str
    hostname: str


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old_host = urllib.parse.urlsplit(req.full_url).hostname
        parsed_new = _require_allowed_https_url(newurl, purpose="SimpleFIN redirect URL")
        if parsed_new.hostname != old_host:
            raise SimpleFINError("SimpleFIN attempted to redirect credentials to another host.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _allowed_host_suffixes() -> tuple[str, ...]:
    raw = os.getenv("SIMPLEFIN_ALLOWED_HOST_SUFFIXES", "")
    if not raw.strip():
        return DEFAULT_ALLOWED_HOST_SUFFIXES
    values = tuple(value.strip().lower() for value in raw.split(",") if value.strip())
    if not values:
        raise SimpleFINError("SIMPLEFIN_ALLOWED_HOST_SUFFIXES contains no valid values.")
    return values


def _host_is_allowed(hostname: str, suffixes: Sequence[str]) -> bool:
    normalized = hostname.rstrip(".").lower()
    for suffix in suffixes:
        candidate = suffix.rstrip(".").lower()
        if candidate.startswith("."):
            if normalized.endswith(candidate) and normalized != candidate[1:]:
                return True
        elif normalized == candidate:
            return True
    return False


def _require_allowed_https_url(url: str, *, purpose: str) -> urllib.parse.SplitResult:
    try:
        parsed = urllib.parse.urlsplit(url.strip())
    except ValueError as exc:
        raise SimpleFINError(f"{purpose} is not a valid URL.") from exc
    if parsed.scheme.lower() != "https":
        raise SimpleFINError(f"{purpose} must use HTTPS.")
    if not parsed.hostname:
        raise SimpleFINError(f"{purpose} has no hostname.")
    if parsed.fragment:
        raise SimpleFINError(f"{purpose} must not contain a URL fragment.")
    if not _host_is_allowed(parsed.hostname, _allowed_host_suffixes()):
        raise SimpleFINError(
            f"{purpose} host is not allowed. Configure "
            "SIMPLEFIN_ALLOWED_HOST_SUFFIXES only for a trusted SimpleFIN server."
        )
    return parsed


def parse_access_url(access_url: str) -> AccessDetails:
    parsed = _require_allowed_https_url(access_url, purpose="SimpleFIN Access URL")
    if parsed.username is None or parsed.password is None:
        raise SimpleFINError("SimpleFIN Access URL does not include Basic Auth credentials.")
    username = urllib.parse.unquote(parsed.username)
    password = urllib.parse.unquote(parsed.password)
    if not username or not password:
        raise SimpleFINError("SimpleFIN Access URL contains empty Basic Auth credentials.")

    clean_netloc = parsed.hostname or ""
    if parsed.port is not None:
        clean_netloc = f"{clean_netloc}:{parsed.port}"
    base_path = parsed.path.rstrip("/")
    accounts_path = f"{base_path}/accounts" if base_path else "/accounts"
    accounts_url = urllib.parse.urlunsplit(
        (parsed.scheme.lower(), clean_netloc, accounts_path, "", "")
    )
    return AccessDetails(
        accounts_url=accounts_url,
        username=username,
        password=password,
        hostname=parsed.hostname or "",
    )


def _decode_setup_token(setup_token: str) -> str:
    compact = "".join(setup_token.split())
    if not compact:
        raise SimpleFINError("Setup Token is empty.")
    padding = "=" * (-len(compact) % 4)
    try:
        decoded = base64.b64decode(compact + padding, altchars=b"-_", validate=True)
        claim_url = decoded.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise SimpleFINError("Setup Token is not valid Base64-encoded UTF-8.") from exc
    _require_allowed_https_url(claim_url, purpose="SimpleFIN claim URL")
    return claim_url


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def _urlopen(
    request: urllib.request.Request,
    *,
    timeout: float,
    allow_same_host_redirects: bool,
):
    redirect_handler = (
        _SameHostRedirectHandler() if allow_same_host_redirects else _NoRedirectHandler()
    )
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_ssl_context()),
        redirect_handler,
    )
    return opener.open(request, timeout=timeout)


def _safe_http_error(status: int, *, operation: str) -> SimpleFINError:
    if status == 402:
        return SimpleFINError(f"{operation} failed because SimpleFIN reports payment is required.")
    if status == 403:
        if operation == "Setup Token claim":
            return SimpleFINError(
                "Setup Token claim was rejected. The token may already have been claimed. "
                "Disable it in SimpleFIN if you did not claim it, then create a new token."
            )
        return SimpleFINError(
            "SimpleFIN rejected the Access URL. Access may have been revoked or the "
            "credential may be invalid."
        )
    if status == 429:
        return SimpleFINError(f"{operation} was rate limited. Try again later.")
    return SimpleFINError(f"{operation} failed with HTTP status {status}.")


def _open_request(
    request: urllib.request.Request,
    *,
    timeout: float,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> bytes:
    try:
        with _urlopen(
            request,
            timeout=timeout,
            allow_same_host_redirects=True,
        ) as response:
            length = response.headers.get("Content-Length")
            if length is not None:
                try:
                    if int(length) > max_bytes:
                        raise SimpleFINError("SimpleFIN response exceeded the allowed size.")
                except ValueError:
                    pass
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SimpleFINError("SimpleFIN response exceeded the allowed size.")
            return body
    except urllib.error.HTTPError as exc:
        raise _safe_http_error(exc.code, operation="SimpleFIN request") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        raise SimpleFINError(f"Could not reach the SimpleFIN server: {reason or 'network error'}.") from exc
    except TimeoutError as exc:
        raise SimpleFINError("SimpleFIN request timed out.") from exc


def claim_setup_token(setup_token: str, *, timeout: float) -> str:
    claim_url = _decode_setup_token(setup_token)
    request = urllib.request.Request(
        claim_url,
        data=b"",
        method="POST",
        headers={
            "Accept": "text/plain",
            "Content-Length": "0",
            "User-Agent": "simplefin-skill/1.0.0",
        },
    )
    try:
        with _urlopen(
            request,
            timeout=timeout,
            allow_same_host_redirects=False,
        ) as response:
            body = response.read(16 * 1024 + 1)
            if len(body) > 16 * 1024:
                raise SimpleFINError("SimpleFIN claim response was unexpectedly large.")
    except urllib.error.HTTPError as exc:
        raise _safe_http_error(exc.code, operation="Setup Token claim") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        raise SimpleFINError(
            f"Could not reach the SimpleFIN claim server: {reason or 'network error'}."
        ) from exc
    except TimeoutError as exc:
        raise SimpleFINError("Setup Token claim timed out.") from exc

    try:
        access_url = body.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise SimpleFINError("SimpleFIN claim response was not valid UTF-8.") from exc
    parse_access_url(access_url)
    return access_url


def _find_secret_file(start: Path | None = None) -> Path | None:
    explicit = os.getenv("SIMPLEFIN_ACCESS_URL_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / DEFAULT_SECRET_RELATIVE_PATH
        if candidate.is_file():
            return candidate
    return None


def load_access_url() -> str:
    from_environment = os.getenv("SIMPLEFIN_ACCESS_URL")
    if from_environment:
        parse_access_url(from_environment)
        return from_environment.strip()

    secret_file = _find_secret_file()
    if secret_file is None:
        raise SimpleFINError(
            "SimpleFIN is not configured. From the local project directory, run "
            "`python3 <skill-directory>/scripts/simplefin.py setup`."
        )
    try:
        mode = stat.S_IMODE(secret_file.stat().st_mode)
    except OSError as exc:
        raise SimpleFINError("Could not inspect the SimpleFIN secret file.") from exc
    if mode & 0o077:
        raise SimpleFINError(
            f"SimpleFIN secret file permissions are too broad ({mode:04o}); run "
            f"`chmod 600 {secret_file}`."
        )
    try:
        access_url = secret_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SimpleFINError("Could not read the SimpleFIN secret file.") from exc
    parse_access_url(access_url)
    return access_url


def credential_status() -> dict[str, Any]:
    """Return credential availability without returning credential contents."""
    from_environment = os.getenv("SIMPLEFIN_ACCESS_URL")
    if from_environment:
        parse_access_url(from_environment)
        return {"configured": True, "source": "runtime-injected-secret"}

    secret_file = _find_secret_file()
    if secret_file is None:
        return {"configured": False, "source": None}

    load_access_url()
    return {
        "configured": True,
        "source": "credential-file",
        "secret_file": str(secret_file),
    }


def _prepare_secret_destination(path: Path, *, replace: bool) -> Path:
    raw_destination = path.expanduser()
    if raw_destination.is_symlink():
        raise SimpleFINError("Secret destination must not be a symbolic link.")
    destination = raw_destination.resolve()
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(destination.parent, 0o700)
    except OSError as exc:
        raise SimpleFINError("Could not secure the SimpleFIN secret directory.") from exc

    if destination.exists():
        if not destination.is_file():
            raise SimpleFINError("Secret destination exists but is not a regular file.")
        try:
            mode = stat.S_IMODE(destination.stat().st_mode)
        except OSError as exc:
            raise SimpleFINError("Could not inspect the existing secret destination.") from exc
        if mode & 0o077:
            raise SimpleFINError(
                f"Existing secret destination permissions are too broad ({mode:04o})."
            )
        if not replace:
            raise SimpleFINError(
                f"Secret file already exists at {destination}. Use the configured "
                "credential or use --replace only for an intentional reconnection."
            )
    return destination


def preflight_secret_destination(path: Path, *, replace: bool) -> dict[str, Any]:
    """Verify safe local writability without creating or consuming a credential."""
    destination = _prepare_secret_destination(path, replace=replace)
    fd = -1
    probe_path: Path | None = None
    try:
        fd, probe_name = tempfile.mkstemp(prefix=".simplefin-storage-probe-", dir=destination.parent)
        probe_path = Path(probe_name)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write("storage-probe\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise SimpleFINError("Secret destination is not safely writable.") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        if probe_path is not None:
            try:
                probe_path.unlink(missing_ok=True)
            except OSError:
                pass

    return {
        "storage_ready": True,
        "secret_file": str(destination),
        "permissions": "0600",
        "note": (
            "Local writability is verified. The harness must separately guarantee "
            "that this location or its external backend persists across runs."
        ),
    }


def _write_secret_file(path: Path, access_url: str, *, replace: bool) -> None:
    destination = _prepare_secret_destination(path, replace=replace)

    fd, temporary_name = tempfile.mkstemp(prefix=".access-url-", dir=destination.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(access_url)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        os.chmod(destination, 0o600)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _basic_auth_header(details: AccessDetails) -> str:
    raw = f"{details.username}:{details.password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _sanitize_text(value: Any, *, maximum: int = 1000) -> str:
    text_value = CONTROL_CHARACTERS.sub("", str(value))
    return text_value[:maximum]


def _sanitize_json_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 8:
        return "[maximum depth reached]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _sanitize_text(value, maximum=4000)
    if isinstance(value, list):
        return [_sanitize_json_value(item, depth=depth + 1) for item in value[:500]]
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in list(value.items())[:500]:
            output[_sanitize_text(key, maximum=200)] = _sanitize_json_value(
                item,
                depth=depth + 1,
            )
        return output
    return _sanitize_text(value, maximum=1000)


def _sanitize_errors(payload: dict[str, Any]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    errlist = payload.get("errlist")
    if isinstance(errlist, list):
        for item in errlist:
            if not isinstance(item, dict):
                continue
            safe_item: dict[str, str] = {}
            for key in ("code", "msg", "conn_id", "account_id"):
                if item.get(key) is not None:
                    safe_item[key] = _sanitize_text(item[key], maximum=500)
            if safe_item:
                sanitized.append(safe_item)
    legacy = payload.get("errors")
    if isinstance(legacy, list):
        for message in legacy:
            sanitized.append({"code": "legacy", "msg": _sanitize_text(message, maximum=500)})
    return sanitized


def _timestamp_to_iso(value: Any) -> str | None:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    try:
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    connections: list[dict[str, Any]] = []
    for connection in payload.get("connections") or []:
        if not isinstance(connection, dict):
            continue
        connections.append(
            {
                "connection_id": _sanitize_text(connection.get("conn_id", "")),
                "name": _sanitize_text(connection.get("name", "")),
                "organization_id": _sanitize_text(connection.get("org_id", "")),
                "organization_url": _sanitize_text(connection.get("org_url", "")),
                "simplefin_url": _sanitize_text(connection.get("sfin_url", "")),
            }
        )

    accounts: list[dict[str, Any]] = []
    for account in payload.get("accounts") or []:
        if not isinstance(account, dict):
            continue
        transactions: list[dict[str, Any]] = []
        for transaction in account.get("transactions") or []:
            if not isinstance(transaction, dict):
                continue
            amount_value = str(transaction.get("amount", ""))
            try:
                amount = Decimal(amount_value)
                direction = "inflow" if amount > 0 else "outflow" if amount < 0 else "zero"
            except InvalidOperation:
                direction = "unknown"
            transactions.append(
                {
                    "transaction_id": _sanitize_text(transaction.get("id", "")),
                    "posted": transaction.get("posted"),
                    "posted_at": _timestamp_to_iso(transaction.get("posted")),
                    "transacted_at": _timestamp_to_iso(transaction.get("transacted_at")),
                    "amount": amount_value,
                    "direction": direction,
                    "description": _sanitize_text(transaction.get("description", ""), maximum=2000),
                    "pending": bool(transaction.get("pending", False)),
                    "extra": (
                        _sanitize_json_value(transaction.get("extra"))
                        if isinstance(transaction.get("extra"), dict)
                        else {}
                    ),
                }
            )
        transactions.sort(key=lambda item: (item.get("posted") or 0, item["transaction_id"]))
        accounts.append(
            {
                "account_id": _sanitize_text(account.get("id", "")),
                "connection_id": _sanitize_text(account.get("conn_id", "")),
                "name": _sanitize_text(account.get("name", "")),
                "currency": _sanitize_text(account.get("currency", "")),
                "balance": str(account.get("balance", "")),
                "available_balance": (
                    str(account["available-balance"])
                    if account.get("available-balance") is not None
                    else None
                ),
                "balance_date": account.get("balance-date"),
                "balance_at": _timestamp_to_iso(account.get("balance-date")),
                "transactions": transactions,
                "extra": (
                    _sanitize_json_value(account.get("extra"))
                    if isinstance(account.get("extra"), dict)
                    else {}
                ),
            }
        )

    return {
        "protocol_version": 2,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "errors": _sanitize_errors(payload),
        "connections": connections,
        "accounts": accounts,
    }


def fetch_accounts(
    *,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
    include_pending: bool = False,
    balances_only: bool = False,
    account_ids: Iterable[str] = (),
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    details = parse_access_url(load_access_url())
    params: list[tuple[str, str]] = [("version", "2")]
    if start_timestamp is not None:
        params.append(("start-date", str(start_timestamp)))
    if end_timestamp is not None:
        params.append(("end-date", str(end_timestamp)))
    if include_pending:
        params.append(("pending", "1"))
    if balances_only:
        params.append(("balances-only", "1"))
    for account_id in account_ids:
        value = account_id.strip()
        if value:
            params.append(("account", value))

    request_url = f"{details.accounts_url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        request_url,
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": _basic_auth_header(details),
            "User-Agent": "simplefin-skill/1.0.0",
        },
    )
    body = _open_request(request, timeout=timeout)
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SimpleFINError("SimpleFIN returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise SimpleFINError("SimpleFIN returned an unexpected JSON structure.")
    return _normalize_payload(payload)


def _parse_query_window(
    start_value: str,
    end_value: str,
    timezone_name: str,
) -> tuple[date, date, int, int]:
    try:
        start_date = date.fromisoformat(start_value)
        end_date = date.fromisoformat(end_value)
    except ValueError as exc:
        raise SimpleFINError("Dates must use ISO format YYYY-MM-DD.") from exc
    if end_date <= start_date:
        raise SimpleFINError("--end must be later than --start.")
    if (end_date - start_date).days > MAX_WINDOW_DAYS:
        raise SimpleFINError("SimpleFIN requests cannot span more than 90 days.")
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise SimpleFINError(f"Unknown timezone: {timezone_name}.") from exc
    start_dt = datetime.combine(start_date, time.min, tzinfo=zone)
    end_dt = datetime.combine(end_date, time.min, tzinfo=zone)
    return start_date, end_date, int(start_dt.timestamp()), int(end_dt.timestamp())


def _default_secret_path() -> Path:
    return Path.cwd() / DEFAULT_SECRET_RELATIVE_PATH


def _command_status(args: argparse.Namespace) -> dict[str, Any]:
    return credential_status()


def _command_preflight_storage(args: argparse.Namespace) -> dict[str, Any]:
    return preflight_secret_destination(Path(args.secret_file), replace=args.replace)


def _command_setup(args: argparse.Namespace) -> dict[str, Any]:
    if not args.storage_preflight_confirmed:
        raise SimpleFINError(
            "Refusing to consume a one-time Setup Token before persistent storage "
            "has been confirmed. Run preflight-storage and confirm the harness "
            "persists the selected destination or external credential backend."
        )
    setup_token = getpass.getpass("SimpleFIN Setup Token: ")
    access_url = claim_setup_token(setup_token, timeout=args.timeout)
    destination = Path(args.secret_file)
    _write_secret_file(destination, access_url, replace=args.replace)
    return {
        "configured": True,
        "secret_file": str(destination.expanduser().resolve()),
        "permissions": "0600",
        "message": "SimpleFIN connection configured. The Access URL was not printed.",
    }


def _command_accounts(args: argparse.Namespace) -> dict[str, Any]:
    result = fetch_accounts(balances_only=True, timeout=args.timeout)
    result["request"] = {"balances_only": True, "pending_included": False}
    return result


def _command_transactions(args: argparse.Namespace) -> dict[str, Any]:
    start_date, end_date, start_timestamp, end_timestamp = _parse_query_window(
        args.start,
        args.end,
        args.timezone,
    )
    result = fetch_accounts(
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        include_pending=args.include_pending,
        account_ids=args.account,
        timeout=args.timeout,
    )
    result["request"] = {
        "start_date_inclusive": start_date.isoformat(),
        "end_date_exclusive": end_date.isoformat(),
        "timezone": args.timezone,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "pending_included": bool(args.include_pending),
        "account_ids": list(args.account),
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read account and transaction data from SimpleFIN Bridge."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTPS request timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--access-url-file",
        help=(
            "Credential file to use for this invocation. This is equivalent to "
            "SIMPLEFIN_ACCESS_URL_FILE and is intended for materialized private state."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser(
        "status",
        help="Check whether a credential is configured without calling SimpleFIN.",
    )
    status_parser.set_defaults(handler=_command_status)

    preflight_parser = subparsers.add_parser(
        "preflight-storage",
        help="Verify a secret destination is safely writable without consuming a token.",
    )
    preflight_parser.add_argument(
        "--secret-file",
        required=True,
        help="Planned credential destination.",
    )
    preflight_parser.add_argument(
        "--replace",
        action="store_true",
        help="Allow an existing restricted credential file during intentional reconnection.",
    )
    preflight_parser.set_defaults(handler=_command_preflight_storage)

    setup_parser = subparsers.add_parser(
        "setup",
        help="Privately claim a one-time Setup Token and save the Access URL.",
    )
    setup_parser.add_argument(
        "--secret-file",
        required=True,
        help="Preflighted secret destination.",
    )
    setup_parser.add_argument(
        "--storage-preflight-confirmed",
        action="store_true",
        help="Confirm a persistent destination or external credential backend was verified.",
    )
    setup_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing secret after intentionally creating a new connection.",
    )
    setup_parser.set_defaults(handler=_command_setup)

    accounts_parser = subparsers.add_parser(
        "accounts",
        help="List connected accounts and current balances.",
    )
    accounts_parser.set_defaults(handler=_command_accounts)

    transactions_parser = subparsers.add_parser(
        "transactions",
        help="Retrieve transactions for an inclusive/exclusive date window.",
    )
    transactions_parser.add_argument("--start", required=True, help="Inclusive date, YYYY-MM-DD.")
    transactions_parser.add_argument("--end", required=True, help="Exclusive date, YYYY-MM-DD.")
    transactions_parser.add_argument(
        "--timezone",
        default="America/New_York",
        help="IANA timezone used for date boundaries.",
    )
    transactions_parser.add_argument(
        "--account",
        action="append",
        default=[],
        help="SimpleFIN account ID. Repeat to request multiple accounts.",
    )
    transactions_parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Request pending transactions when supported.",
    )
    transactions_parser.set_defaults(handler=_command_transactions)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.timeout > 120:
        parser.error("--timeout must be greater than 0 and no more than 120 seconds.")
    if args.access_url_file:
        os.environ["SIMPLEFIN_ACCESS_URL_FILE"] = args.access_url_file
    try:
        result = args.handler(args)
    except SimpleFINError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stderr, ensure_ascii=False)
        sys.stderr.write("\n")
        return 1
    except KeyboardInterrupt:
        json.dump({"ok": False, "error": "Operation cancelled."}, sys.stderr)
        sys.stderr.write("\n")
        return 130
    json.dump({"ok": True, "data": result}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
