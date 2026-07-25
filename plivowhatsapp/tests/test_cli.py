import json
from pathlib import Path

import pytest

import plivo_whatsapp
from plivo_whatsapp_lib.cli import build_parser, main
from plivo_whatsapp_lib.config import load_store, profile_path, save_store


def task_template(*, language="en", status="APPROVED", source="waba"):
    return {
        "template_id": "tpl-1" if source == "waba" else None,
        "name": "task_completes",
        "language": language,
        "category": "UTILITY" if source == "waba" else None,
        "status": status,
        "quality_score": None,
        "source": source,
        "components": [{"type": "BODY", "text": "Task {{1}} is {{2}}"}],
        "parameters": [
            {"kind": "positional", "key": "1", "component": "body"},
            {"kind": "positional", "key": "2", "component": "body"},
        ],
    }


def configured_profile(*, waba_id=None):
    return {
        "auth_id": "MAABCDEFGHIJKLMNOPQR",
        "auth_token": "secret-token",
        "sender": "+19543525707",
        "waba_id": waba_id,
        "default_template": "task_completes",
        "templates": {
            "task_completes": task_template(
                status="UNKNOWN",
                source="manual",
            )
        },
    }


@pytest.fixture
def configured_path(tmp_path):
    path = profile_path(tmp_path)
    save_store(
        {
            "version": 1,
            "profiles": {"default": configured_profile()},
        },
        path,
    )
    return path


@pytest.fixture
def configured_waba_path(tmp_path):
    path = profile_path(tmp_path)
    save_store(
        {
            "version": 1,
            "profiles": {
                "default": configured_profile(waba_id="123456789012345")
            },
        },
        path,
    )
    return path


class FakeGateway:
    def __init__(self):
        self.send_calls = []
        self.send_attempts = 0
        self.status_calls = []
        self.next_status = {
            "message_uuid": "u1",
            "message_type": "whatsapp",
            "message_state": "queued",
            "error_code": "",
            "delivered": False,
        }
        self.send_error = None
        self.message_uuids = ["u1"]
        self.status_errors = {}
        self.remote_templates = {}

    def send_text(self, destination, text):
        self.send_attempts += 1
        if self.send_error is not None:
            raise self.send_error
        self.send_calls.append(("text", destination, text))
        return list(self.message_uuids)

    def send_template(self, destination, template, values):
        self.send_attempts += 1
        if self.send_error is not None:
            raise self.send_error
        self.send_calls.append(("template", destination, template, values))
        return list(self.message_uuids)

    def message_status(self, message_uuid):
        self.status_calls.append(message_uuid)
        if message_uuid in self.status_errors:
            raise self.status_errors[message_uuid]
        return dict(self.next_status)

    def sync_remote_templates(self):
        return dict(self.remote_templates)


@pytest.fixture
def fake_gateway():
    return FakeGateway()


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--help"],
        ["send-text", "--help"],
        ["template", "sync", "--help"],
        ["configure"],
        ["show-config"],
        ["delete-profile"],
        ["template", "list"],
        ["template", "show"],
        ["template", "search"],
        ["template", "inspect-text"],
    ],
)
def test_entrypoint_keeps_non_gateway_commands_outside_sdk_bootstrap(argv):
    main_calls = []

    assert (
        plivo_whatsapp.run(
            argv,
            sdk_available_fn=lambda: pytest.fail("SDK check was not expected"),
            ensure_sdk_fn=lambda **_: pytest.fail("SDK install was not expected"),
            execv_fn=lambda *_: pytest.fail("re-exec was not expected"),
            main_fn=lambda received: (main_calls.append(received), 7)[1],
        )
        == 7
    )

    assert main_calls == [argv]


@pytest.mark.parametrize(
    "argv",
    [
        ["send-text"],
        ["send-template"],
        ["status"],
        ["template", "sync"],
    ],
)
def test_entrypoint_reexecutes_gateway_commands_in_available_sdk_venv(
    tmp_path,
    argv,
):
    target_python = tmp_path / "venv" / "bin" / "python"
    exec_calls = []

    assert (
        plivo_whatsapp.run(
            argv,
            sdk_available_fn=lambda: True,
            ensure_sdk_fn=lambda **_: pytest.fail("install was not expected"),
            venv_python_fn=lambda: target_python,
            execv_fn=lambda executable, arguments: exec_calls.append((executable, arguments)),
            main_fn=lambda _: pytest.fail("main was not expected"),
            current_executable=tmp_path / "system" / "python",
        )
        == 0
    )

    assert exec_calls == [
        (
            str(target_python),
            [
                str(target_python),
                str(Path(plivo_whatsapp.__file__).resolve()),
                *argv,
            ],
        )
    ]


