import base64
import json
import sys
import types
from urllib.error import HTTPError

import pytest

from plivo_whatsapp_lib.gateway import PlivoGateway, explain_error


class FakeTemplate:
    def __init__(self, *, name, language, components):
        self.name = name
        self.language = language
        self.components = components


class FakeResponse:
    def __init__(self, message_uuids):
        self.message_uuid = message_uuids


class FakeMessages:
    def __init__(self):
        self.create_calls = []
        self.get_calls = []
        self.create_response = FakeResponse(["uuid-1"])
        self.status = {
            "message_uuid": "u",
            "message_type": "whatsapp",
            "message_state": "queued",
            "error_code": "",
        }
        self.create_error = None

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.create_error is not None:
            raise self.create_error
        return self.create_response

    def get(self, message_uuid):
        self.get_calls.append(message_uuid)
        return self.status


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


class JsonResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return self._body


class FakeOpener:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.timeouts = []

    def __call__(self, request, *, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        return JsonResponse(self._responses.pop(0))


@pytest.fixture
def fake_client():
    return FakeClient()


@pytest.fixture
def profile():
    return {
        "auth_id": "MAABCDEFGHIJKLMNOPQR",
        "auth_token": "secret-token",
        "sender": "+19543525707",
        "waba_id": "123456789012345",
        "templates": {},
        "default_template": None,
    }


@pytest.fixture(autouse=True)
def fake_plivo_template(monkeypatch):
    plivo_module = types.ModuleType("plivo")
    utils_module = types.ModuleType("plivo.utils")
    template_module = types.ModuleType("plivo.utils.template")
    template_module.Template = FakeTemplate
    plivo_module.utils = utils_module
    utils_module.template = template_module
    monkeypatch.setitem(sys.modules, "plivo", plivo_module)
    monkeypatch.setitem(sys.modules, "plivo.utils", utils_module)
    monkeypatch.setitem(sys.modules, "plivo.utils.template", template_module)


def task_template(*, language="en", status="APPROVED", source="waba"):
    return {
        "template_id": "tpl-1" if source == "waba" else None,
        "name": "task_completes",
        "language": language,
        "category": "UTILITY",
        "status": status,
        "quality_score": {"score": "GREEN"},
        "source": source,
        "components": [
            {
                "type": "BODY",
                "text": "Task {{1}} is {{2}}",
            }
        ],
        "parameters": [
            {"kind": "positional", "key": "1", "component": "body"},
            {"kind": "positional", "key": "2", "component": "body"},
        ],
    }


def values():
    return {"1": "Newsletter setup", "2": "Completed"}


def test_send_text_calls_plivo_once(fake_client, profile):
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    assert gateway.send_text("+1 (925) 385-8017", "Hello") == ["uuid-1"]
    assert fake_client.messages.create_calls == [
        {
            "src": "+19543525707",
            "dst": "+19253858017",
            "type_": "whatsapp",
            "text": "Hello",
        }
    ]


def test_send_text_does_not_retry_an_ambiguous_failure(fake_client, profile):
    fake_client.messages.create_error = RuntimeError("ambiguous failure")
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    with pytest.raises(RuntimeError, match="ambiguous"):
        gateway.send_text("+19253858017", "Hello")

    assert len(fake_client.messages.create_calls) == 1


def test_send_text_returns_every_valid_response_uuid(fake_client, profile):
    fake_client.messages.create_response = FakeResponse(["uuid-1", "uuid-2"])
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    assert gateway.send_text("+19253858017", "Hello") == ["uuid-1", "uuid-2"]


@pytest.mark.parametrize(
    "response",
    [
        object(),
        FakeResponse([]),
        FakeResponse(""),
        FakeResponse(["  "]),
        FakeResponse([123]),
        types.SimpleNamespace(message_uuid={"uuid": "uuid-1"}),
    ],
    ids=[
        "missing",
        "empty-list",
        "empty-string",
        "blank-string",
        "non-string-item",
        "malformed-mapping",
    ],
)
def test_send_text_rejects_ambiguous_uuid_responses(
    fake_client,
    profile,
    response,
):
    fake_client.messages.create_response = response
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    with pytest.raises(
        RuntimeError,
        match=r"(?i)ambiguous.*do not automatically retry.*reconcile",
    ):
        gateway.send_text("+19253858017", "Hello")

    assert len(fake_client.messages.create_calls) == 1


def test_send_template_uses_exact_name_language_and_parameters(
    fake_client, profile
):
    fake_client.messages.create_response = FakeResponse(["uuid-template"])
    template = task_template(language="en")
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    assert gateway.send_template(
        "+19253858017",
        template,
        values(),
    ) == ["uuid-template"]
    assert len(fake_client.messages.create_calls) == 1
    sent = fake_client.messages.create_calls[0]
    assert sent["src"] == "+19543525707"
    assert sent["dst"] == "+19253858017"
    assert sent["type_"] == "whatsapp"
    assert sent["template"].name == "task_completes"
    assert sent["template"].language == "en"
    assert sent["template"].components == [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "Newsletter setup"},
                {"type": "text", "text": "Completed"},
            ],
        }
    ]


