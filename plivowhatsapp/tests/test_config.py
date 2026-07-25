import json
import os
import stat
import copy
from pathlib import Path

import pytest

from plivo_whatsapp_lib.config import (
    delete_profile,
    load_store,
    normalize_e164,
    profile_path,
    redact_profile,
    save_store,
    upsert_profile,
)
from plivo_whatsapp_lib.templates import build_ephemeral_template


def sample_profile():
    return {
        "auth_id": "MAABCDEFGHIJKLMNOPQR",
        "auth_token": "secret-token",
        "sender": "+19543525707",
        "waba_id": "123456789012345",
        "default_template": "task_completes",
        "templates": {
            "task_completes": {
                "template_id": None,
                "name": "task_completes",
                "language": "en-US",
                "category": None,
                "status": "UNKNOWN",
                "quality_score": None,
                "source": "manual",
                "components": [
                    {"type": "BODY", "text": "Task {{1}} owner {{2}}"}
                ],
                "parameters": [
                    {
                        "kind": "positional",
                        "key": "1",
                        "component": "body",
                    },
                    {
                        "kind": "positional",
                        "key": "2",
                        "component": "body",
                    },
                ],
            }
        },
    }


def test_profile_path_uses_private_config_home(tmp_path):
    assert profile_path(tmp_path) == (
        tmp_path / ".config" / "plivo-whatsapp" / "profiles.json"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+1 954 352 5707", "+19543525707"),
        ("19253858017", "+19253858017"),
    ],
)
def test_normalize_e164(raw, expected):
    assert normalize_e164(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "+0123", "+1234567890123456"])
def test_normalize_e164_rejects_invalid_values(raw):
    with pytest.raises(ValueError):
        normalize_e164(raw)


def test_normalize_e164_removes_supported_punctuation():
    assert normalize_e164("+1 (954)-352-5707") == "+19543525707"


def test_load_store_returns_empty_store_when_path_does_not_exist(tmp_path):
    assert load_store(tmp_path / "missing.json") == {"version": 1, "profiles": {}}


def test_save_store_uses_private_permissions_and_round_trips(tmp_path):
    path = profile_path(tmp_path)
    store = {"version": 1, "profiles": {"default": sample_profile()}}
    save_store(store, path)
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert load_store(path) == store


def test_store_round_trip_allows_stale_legacy_default_template(tmp_path):
    path = profile_path(tmp_path)
    profile = sample_profile()
    profile["templates"] = {}
    store = {"version": 1, "profiles": {"default": profile}}

    save_store(store, path)

    assert load_store(path) == store


@pytest.mark.parametrize(
    "default_template",
    [123, "", "   ", " task_completes"],
)
def test_store_rejects_malformed_legacy_default_template(
    tmp_path,
    default_template,
):
    profile = sample_profile()
    profile["default_template"] = default_template

    with pytest.raises(ValueError, match="default_template"):
        save_store(
            {"version": 1, "profiles": {"default": profile}},
            profile_path(tmp_path),
        )


def test_persisted_profile_rejects_ephemeral_template(tmp_path):
    profile = sample_profile()
    profile["templates"]["task_completes"] = build_ephemeral_template(
        "task_completes", "en_US", "Task {{1}} result {{2}}"
    )
    with pytest.raises(ValueError, match="ephemeral"):
        save_store(
            {"version": 1, "profiles": {"default": profile}},
            profile_path(tmp_path),
        )


def test_save_store_replaces_atomically(tmp_path, monkeypatch):
    path = profile_path(tmp_path)
    save_store({"version": 1, "profiles": {}}, path)
    replacements = []
    real_replace = os.replace
    monkeypatch.setattr(
        os,
        "replace",
        lambda src, dst: (
            replacements.append((Path(src), Path(dst))),
            real_replace(src, dst),
        )[1],
    )
    save_store({"version": 1, "profiles": {"default": sample_profile()}}, path)
    assert replacements and replacements[-1][1] == path


@pytest.mark.parametrize(
    "store",
    [
        {"version": 2, "profiles": {}},
        {"version": True, "profiles": {}},
        {"version": 1, "profiles": []},
    ],
)
def test_save_store_rejects_invalid_store_shape(tmp_path, store):
    with pytest.raises(ValueError):
        save_store(store, tmp_path / "profiles.json")


def test_load_store_rejects_invalid_store_shape(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text('{"version": 1, "profiles": []}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_store(path)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda profile: profile.pop("auth_id"), "auth_id"),
        (
            lambda profile: profile.update(auth_id="not-a-plivo-auth-id"),
            "auth_id",
        ),
        (lambda profile: profile.update(auth_token="   "), "auth_token"),
        (lambda profile: profile.update(sender="19543525707"), "sender"),
        (lambda profile: profile.update(waba_id=123), "waba_id"),
        (lambda profile: profile.update(waba_id="waba-not-numeric"), "waba_id"),
        (lambda profile: profile.update(templates=[]), "templates"),
        (lambda profile: profile.update(default_template=123), "default_template"),
        (
            lambda profile: profile["templates"]["task_completes"].update(
                language="English"
            ),
            "BCP-47",
        ),
        (
            lambda profile: profile["templates"]["task_completes"].update(
                source="remote"
            ),
            "source",
        ),
        (
            lambda profile: profile["templates"]["task_completes"].update(
                parameters=[]
            ),
            "parameters",
        ),
    ],
)
def test_load_store_rejects_invalid_stored_profile_schema(
    tmp_path,
    mutation,
    match,
):
    profile = copy.deepcopy(sample_profile())
    mutation(profile)
    path = tmp_path / "profiles.json"
    path.write_text(
        json.dumps({"version": 1, "profiles": {"work": profile}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=match):
        load_store(path)


def test_upsert_profile_adds_and_replaces_named_profile(tmp_path):
    path = profile_path(tmp_path)
    original = sample_profile()
    inserted = upsert_profile("work", original, path)
    assert inserted == {"version": 1, "profiles": {"work": original}}

    replacement = {**sample_profile(), "sender": "+19253858017"}
    replaced = upsert_profile("work", replacement, path)
    assert replaced == {"version": 1, "profiles": {"work": replacement}}
    assert load_store(path) == replaced


def test_delete_profile_removes_named_profile(tmp_path):
    path = profile_path(tmp_path)
    upsert_profile("work", sample_profile(), path)
    resulting_store = delete_profile("work", path)
    assert resulting_store == {"version": 1, "profiles": {}}
    assert load_store(path) == resulting_store


def test_redact_profile_never_returns_token():
    visible = redact_profile(sample_profile())
    assert visible["auth_token"] == "***REDACTED***"
    assert "secret-token" not in json.dumps(visible)


def test_redact_profile_does_not_modify_input_or_share_nested_values():
    profile = sample_profile()
    visible = redact_profile(profile)
    visible["templates"]["task_completes"]["language"] = "fr"
    assert profile == sample_profile()