def test_entrypoint_obtains_consent_before_install_and_reexec(tmp_path):
    target_python = tmp_path / "venv" / "bin" / "python"
    prompts = []
    exec_calls = []

    def fake_ensure_sdk(*, confirm):
        assert confirm("Install the SDK?") is True
        return target_python

    assert (
        plivo_whatsapp.run(
            ["send-text"],
            input_fn=lambda prompt: (prompts.append(prompt), "yes")[1],
            sdk_available_fn=lambda: False,
            ensure_sdk_fn=fake_ensure_sdk,
            venv_python_fn=lambda: target_python,
            execv_fn=lambda executable, arguments: exec_calls.append((executable, arguments)),
            main_fn=lambda _: pytest.fail("main was not expected"),
            current_executable=tmp_path / "system" / "python",
        )
        == 0
    )

    assert prompts == ["Install the SDK? Type yes to confirm: "]
    assert exec_calls[0][0] == str(target_python)


def test_entrypoint_declined_sdk_install_exits_without_reexec(tmp_path):
    output = []

    def fake_ensure_sdk(*, confirm):
        if not confirm("Install the SDK?"):
            raise PermissionError("Plivo SDK installation declined")
        pytest.fail("confirmation unexpectedly accepted")

    assert (
        plivo_whatsapp.run(
            ["send-template"],
            input_fn=lambda _: "no",
            output_fn=output.append,
            sdk_available_fn=lambda: False,
            ensure_sdk_fn=fake_ensure_sdk,
            execv_fn=lambda *_: pytest.fail("re-exec was not expected"),
            main_fn=lambda _: pytest.fail("main was not expected"),
            current_executable=tmp_path / "system" / "python",
        )
        == 1
    )

    assert output == ["Error: Plivo SDK installation declined"]


def test_entrypoint_runs_gateway_command_directly_inside_sdk_venv(tmp_path):
    target_python = tmp_path / "venv" / "bin" / "python"
    main_calls = []

    assert (
        plivo_whatsapp.run(
            ["status"],
            sdk_available_fn=lambda: True,
            ensure_sdk_fn=lambda **_: pytest.fail("install was not expected"),
            venv_python_fn=lambda: target_python,
            execv_fn=lambda *_: pytest.fail("re-exec was not expected"),
            main_fn=lambda argv: (main_calls.append(argv), 0)[1],
            current_executable=target_python,
        )
        == 0
    )

    assert main_calls == [["status"]]


def test_parser_has_no_auth_token_argument():
    parser = build_parser()
    help_text = parser.format_help()
    for command in parser._subparsers._group_actions[0].choices.values():
        help_text += command.format_help()
    assert "--auth-token" not in help_text


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("add", ["--name", "task_completes", "--language", "en"]),
        ("remove", ["--name", "task_completes"]),
        ("set-default", ["--name", "task_completes"]),
    ],
)
def test_template_mutation_subcommands_are_not_registered(name, arguments):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["template", name, *arguments])


def test_configure_reads_token_from_secret_prompt(tmp_path):
    answers = iter(["default", "MAABCDEFGHIJKLMNOPQR", "+19543525707", ""])
    secrets = []
    path = profile_path(tmp_path)

    result = main(
        ["configure", "--config", str(path)],
        input_fn=lambda _: next(answers),
        secret_fn=lambda prompt: (
            secrets.append(prompt),
            "secret-token",
        )[1],
        output_fn=lambda _: None,
    )

    assert result == 0
    assert secrets == ["Plivo Auth Token: "]
    profile = load_store(path)["profiles"]["default"]
    assert profile["auth_token"] == "secret-token"
    assert profile["sender"] == "+19543525707"
    assert profile["waba_id"] is None
    assert profile["templates"] == {}


