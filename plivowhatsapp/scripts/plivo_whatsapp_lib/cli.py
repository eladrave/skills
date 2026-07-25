"""Interactive command line workflow for safe Plivo WhatsApp operations."""

from __future__ import annotations

import argparse
import getpass
import json
import re
from collections.abc import Callable
from pathlib import Path

from .config import (
    delete_profile,
    load_store,
    normalize_e164,
    profile_path,
    redact_profile,
    save_store,
    upsert_profile,
)
from .gateway import PlivoGateway, explain_error
from .templates import (
    build_ephemeral_template,
    search_templates,
    validate_sendable_template,
    validate_values,
)


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]
GatewayFactory = Callable[[dict], object]
_AUTHORIZATION_VALUE_PATTERN = re.compile(
    r"""
    (?P<prefix>["']?authorization["']?\s*[:=]\s*)
    (?:
        '(?:\\.|[^'])*'
        | "(?:\\.|[^"])*"
        | (?:(?:basic|bearer)\s+)?[^\s,}\]]+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_AUTH_SCHEME_CREDENTIAL_PATTERN = re.compile(
    r"\b(?P<scheme>basic|bearer)\s+[A-Za-z0-9._~+/=-]+",
    re.IGNORECASE,
)


def _add_context_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="advanced override for the local profile store",
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="configured profile name (default: default)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the complete command surface without credential arguments."""
    parser = argparse.ArgumentParser(
        description="Configure and use Plivo WhatsApp safely.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    configure = commands.add_parser("configure")
    configure.add_argument(
        "--config",
        type=Path,
        default=None,
        help="advanced override for the local profile store",
    )

    show_config = commands.add_parser("show-config")
    _add_context_arguments(show_config)

    delete = commands.add_parser("delete-profile")
    _add_context_arguments(delete)

    send_text = commands.add_parser("send-text")
    _add_context_arguments(send_text)
    send_text.add_argument("--to", dest="destination")
    send_text.add_argument("--text")

    send_template = commands.add_parser("send-template")
    _add_context_arguments(send_template)
    send_template.add_argument("--to", dest="destination")
    send_template.add_argument("--template")
    send_template.add_argument("--language")
    send_template.add_argument("--template-text")

    status = commands.add_parser("status")
    _add_context_arguments(status)
    status.add_argument("--message-uuid", required=True)
    status.add_argument(
        "--message-kind",
        choices=("freeform", "template"),
        required=True,
        help="original send mode, used for exact error guidance",
    )

    template = commands.add_parser("template")
    template_commands = template.add_subparsers(
        dest="template_command",
        required=True,
    )

    for name in ("list", "sync"):
        subcommand = template_commands.add_parser(name)
        _add_context_arguments(subcommand)

    template_show = template_commands.add_parser("show")
    _add_context_arguments(template_show)
    template_show.add_argument("--name", required=True)

    template_search = template_commands.add_parser("search")
    _add_context_arguments(template_search)
    template_search.add_argument("--query", required=True)

    template_inspect = template_commands.add_parser("inspect-text")
    template_inspect.add_argument("--text", required=True)

    return parser


def _store_path(args: argparse.Namespace) -> Path:
    return args.config if args.config is not None else profile_path()


def _profile(args: argparse.Namespace) -> tuple[dict, dict, Path]:
    path = _store_path(args)
    store = load_store(path)
    try:
        profile = store["profiles"][args.profile]
    except KeyError:
        raise ValueError(f"profile does not exist: {args.profile}") from None
    return store, profile, path


def _print_json(value: object, output_fn: OutputFn) -> None:
    output_fn(json.dumps(value, indent=2, sort_keys=True))


def _configure(
    args: argparse.Namespace,
    input_fn: InputFn,
    secret_fn: InputFn,
    output_fn: OutputFn,
) -> int:
    name = input_fn("Profile name: ").strip()
    auth_id = input_fn("Plivo Auth ID: ").strip()
    auth_token = secret_fn("Plivo Auth Token: ")
    sender = normalize_e164(input_fn("WhatsApp sender number: ").strip())
    waba_id = input_fn("WABA ID (optional): ").strip() or None

    if not name:
        raise ValueError("profile name must not be empty")
    if not auth_id:
        raise ValueError("Plivo Auth ID must not be empty")
    if not auth_token:
        raise ValueError("Plivo Auth Token must not be empty")

    profile = {
        "auth_id": auth_id,
        "auth_token": auth_token,
        "sender": sender,
        "waba_id": waba_id,
        "templates": {},
    }
    upsert_profile(name, profile, _store_path(args))
    _print_json(redact_profile(profile), output_fn)
    return 0


def _show_config(
    args: argparse.Namespace,
    output_fn: OutputFn,
) -> int:
    _, profile, _ = _profile(args)
    _print_json(redact_profile(profile), output_fn)
    return 0


def _delete_profile(
    args: argparse.Namespace,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> int:
    _profile(args)
    answer = input_fn(f"Delete profile {args.profile}? Type yes to confirm: ")
    if answer != "yes":
        output_fn("Profile deletion cancelled.")
        return 2
    delete_profile(args.profile, _store_path(args))
    output_fn(f"Deleted profile {args.profile}.")
    return 0


def _save_profile(
    store: dict,
    profile_name: str,
    profile: dict,
    path: Path,
) -> None:
    store["profiles"][profile_name] = profile
    save_store(store, path)


def _template_command(
    args: argparse.Namespace,
    gateway_factory: GatewayFactory,
    output_fn: OutputFn,
) -> int:
    if args.template_command == "inspect-text":
        template = build_ephemeral_template(
            "inspection_only",
            "en",
            args.text,
        )
        _print_json(
            {
                "text": args.text,
                "parameters": template["parameters"],
            },
            output_fn,
        )
        return 0

    store, profile, path = _profile(args)

    if args.template_command == "list":
        _print_json(profile.get("templates", {}), output_fn)
        return 0

    if args.template_command == "show":
        try:
            template = profile.get("templates", {})[args.name]
        except KeyError:
            raise ValueError(f"template does not exist: {args.name}") from None
        _print_json(template, output_fn)
        return 0

    if args.template_command == "search":
        _print_json(
            search_templates(profile.get("templates", {}), args.query),
            output_fn,
        )
        return 0

    if args.template_command == "sync":
        if not profile.get("waba_id"):
            raise ValueError("WABA ID is required for remote template synchronization")
        templates = gateway_factory(profile).sync_remote_templates()
        updated = dict(profile)
        updated["templates"] = templates
        _save_profile(store, args.profile, updated, path)
        _print_json(templates, output_fn)
        return 0

    raise ValueError(f"unsupported template command: {args.template_command}")


def _destination(args: argparse.Namespace, input_fn: InputFn) -> str:
    raw = args.destination
    if raw is None:
        raw = input_fn("Destination number: ")
    return normalize_e164(raw.strip())


def _confirm_send(
    input_fn: InputFn,
    output_fn: OutputFn,
    prompt: str = "Send exactly once? Type yes to confirm: ",
) -> bool:
    answer = input_fn(prompt)
    if answer == "yes":
        return True
    output_fn("Send cancelled; no external request was made.")
    return False


def _report_sent_statuses(
    gateway: object,
    message_uuids: list[str],
    message_kind: str,
    args: argparse.Namespace,
    output_fn: OutputFn,
) -> bool:
    failed = False
    for message_uuid in message_uuids:
        output_fn(f"Message UUID: {message_uuid}")
        try:
            status = gateway.message_status(message_uuid)
        except Exception as error:
            failed = True
            output_fn(f"{message_uuid}: status error: {_redacted_error(error, args)}")
            continue
        state = status.get("message_state", "unknown")
        error_code = status.get("error_code")
        line = f"{status.get('message_uuid', message_uuid)}: {state}"
        if error_code:
            line += f" (error {error_code})"
            line += f"; {explain_error(str(error_code), message_kind)}"
        output_fn(line)
    return not failed


def _ambiguous_send_error(
    message_kind: str,
    error: Exception,
) -> RuntimeError:
    return RuntimeError(
        f"The {message_kind} send result is ambiguous: {error}. "
        "Do not automatically retry; reconcile the Plivo message record "
        "first."
    )


def _send_text(
    args: argparse.Namespace,
    input_fn: InputFn,
    gateway_factory: GatewayFactory,
    output_fn: OutputFn,
) -> int:
    _, profile, _ = _profile(args)
    destination = _destination(args, input_fn)
    text = args.text
    if text is None:
        text = input_fn("Message text: ")
    if not text:
        raise ValueError("message text must not be empty")

    _print_json(
        {
            "profile": args.profile,
            "sender": profile["sender"],
            "to": destination,
            "type": "freeform",
            "text": text,
        },
        output_fn,
    )
    if not _confirm_send(input_fn, output_fn):
        return 2

    gateway = gateway_factory(profile)
    try:
        message_uuids = gateway.send_text(destination, text)
    except Exception as error:
        raise _ambiguous_send_error("freeform", error) from error
    statuses_ok = _report_sent_statuses(
        gateway,
        message_uuids,
        "freeform",
        args,
        output_fn,
    )
    return 0 if statuses_ok else 1


def _resolve_template(
    profile: dict,
    args: argparse.Namespace,
    input_fn: InputFn,
) -> tuple[dict, str]:
    name = args.template or input_fn("Existing template name: ").strip()
    if not name:
        raise ValueError("template name must not be empty")

    cached = profile.get("templates", {}).get(name)
    if cached is not None and cached.get("source") == "waba":
        return cached, "provider-verified"

    language = args.language or input_fn(
        "Exact Plivo template language code: "
    ).strip()
    text = args.template_text or input_fn(
        "Complete existing template text: "
    )
    return (
        build_ephemeral_template(name, language, text),
        "user-attested-unverified",
    )


def _send_template(
    args: argparse.Namespace,
    input_fn: InputFn,
    gateway_factory: GatewayFactory,
    output_fn: OutputFn,
) -> int:
    _, profile, _ = _profile(args)
    destination = _destination(args, input_fn)
    template, approval = _resolve_template(profile, args, input_fn)
    validate_sendable_template(template)
    values = {}
    for parameter in template.get("parameters", []):
        key = parameter["key"]
        values[key] = input_fn(f"Template parameter {key}: ")
    validate_values(template, values)

    _print_json(
        {
            "profile": args.profile,
            "sender": profile["sender"],
            "to": destination,
            "type": "template",
            "template": template["name"],
            "language": template["language"],
            "status": template.get("status", "UNKNOWN"),
            "parameters": values,
            "approval": approval,
            "template_text": next(
                component["text"]
                for component in template["components"]
                if component["type"].upper() == "BODY"
            ),
        },
        output_fn,
    )
    confirmation_prompt = (
        "I confirm this existing Plivo template is approved. "
        "Send exactly once? Type yes to confirm: "
        if approval == "user-attested-unverified"
        else "Send exactly once? Type yes to confirm: "
    )
    if not _confirm_send(input_fn, output_fn, confirmation_prompt):
        return 2

    gateway = gateway_factory(profile)
    try:
        message_uuids = gateway.send_template(
            destination,
            template,
            values,
        )
    except Exception as error:
        raise _ambiguous_send_error("template", error) from error
    statuses_ok = _report_sent_statuses(
        gateway,
        message_uuids,
        "template",
        args,
        output_fn,
    )
    return 0 if statuses_ok else 1


def _status(
    args: argparse.Namespace,
    gateway_factory: GatewayFactory,
    output_fn: OutputFn,
) -> int:
    _, profile, _ = _profile(args)
    status = gateway_factory(profile).message_status(args.message_uuid)
    status = dict(status)
    status["message_kind"] = args.message_kind
    error_code = status.get("error_code")
    if error_code:
        status["error_guidance"] = explain_error(
            str(error_code),
            args.message_kind,
        )
    _print_json(status, output_fn)
    return 0


def _redacted_error(error: Exception, args: argparse.Namespace) -> str:
    message = str(error).replace("\r", " ").replace("\n", " ")
    try:
        store = load_store(_store_path(args))
    except Exception:
        store = {"profiles": {}}
    for profile in store.get("profiles", {}).values():
        token = profile.get("auth_token")
        if token:
            message = message.replace(str(token), "***REDACTED***")
    message = _AUTHORIZATION_VALUE_PATTERN.sub(
        lambda match: f"{match.group('prefix')}***REDACTED***",
        message,
    )
    message = _AUTH_SCHEME_CREDENTIAL_PATTERN.sub(
        lambda match: f"{match.group('scheme')} ***REDACTED***",
        message,
    )
    return message


def main(
    argv: list[str] | None = None,
    *,
    input_fn: InputFn = input,
    secret_fn: InputFn = getpass.getpass,
    gateway_factory: GatewayFactory = PlivoGateway,
    output_fn: OutputFn = print,
) -> int:
    """Run one CLI operation and return its process exit status."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "configure":
            return _configure(args, input_fn, secret_fn, output_fn)
        if args.command == "show-config":
            return _show_config(args, output_fn)
        if args.command == "delete-profile":
            return _delete_profile(args, input_fn, output_fn)
        if args.command == "send-text":
            return _send_text(
                args,
                input_fn,
                gateway_factory,
                output_fn,
            )
        if args.command == "send-template":
            return _send_template(
                args,
                input_fn,
                gateway_factory,
                output_fn,
            )
        if args.command == "status":
            return _status(args, gateway_factory, output_fn)
        if args.command == "template":
            return _template_command(
                args,
                gateway_factory,
                output_fn,
            )
        raise ValueError(f"unsupported command: {args.command}")
    except Exception as error:
        output_fn(f"Error: {_redacted_error(error, args)}")
        return 1