def test_send_template_rejects_nonapproved_synced_template(profile):
    gateway = PlivoGateway(
        profile,
        client_factory=lambda *_: pytest.fail("no client"),
    )

    with pytest.raises(ValueError, match="APPROVED"):
        gateway.send_template(
            "+19253858017",
            task_template(status="PENDING"),
            values(),
        )


def test_send_template_does_not_retry_an_ambiguous_failure(
    fake_client, profile
):
    fake_client.messages.create_error = RuntimeError("ambiguous failure")
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    with pytest.raises(RuntimeError, match="ambiguous"):
        gateway.send_template(
            "+19253858017",
            task_template(),
            values(),
        )

    assert len(fake_client.messages.create_calls) == 1


def test_send_template_allows_ephemeral_template_with_unverified_status(
    fake_client,
    profile,
):
    fake_client.messages.create_response = FakeResponse("uuid-ephemeral")
    ephemeral = task_template(status="UNVERIFIED", source="ephemeral")
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    assert gateway.send_template(
        "+19253858017",
        ephemeral,
        values(),
    ) == ["uuid-ephemeral"]


def test_send_template_rejects_legacy_manual_template_before_sdk_call(
    profile,
):
    manual = task_template(status="UNKNOWN", source="manual")
    gateway = PlivoGateway(
        profile,
        client_factory=lambda *_: pytest.fail("no client"),
    )

    with pytest.raises(ValueError, match="legacy manual templates"):
        gateway.send_template("+19253858017", manual, values())


def test_send_template_rejects_unsupported_dynamic_components(
    fake_client, profile
):
    template = task_template()
    template["components"].append({"type": "HEADER", "format": "IMAGE"})
    gateway = PlivoGateway(profile, client_factory=lambda *_: fake_client)

    with pytest.raises(ValueError, match="HEADER:IMAGE"):
        gateway.send_template("+19253858017", template, values())

    assert fake_client.messages.create_calls == []


def test_message_status_does_not_map_queued_to_delivered(fake_client, profile):
    fake_client.messages.status = {
        "message_uuid": "u",
        "message_type": "whatsapp",
        "message_state": "queued",
        "error_code": "",
    }

    result = PlivoGateway(
        profile,
        client_factory=lambda *_: fake_client,
    ).message_status("u")

    assert result == {
        "message_uuid": "u",
        "message_type": "whatsapp",
        "message_state": "queued",
        "error_code": "",
        "delivered": False,
    }
    assert fake_client.messages.get_calls == ["u"]


@pytest.mark.parametrize("state", ["delivered", "read"])
def test_message_status_maps_only_delivered_and_read_to_delivered(
    fake_client, profile, state
):
    fake_client.messages.status = types.SimpleNamespace(
        message_uuid="u",
        message_type="whatsapp",
        message_state=state,
        error_code=None,
    )

    result = PlivoGateway(
        profile,
        client_factory=lambda *_: fake_client,
    ).message_status("u")

    assert result["delivered"] is True


@pytest.mark.parametrize("state", ["sent", "failed", "undelivered"])
def test_message_status_keeps_other_states_not_delivered(
    fake_client, profile, state
):
    fake_client.messages.status["message_state"] = state

    result = PlivoGateway(
        profile,
        client_factory=lambda *_: fake_client,
    ).message_status("u")

    assert result["message_state"] == state
    assert result["delivered"] is False


def test_explain_error_distinguishes_340_and_350():
    assert "language" in explain_error("340", "template").lower()
    assert "conversation" in explain_error("340", "freeform").lower()
    assert "parameter" in explain_error("350", "template").lower()
    assert "999" in explain_error("999", "freeform")