def test_configure_does_not_prompt_for_or_persist_template(tmp_path):
    path = profile_path(tmp_path)
    answers = iter(
        [
            "default",
            "MAABCDEFGHIJKLMNOPQR",
            "+19543525707",
            "",
        ]
    )
    prompts = []

    assert (
        main(
            ["configure", "--config", str(path)],
            input_fn=lambda prompt: (prompts.append(prompt), next(answers))[1],
            secret_fn=lambda _: "secret-token",
            output_fn=lambda _: None,
        )
        == 0
    )

    profile = load_store(path)["profiles"]["default"]
    assert profile["templates"] == {}
    assert profile.get("default_template") is None
    assert not any("template" in prompt.lower() for prompt in prompts)


def test_send_text_previews_and_requires_confirmation(
    configured_path,
    fake_gateway,
):
    answers = iter(["Hello", "no"])
    gateway_profiles = []
    output = []

    result = main(
        [
            "send-text",
            "--config",
            str(configured_path),
            "--profile",
            "default",
            "--to",
            "+19253858017",
        ],
        input_fn=lambda _: next(answers),
        gateway_factory=lambda profile: (
            gateway_profiles.append(profile),
            fake_gateway,
        )[1],
        output_fn=output.append,
    )

    assert result == 2
    assert gateway_profiles == []
    assert fake_gateway.send_calls == []
    assert fake_gateway.send_attempts == 0
    assert any("Hello" in line for line in output)


def test_send_text_sends_once_and_reports_queued_as_queued(
    configured_path,
    fake_gateway,
):
    answers = iter(["Hello", "yes"])
    fake_gateway.next_status = {
        "message_uuid": "u1",
        "message_state": "queued",
        "delivered": False,
    }
    output = []

    result = main(
        [
            "send-text",
            "--config",
            str(configured_path),
            "--profile",
            "default",
            "--to",
            "+19253858017",
        ],
        input_fn=lambda _: next(answers),
        gateway_factory=lambda _: fake_gateway,
        output_fn=output.append,
    )

    assert result == 0
    assert fake_gateway.send_calls == [("text", "+19253858017", "Hello")]
    assert fake_gateway.send_attempts == 1
    assert fake_gateway.status_calls == ["u1"]
    assert any("queued" in line for line in output)
    assert not any("delivered" in line.lower() for line in output)


def test_send_text_reads_every_returned_uuid_once(
    configured_path,
    fake_gateway,
):
    fake_gateway.message_uuids = ["u1", "u2"]

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--text",
                "Hello",
            ],
            input_fn=lambda _: "yes",
            gateway_factory=lambda _: fake_gateway,
            output_fn=lambda _: None,
        )
        == 0
    )

    assert fake_gateway.status_calls == ["u1", "u2"]


def test_send_text_preserves_all_uuids_when_first_status_read_fails(
    configured_path,
    fake_gateway,
):
    fake_gateway.message_uuids = ["u1", "u2"]
    fake_gateway.status_errors["u1"] = TimeoutError("status lookup failed for secret-token")
    output = []

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--text",
                "Hello",
            ],
            input_fn=lambda _: "yes",
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 1
    )

    assert fake_gateway.send_attempts == 1
    assert fake_gateway.status_calls == ["u1", "u2"]
    rendered = "\n".join(output)
    assert "u1" in rendered
    assert "u2" in rendered
    assert rendered.count("status lookup failed") == 1
    assert "secret-token" not in rendered
    assert "***REDACTED***" in rendered


def test_send_text_accepts_message_argument_without_prompting_for_text(
    configured_path,
    fake_gateway,
):
    prompts = []

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--text",
                "Hello",
            ],
            input_fn=lambda prompt: (prompts.append(prompt), "yes")[1],
            gateway_factory=lambda _: fake_gateway,
            output_fn=lambda _: None,
        )
        == 0
    )

    assert prompts == ["Send exactly once? Type yes to confirm: "]


