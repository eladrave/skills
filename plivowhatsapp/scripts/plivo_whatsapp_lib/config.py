"""Secure local profile storage for the Plivo WhatsApp skill."""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path

from .templates import validate_template


EMPTY_STORE = {"version": 1, "profiles": {}}
_E164_PATTERN = re.compile(r"\+[1-9][0-9]{7,14}")
_AUTH_ID_PATTERN = re.compile(r"MA[A-Z0-9]{18}")
_WABA_ID_PATTERN = re.compile(r"[1-9][0-9]{4,31}")


def profile_path(home: Path | None = None) -> Path:
    base = home if home is not None else Path.home()
    return base / ".config" / "plivo-whatsapp" / "profiles.json"


def normalize_e164(value: str) -> str:
    normalized = re.sub(r"[ ()-]", "", value)
    if not normalized.startswith("+"):
        normalized = f"+{normalized}"
    if _E164_PATTERN.fullmatch(normalized) is None:
        raise ValueError("phone number must be a valid E.164 value")
    return normalized


def _validate_store(store: object) -> None:
    if not isinstance(store, Mapping):
        raise ValueError("profile store must be a mapping")
    version = store.get("version")
    if type(version) is not int or version != 1:
        raise ValueError("profile store version must be 1")
    if not isinstance(store.get("profiles"), Mapping):
        raise ValueError("profile store profiles must be a mapping")
    for name, profile in store["profiles"].items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("profile names must be non-empty strings")
        validate_profile(profile)


def validate_profile(profile: object) -> None:
    """Validate a complete profile without contacting Plivo."""
    if not isinstance(profile, Mapping):
        raise ValueError("profile must be a mapping")

    for field in ("auth_id", "auth_token", "sender"):
        value = profile.get(field)
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
        ):
            raise ValueError(
                f"profile {field} must be a non-empty string"
            )

    if _AUTH_ID_PATTERN.fullmatch(profile["auth_id"]) is None:
        raise ValueError(
            "profile auth_id must be a 20-character Plivo Auth ID "
            "starting with MA"
        )

    sender = profile["sender"]
    try:
        normalized_sender = normalize_e164(sender)
    except ValueError:
        raise ValueError(
            "profile sender must be a valid E.164 value"
        ) from None
    if normalized_sender != sender:
        raise ValueError(
            "profile sender must be stored in canonical E.164 format"
        )

    waba_id = profile.get("waba_id")
    if waba_id is not None and (
        not isinstance(waba_id, str)
        or not waba_id.strip()
        or waba_id != waba_id.strip()
        or _WABA_ID_PATTERN.fullmatch(waba_id) is None
    ):
        raise ValueError(
            "profile waba_id must be a numeric WhatsApp Business Account ID "
            "or None"
        )

    templates = profile.get("templates", {})
    if not isinstance(templates, Mapping):
        raise ValueError("profile templates must be a mapping")
    for name, template in templates.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "profile template names must be non-empty strings"
            )
        validate_template(template)
        if template["source"] == "ephemeral":
            raise ValueError("ephemeral templates must never be persisted")
        if template["name"] != name:
            raise ValueError(
                "profile template catalog key must match template name"
            )

    default_template = profile.get("default_template")
    if default_template is not None and (
        not isinstance(default_template, str)
        or not default_template.strip()
        or default_template != default_template.strip()
    ):
        raise ValueError(
            "profile default_template must be a non-empty string or None"
        )


def load_store(path: Path | None = None) -> dict:
    target = path if path is not None else profile_path()
    if not target.exists():
        return copy.deepcopy(EMPTY_STORE)

    with target.open(encoding="utf-8") as profile_file:
        store = json.load(profile_file)
    _validate_store(store)
    return store


def save_store(store: dict, path: Path | None = None) -> None:
    _validate_store(store)
    target = path if path is not None else profile_path()
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    target.parent.chmod(0o700)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(store, temporary_file, indent=2, sort_keys=True)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            os.fchmod(temporary_file.fileno(), 0o600)

        os.replace(temporary_path, target)
        target.chmod(0o600)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def upsert_profile(
    name: str,
    profile: dict,
    path: Path | None = None,
) -> dict:
    store = copy.deepcopy(load_store(path))
    store["profiles"][name] = copy.deepcopy(profile)
    save_store(store, path)
    return store


def delete_profile(name: str, path: Path | None = None) -> dict:
    store = copy.deepcopy(load_store(path))
    store["profiles"].pop(name, None)
    save_store(store, path)
    return store


def redact_profile(profile: dict) -> dict:
    visible = copy.deepcopy(profile)
    if "auth_token" in visible:
        visible["auth_token"] = "***REDACTED***"
    return visible