def test_list_remote_templates_follows_pagination_with_basic_auth(
    profile, capsys
):
    opener = FakeOpener(
        [
            {
                "templates": [{"id": "tpl-1", "name": "first"}],
                "meta": {"next": "?limit=1&offset=1"},
            },
            {
                "templates": [{"id": "tpl-2", "name": "second"}],
                "meta": {"next": None},
            },
        ]
    )

    result = PlivoGateway(profile, opener=opener).list_remote_templates()

    assert result == [
        {"id": "tpl-1", "name": "first"},
        {"id": "tpl-2", "name": "second"},
    ]
    assert [request.get_method() for request in opener.requests] == ["GET", "GET"]
    assert opener.requests[0].full_url == (
        "https://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
        "WhatsApp/Template/123456789012345/"
    )
    assert opener.requests[1].full_url.endswith("?limit=1&offset=1")
    expected_auth = "Basic " + base64.b64encode(
        b"MAABCDEFGHIJKLMNOPQR:secret-token"
    ).decode("ascii")
    assert [
        request.get_header("Authorization") for request in opener.requests
    ] == [expected_auth, expected_auth]
    assert "secret-token" not in json.dumps(result)
    assert capsys.readouterr() == ("", "")
    assert opener.timeouts == [10, 10]


def test_waba_read_forwards_timeout_and_propagates_timeout(profile):
    class TimingOutOpener:
        def __init__(self):
            self.timeouts = []

        def __call__(self, request, *, timeout=None):
            self.timeouts.append(timeout)
            raise TimeoutError("WABA read timed out")

    opener = TimingOutOpener()

    with pytest.raises(TimeoutError, match="timed out"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert opener.timeouts == [10]


def test_waba_redirect_rejects_cross_origin_before_resending_auth(profile):
    class RedirectingOpener:
        def __init__(self):
            self.requests = []

        def __call__(self, request, *, timeout=None):
            self.requests.append(request)
            raise HTTPError(
                request.full_url,
                302,
                "Found",
                {"Location": "https://attacker.example/collect"},
                None,
            )

    opener = RedirectingOpener()

    with pytest.raises(ValueError, match="untrusted Plivo WABA URL"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 1
    assert opener.requests[0].full_url.startswith("https://api.plivo.com/")


def test_waba_read_rejects_non_default_https_port_before_auth(profile):
    opener = FakeOpener([{"templates": [], "meta": {"next": None}}])
    gateway = PlivoGateway(profile, opener=opener)

    with pytest.raises(ValueError, match="untrusted Plivo WABA URL"):
        gateway._read_json(
            "https://api.plivo.com:444/v1/Account/"
            "MAABCDEFGHIJKLMNOPQR/WhatsApp/Template/123456789012345/"
        )

    assert opener.requests == []


def test_waba_redirect_rejects_non_default_https_port_before_resending_auth(
    profile,
):
    class RedirectingOpener:
        def __init__(self):
            self.requests = []

        def __call__(self, request, *, timeout=None):
            self.requests.append(request)
            raise HTTPError(
                request.full_url,
                302,
                "Found",
                {
                    "Location": (
                        "https://api.plivo.com:444/v1/Account/"
                        "MAABCDEFGHIJKLMNOPQR/WhatsApp/Template/"
                        "123456789012345/"
                    )
                },
                None,
            )

    opener = RedirectingOpener()

    with pytest.raises(ValueError, match="untrusted Plivo WABA URL"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 1


def test_list_remote_templates_rejects_pagination_cycle(profile):
    opener = FakeOpener(
        [
            {
                "templates": [{"id": "tpl-1"}],
                "meta": {"next": "?offset=1"},
            },
            {
                "templates": [{"id": "tpl-2"}],
                "meta": {"next": "?offset=1"},
            },
        ]
    )

    with pytest.raises(ValueError, match="pagination cycle"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 2


def test_list_remote_templates_enforces_page_limit(profile):
    responses = [
        {
            "templates": [],
            "meta": {"next": f"?page={page + 1}"},
        }
        for page in range(100)
    ]
    opener = FakeOpener(responses)

    with pytest.raises(ValueError, match="page limit"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 100


def test_list_remote_templates_enforces_object_limit(profile):
    opener = FakeOpener(
        [
            {
                "templates": [{"id": f"tpl-{index}"} for index in range(1001)],
                "meta": {"next": None},
            }
        ]
    )

    with pytest.raises(ValueError, match="object limit"):
        PlivoGateway(profile, opener=opener).list_remote_templates()


def test_list_remote_templates_rejects_hostile_pagination_before_opening(
    profile,
):
    opener = FakeOpener(
        [
            {
                "templates": [{"id": "tpl-1", "name": "first"}],
                "meta": {"next": "https://attacker.example/steal"},
            },
            {
                "templates": [],
                "meta": {"next": None},
            },
        ]
    )

    with pytest.raises(ValueError, match="Plivo WABA URL"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 1
    assert opener.requests[0].full_url == (
        "https://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
        "WhatsApp/Template/123456789012345/"
    )


@pytest.mark.parametrize(
    "next_url",
    [
        (
            "http://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
            "WhatsApp/Template/123456789012345/?offset=1"
        ),
        (
            "https://user@api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
            "WhatsApp/Template/123456789012345/?offset=1"
        ),
        (
            "https://api.plivo.com/v1/Account/MAQRSTUVWXYZABCDEFGH/"
            "WhatsApp/Template/123456789012345/?offset=1"
        ),
        (
            "https://api.plivo.com:444/v1/Account/MAABCDEFGHIJKLMNOPQR/"
            "WhatsApp/Template/123456789012345/?offset=1"
        ),
        (
            "https://api.plivo.com:notaport/v1/Account/"
            "MAABCDEFGHIJKLMNOPQR/WhatsApp/Template/"
            "123456789012345/?offset=1"
        ),
    ],
)
def test_list_remote_templates_rejects_untrusted_pagination_components(
    profile, next_url
):
    opener = FakeOpener(
        [
            {
                "templates": [],
                "meta": {"next": next_url},
            },
            {
                "templates": [],
                "meta": {"next": None},
            },
        ]
    )

    with pytest.raises(ValueError, match="Plivo WABA URL"):
        PlivoGateway(profile, opener=opener).list_remote_templates()

    assert len(opener.requests) == 1


def test_get_remote_template_reads_exact_template_url(profile):
    opener = FakeOpener(
        [
            {
                "id": "tpl-1",
                "name": "task_completes",
                "language": "en-US",
                "status": "APPROVED",
                "components": [],
            }
        ]
    )

    result = PlivoGateway(profile, opener=opener).get_remote_template("tpl-1")

    assert result["name"] == "task_completes"
    assert opener.requests[0].full_url == (
        "https://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
        "WhatsApp/Template/123456789012345/tpl-1/"
    )


@pytest.mark.parametrize(
    "operation",
    [
        lambda gateway: gateway.list_remote_templates(),
        lambda gateway: gateway.get_remote_template("tpl-1"),
        lambda gateway: gateway.sync_remote_templates(),
    ],
)
def test_remote_template_reads_require_waba_before_opening(
    profile, operation
):
    profile["waba_id"] = None
    opener = FakeOpener([])

    with pytest.raises(ValueError, match="WABA"):
        operation(PlivoGateway(profile, opener=opener))

    assert opener.requests == []


def test_sync_remote_templates_fetches_and_normalizes_every_full_template(
    profile,
):
    opener = FakeOpener(
        [
            {
                "templates": [
                    {"id": "tpl-1", "name": "task_completes"},
                    {"id": "tpl-2", "name": "welcome"},
                ],
                "meta": {"next": None},
            },
            {
                "id": "tpl-1",
                "name": "task_completes",
                "language": "en-US",
                "category": "UTILITY",
                "status": "APPROVED",
                "quality_score": {"score": "GREEN"},
                "components": [
                    {"type": "BODY", "text": "Task {{1}} is {{2}}"}
                ],
            },
            {
                "id": "tpl-2",
                "name": "welcome",
                "language": "fr",
                "category": "MARKETING",
                "status": "PENDING",
                "components": [
                    {"type": "BODY", "text": "Bonjour {{customer_name}}"}
                ],
            },
        ]
    )

    result = PlivoGateway(profile, opener=opener).sync_remote_templates()

    assert list(result) == ["task_completes", "welcome"]
    assert result["task_completes"] == {
        "template_id": "tpl-1",
        "name": "task_completes",
        "language": "en-US",
        "category": "UTILITY",
        "status": "APPROVED",
        "quality_score": {"score": "GREEN"},
        "source": "waba",
        "components": [{"type": "BODY", "text": "Task {{1}} is {{2}}"}],
        "parameters": [
            {"kind": "positional", "key": "1", "component": "body"},
            {"kind": "positional", "key": "2", "component": "body"},
        ],
    }
    assert result["welcome"]["parameters"] == [
        {"kind": "named", "key": "customer_name", "component": "body"}
    ]
    assert [request.full_url for request in opener.requests[1:]] == [
        (
            "https://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
            "WhatsApp/Template/123456789012345/tpl-1/"
        ),
        (
            "https://api.plivo.com/v1/Account/MAABCDEFGHIJKLMNOPQR/"
            "WhatsApp/Template/123456789012345/tpl-2/"
        ),
    ]