def test_send_template_prompts_for_every_parameter(
    configured_path,
    fake_gateway,
):
    profile = configured_profile(waba_id="123456789012345")
    profile["templates"]["task_completes"] = task_template()
    save_store(
        {"version": 1, "profiles": {"default": profile}},
        configured_path,
    )
    answers = iter(["Newsletter setup", "Completed", "yes"])

    result = main(
        [
            "send-template",
            "--config",
            str(configured_path),
            "--profile",
            "default",
            "--template",
            "task_completes",
            "--to",
            "+19253858017",
        ],
        input_fn=lambda _: next(answers),
        gateway_factory=lambda _: fake_gateway,
        output_fn=lambda _: None,
    )

    assert result == 0
    assert fake_gateway.send_calls[0][3] == {
        "1": "Newsletter setup",
        "2": "Completed",
    }


def test_send_template_does_not_select_legacy_profile_default(
    configured_path,
    fake_gateway,
):
    prompts = []
    gateway_calls = []
    output = []

    assert (
        main(
            [
                "send-template",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
            ],
            input_fn=lambda prompt: (prompts.append(prompt), "")[1],
            gateway_factory=lambda profile: gateway_calls.append(profile),
            output_fn=output.append,
        )
        == 1
    )

    assert prompts == ["Existing template name: "]
    assert gateway_calls == []
    assert "template name must not be empty" in "\n".join(output)


def test_template_search_returns_cached_matches_without_gateway(
    configured_waba_path,
):
    output = []

    assert (
        main(
            [
                "template",
                "search",
                "--config",
                str(configured_waba_path),
                "--profile",
                "default",
                "--query",
                "task",
            ],
            gateway_factory=lambda _: pytest.fail("gateway was not expected"),
            output_fn=output.append,
        )
        == 0
    )

    assert "task_completes" in "\n".join(output)


def test_template_inspect_text_is_offline_and_has_no_profile_requirement():
    output = []

    assert (
        main(
            [
                "template",
                "inspect-text",
                "--text",
                "Task {{1}} result {{2}}",
            ],
            gateway_factory=lambda _: pytest.fail("gateway was not expected"),
            output_fn=output.append,
        )
        == 0
    )

    assert [
        item["key"]
        for item in json.loads("\n".join(output))["parameters"]
    ] == ["1", "2"]


@pytest.mark.parametrize(
    ("text", "expected_error"),
    [
        ("Task {{1}} repeats {{1}}", "duplicate"),
        (
            "Hello {{customer_name}} again {{customer_name}}",
            "duplicate",
        ),
        ("Task {{0}}", "invalid"),
        ("Task {{ customer }}", "invalid"),
        ("Task {{1", "unmatched opening"),
        ("Task 1}}", "unmatched closing"),
    ],
)
def test_template_inspect_text_rejects_invalid_body_markers_offline(
    text,
    expected_error,
):
    output = []

    result = main(
        ["template", "inspect-text", "--text", text],
        gateway_factory=lambda _: pytest.fail("gateway was not expected"),
        output_fn=output.append,
    )

    assert result == 1
    assert expected_error in "\n".join(output)


@pytest.mark.parametrize(
    ("text", "expected_error"),
    [
        ("Task {{1}} repeats {{1}}", "duplicate"),
        (
            "Hello {{customer_name}} again {{customer_name}}",
            "duplicate",
        ),
        ("Task {{0}}", "invalid"),
        ("Task {{ customer }}", "invalid"),
        ("Task {{1", "unmatched opening"),
        ("Task 1}}", "unmatched closing"),
    ],
)
def test_send_template_rejects_invalid_body_markers_before_side_effects(
    configured_path,
    fake_gateway,
    text,
    expected_error,
):
    before = configured_path.read_bytes()
    prompts = []
    gateway_calls = []
    output = []

    result = main(
        [
            "send-template",
            "--config",
            str(configured_path),
            "--profile",
            "default",
            "--to",
            "+19253858017",
            "--template",
            "task_completes",
            "--language",
            "en_US",
            "--template-text",
            text,
        ],
        input_fn=lambda prompt: (prompts.append(prompt), "yes")[1],
        gateway_factory=lambda profile: (
            gateway_calls.append(profile),
            fake_gateway,
        )[1],
        output_fn=output.append,
    )

    assert result == 1
    assert expected_error in "\n".join(output)
    assert prompts == []
    assert gateway_calls == []
    assert fake_gateway.send_calls == []
    assert fake_gateway.send_attempts == 0
    assert configured_path.read_bytes() == before


def test_no_waba_template_send_is_ephemeral_and_not_persisted(
    configured_path,
    fake_gateway,
):
    before = configured_path.read_bytes()
    prompts = []
    output = []
    answers = iter(["Task A", "Completed", "yes"])

    assert (
        main(
            [
                "send-template",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--template",
                "task_completes",
                "--language",
                "en_US",
                "--template-text",
                "The task {{1}} was completed. Result: {{2}}.",
            ],
            input_fn=lambda prompt: (
                prompts.append(prompt),
                next(answers),
            )[1],
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 0
    )

    assert configured_path.read_bytes() == before
    sent_template = fake_gateway.send_calls[0][2]
    assert sent_template["source"] == "ephemeral"
    assert sent_template["status"] == "UNVERIFIED"
    preview = json.loads(output[0])
    assert preview["approval"] == "user-attested-unverified"
    assert preview["template_text"] == (
        "The task {{1}} was completed. Result: {{2}}."
    )
    assert prompts[-1] == (
        "I confirm this existing Plivo template is approved. "
        "Send exactly once? Type yes to confirm: "
    )


def test_legacy_manual_cache_is_not_selected_automatically(
    configured_path,
    fake_gateway,
):
    profile = load_store(configured_path)["profiles"]["default"]
    assert profile["templates"]["task_completes"]["source"] == "manual"
    before = configured_path.read_bytes()
    answers = iter(
        ["en_US", "Task {{1}} result {{2}}", "A", "Done", "yes"]
    )

    assert (
        main(
            [
                "send-template",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--template",
                "task_completes",
            ],
            input_fn=lambda _: next(answers),
            gateway_factory=lambda _: fake_gateway,
            output_fn=lambda _: None,
        )
        == 0
    )

    assert fake_gateway.send_calls[0][2]["source"] == "ephemeral"
    assert configured_path.read_bytes() == before


def test_show_config_redacts_token(configured_path):
    output = []

    assert (
        main(
            [
                "show-config",
                "--config",
                str(configured_path),
                "--profile",
                "default",
            ],
            output_fn=output.append,
        )
        == 0
    )

    rendered = "\n".join(output)
    assert "***REDACTED***" in rendered
    assert "secret-token" not in rendered


def test_delete_profile_requires_confirmation(configured_path):
    assert (
        main(
            [
                "delete-profile",
                "--config",
                str(configured_path),
                "--profile",
                "default",
            ],
            input_fn=lambda _: "no",
            output_fn=lambda _: None,
        )
        == 2
    )
    assert "default" in load_store(configured_path)["profiles"]


def test_delete_profile_removes_profile_after_exact_confirmation(
    configured_path,
):
    assert (
        main(
            [
                "delete-profile",
                "--config",
                str(configured_path),
                "--profile",
                "default",
            ],
            input_fn=lambda _: "yes",
            output_fn=lambda _: None,
        )
        == 0
    )
    assert "default" not in load_store(configured_path)["profiles"]


def test_status_reads_once(configured_path, fake_gateway):
    output = []
    fake_gateway.next_status = {
        "message_uuid": "u1",
        "message_state": "read",
        "delivered": True,
        "error_code": "",
    }

    assert (
        main(
            [
                "status",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--message-uuid",
                "u1",
                "--message-kind",
                "template",
            ],
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 0
    )

    assert fake_gateway.status_calls == ["u1"]
    assert any("read" in line for line in output)


@pytest.mark.parametrize(
    ("command", "error_code", "expected_guidance"),
    [
        ("send-text", "340", "plivo error 340:"),
        ("send-template", "340", "plivo error 340:"),
        ("send-template", "350", "plivo error 350:"),
    ],
)
def test_post_send_status_uses_message_kind_error_guidance(
    configured_path,
    fake_gateway,
    command,
    error_code,
    expected_guidance,
):
    fake_gateway.next_status = {
        "message_uuid": "u1",
        "message_type": "whatsapp",
        "message_state": "failed",
        "error_code": error_code,
        "delivered": False,
    }
    answers = iter(
        ["Hello", "yes"]
        if command == "send-text"
        else ["Task", "Failed", "yes"]
    )
    output = []

    assert (
        main(
            [
                command,
                "--config",
                str(configured_path),
                "--profile",
                "default",
                *(
                    [
                        "--template",
                        "task_completes",
                        "--language",
                        "en_US",
                        "--template-text",
                        "Task {{1}} is {{2}}",
                    ]
                    if command == "send-template"
                    else []
                ),
                "--to",
                "+19253858017",
            ],
            input_fn=lambda _: next(answers),
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 0
    )

    assert expected_guidance in "\n".join(output).lower()


def test_standalone_status_uses_explicit_message_kind_error_guidance(
    configured_path,
    fake_gateway,
):
    fake_gateway.next_status = {
        "message_uuid": "u1",
        "message_type": "whatsapp",
        "message_state": "failed",
        "error_code": "350",
        "delivered": False,
    }
    output = []

    assert (
        main(
            [
                "status",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--message-uuid",
                "u1",
                "--message-kind",
                "template",
            ],
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 0
    )

    assert "parameter" in "\n".join(output).lower()


@pytest.mark.parametrize(
    "argv",
    [
        ["template", "list"],
        ["template", "show", "--name", "task_completes"],
        ["template", "search", "--query", "task"],
        ["template", "inspect-text", "--text", "Task {{1}}"],
        ["template", "sync"],
    ],
)
def test_read_only_template_subcommands_are_registered(argv):
    parsed = build_parser().parse_args(argv)
    assert parsed.command == "template"


def test_template_sync_persists_remote_catalog(
    configured_waba_path,
    fake_gateway,
):
    fake_gateway.remote_templates = {
        "task_completes": task_template(
            language="en",
            status="APPROVED",
        )
    }

    assert (
        main(
            [
                "template",
                "sync",
                "--config",
                str(configured_waba_path),
                "--profile",
                "default",
            ],
            gateway_factory=lambda _: fake_gateway,
            output_fn=lambda _: None,
        )
        == 0
    )

    profile = load_store(configured_waba_path)["profiles"]["default"]
    assert profile["templates"] == fake_gateway.remote_templates


def test_template_sync_preserves_stale_legacy_default_while_replacing_templates(
    configured_waba_path,
    fake_gateway,
):
    fake_gateway.remote_templates = {}
    before = load_store(configured_waba_path)["profiles"]["default"]
    assert before["default_template"] == "task_completes"

    assert (
        main(
            [
                "template",
                "sync",
                "--config",
                str(configured_waba_path),
                "--profile",
                "default",
            ],
            gateway_factory=lambda _: fake_gateway,
            output_fn=lambda _: None,
        )
        == 0
    )

    after = load_store(configured_waba_path)["profiles"]["default"]
    assert after == {**before, "templates": {}}
    assert after["default_template"] == before["default_template"]


def test_template_sync_requires_waba_before_creating_gateway(
    configured_path,
):
    gateway_calls = []
    output = []

    assert (
        main(
            [
                "template",
                "sync",
                "--config",
                str(configured_path),
                "--profile",
                "default",
            ],
            gateway_factory=lambda profile: gateway_calls.append(profile),
            output_fn=output.append,
        )
        == 1
    )

    assert gateway_calls == []
    assert any("WABA ID" in line for line in output)


def test_gateway_error_is_reported_once_without_retry(
    configured_path,
    fake_gateway,
):
    fake_gateway.send_error = TimeoutError("ambiguous transport failure")
    output = []
    answers = iter(["Hello", "yes"])

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
            ],
            input_fn=lambda _: next(answers),
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 1
    )

    assert fake_gateway.send_attempts == 1
    assert len([line for line in output if "ambiguous" in line]) == 1
    rendered = "\n".join(output).lower()
    assert "do not automatically retry" in rendered
    assert "reconcile" in rendered


def test_template_create_exception_has_no_retry_reconcile_guidance(
    configured_path,
    fake_gateway,
):
    fake_gateway.send_error = ConnectionError("connection reset")
    output = []
    answers = iter(["Task", "Failed", "yes"])

    assert (
        main(
            [
                "send-template",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--template",
                "task_completes",
                "--language",
                "en_US",
                "--template-text",
                "Task {{1}} is {{2}}",
                "--to",
                "+19253858017",
            ],
            input_fn=lambda _: next(answers),
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 1
    )

    assert fake_gateway.send_attempts == 1
    rendered = "\n".join(output).lower()
    assert "template send result is ambiguous" in rendered
    assert "do not automatically retry" in rendered
    assert "reconcile" in rendered


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        (task_template(status="PENDING"), "APPROVED"),
        (
            {
                **task_template(),
                "components": [
                    {"type": "HEADER", "format": "IMAGE"},
                    {
                        "type": "BODY",
                        "text": "Task {{1}} result {{2}}",
                    },
                ],
            },
            "unsupported dynamic template components",
        ),
    ],
)
def test_template_deterministic_preflight_fails_before_confirmation(
    configured_path,
    template,
    expected,
):
    profile = configured_profile()
    profile["templates"]["task_completes"] = template
    save_store(
        {"version": 1, "profiles": {"default": profile}},
        configured_path,
    )
    gateway_calls = []
    output = []

    assert (
        main(
            [
                "send-template",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--template",
                "task_completes",
                "--to",
                "+19253858017",
            ],
            input_fn=lambda _: (_ for _ in ()).throw(
                AssertionError("deterministic preflight must not prompt")
            ),
            gateway_factory=lambda profile: gateway_calls.append(profile),
            output_fn=output.append,
        )
        == 1
    )

    rendered = "\n".join(output)
    assert expected in rendered
    assert "ambiguous" not in rendered.lower()
    assert gateway_calls == []


def test_invalid_stored_profile_blocks_gateway_and_keeps_token_redacted(
    tmp_path,
):
    path = profile_path(tmp_path)
    profile = configured_profile()
    profile["sender"] = "not-e164"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"version": 1, "profiles": {"default": profile}}),
        encoding="utf-8",
    )
    gateway_calls = []
    output = []

    assert (
        main(
            [
                "send-text",
                "--config",
                str(path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--text",
                "Hello",
            ],
            input_fn=lambda _: "yes",
            gateway_factory=lambda profile: gateway_calls.append(profile),
            output_fn=output.append,
        )
        == 1
    )

    assert gateway_calls == []
    rendered = "\n".join(output)
    assert "sender" in rendered
    assert "secret-token" not in rendered


def test_exception_output_redacts_stored_token(
    configured_path,
    fake_gateway,
):
    fake_gateway.send_error = RuntimeError("Authorization failed for secret-token")
    output = []
    answers = iter(["Hello", "yes"])

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
            ],
            input_fn=lambda _: next(answers),
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 1
    )

    rendered = "\n".join(output)
    assert "secret-token" not in rendered
    assert "***REDACTED***" in rendered


@pytest.mark.parametrize(
    ("error_text", "secret"),
    [
        (
            "request failed: headers={'Authorization': 'Basic bWFzc2l2ZS1iYXNlNjQtc2VjcmV0'}",
            "bWFzc2l2ZS1iYXNlNjQtc2VjcmV0",
        ),
        (
            "request failed: Authorization: Basic YW5vdGhlci1iYXNlNjQtc2VjcmV0",
            "YW5vdGhlci1iYXNlNjQtc2VjcmV0",
        ),
        (
            'request failed: headers={"Authorization": "Bearer header-token-secret"}',
            "header-token-secret",
        ),
        (
            "request failed with Basic YmFyZS1iYXNpYy1jcmVkZW50aWFs",
            "YmFyZS1iYXNpYy1jcmVkZW50aWFs",
        ),
    ],
)
def test_exception_output_redacts_authorization_header_values(
    configured_path,
    fake_gateway,
    error_text,
    secret,
):
    fake_gateway.send_error = RuntimeError(error_text)
    output = []

    assert (
        main(
            [
                "send-text",
                "--config",
                str(configured_path),
                "--profile",
                "default",
                "--to",
                "+19253858017",
                "--text",
                "Hello",
            ],
            input_fn=lambda _: "yes",
            gateway_factory=lambda _: fake_gateway,
            output_fn=output.append,
        )
        == 1
    )

    rendered = "\n".join(output)
    assert secret not in rendered
    assert "***REDACTED***" in rendered
