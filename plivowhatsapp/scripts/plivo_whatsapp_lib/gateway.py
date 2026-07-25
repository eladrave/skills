"""Plivo WhatsApp message operations and read-only WABA template access."""

from __future__ import annotations

import base64
import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import normalize_e164, validate_profile
from .templates import (
    normalize_template,
    validate_sendable_template,
    validate_values,
)

WABA_READ_TIMEOUT_SECONDS = 10
MAX_WABA_PAGES = 100
MAX_WABA_OBJECTS = 1000
MAX_WABA_REDIRECTS = 5
_REDIRECT_CODES = {301, 302, 303, 307, 308}


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _default_opener(request: Request, *, timeout: int):
    return build_opener(_NoRedirectHandler()).open(
        request,
        timeout=timeout,
    )


def _default_client_factory(auth_id: str, auth_token: str):
    import plivo

    return plivo.RestClient(auth_id, auth_token)


def _build_template(*, name: str, language: str, components: list[dict]):
    from plivo.utils.template import Template

    return Template(
        name=name,
        language=language,
        components=components,
    )


def _field(value: object, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _message_uuids(response: object) -> list[str]:
    message_uuids = _field(response, "message_uuid")
    if message_uuids is None:
        message_uuids = _field(response, "message_uuids")
    if isinstance(message_uuids, str):
        message_uuids = [message_uuids]
    if not isinstance(message_uuids, (list, tuple)) or not message_uuids:
        raise RuntimeError(
            "Ambiguous send result: Plivo returned no valid message UUIDs. "
            "Do not automatically retry; reconcile the Plivo message record "
            "first."
        )
    if not all(
        isinstance(message_uuid, str) and message_uuid.strip()
        for message_uuid in message_uuids
    ):
        raise RuntimeError(
            "Ambiguous send result: Plivo returned malformed message UUIDs. "
            "Do not automatically retry; reconcile the Plivo message record "
            "first."
        )
    return [message_uuid.strip() for message_uuid in message_uuids]


def explain_error(code: str, message_kind: str) -> str:
    """Return message-kind-specific guidance without exposing credentials."""
    normalized_code = str(code)
    normalized_kind = message_kind.lower()

    if normalized_code == "340":
        if normalized_kind == "template":
            return (
                "Plivo error 340: check that the template is APPROVED and "
                "that its exact name and language are being used."
            )
        if normalized_kind == "freeform":
            return (
                "Plivo error 340: check that the destination has an eligible "
                "open WhatsApp conversation for a freeform message."
            )
    if normalized_code == "350" and normalized_kind == "template":
        return (
            "Plivo error 350: verify every template parameter's number, "
            "order, name, type, and formatting."
        )
    return f"Plivo error {normalized_code}: inspect the Plivo message record."


class PlivoGateway:
    """Perform exactly one Plivo operation for each requested gateway call."""

    def __init__(
        self,
        profile: dict,
        client_factory: Callable | None = None,
        opener: Callable | None = None,
    ):
        validate_profile(profile)
        self._profile = dict(profile)
        self._client_factory = client_factory or _default_client_factory
        self._opener = opener or _default_opener
        self._client_instance = None

    def _client(self):
        if self._client_instance is None:
            self._client_instance = self._client_factory(
                self._profile["auth_id"],
                self._profile["auth_token"],
            )
        return self._client_instance

    def send_text(self, dst: str, text: str) -> list[str]:
        response = self._client().messages.create(
            src=self._profile["sender"],
            dst=normalize_e164(dst),
            type_="whatsapp",
            text=text,
        )
        return _message_uuids(response)

    def send_template(
        self,
        dst: str,
        template: dict,
        values: dict[str, str],
    ) -> list[str]:
        validate_sendable_template(template)
        parameters = validate_values(template, values)
        plivo_template = _build_template(
            name=template["name"],
            language=template["language"],
            components=[{"type": "body", "parameters": parameters}],
        )
        response = self._client().messages.create(
            src=self._profile["sender"],
            dst=normalize_e164(dst),
            type_="whatsapp",
            template=plivo_template,
        )
        return _message_uuids(response)

    def message_status(self, message_uuid: str) -> dict:
        status = self._client().messages.get(message_uuid)
        message_state = _field(status, "message_state")
        return {
            "message_uuid": str(
                _field(status, "message_uuid", message_uuid)
            ),
            "message_type": _field(status, "message_type"),
            "message_state": message_state,
            "error_code": _field(status, "error_code"),
            "delivered": message_state in {"delivered", "read"},
        }

    def _waba_base_url(self) -> str:
        waba_id = self._profile.get("waba_id")
        if not waba_id:
            raise ValueError("WABA ID is required for remote template reads")
        auth_id = quote(str(self._profile["auth_id"]), safe="")
        encoded_waba_id = quote(str(waba_id), safe="")
        return (
            f"https://api.plivo.com/v1/Account/{auth_id}/"
            f"WhatsApp/Template/{encoded_waba_id}/"
        )

    def _validate_waba_url(self, url: str) -> None:
        parsed_url = urlsplit(url)
        expected_path_prefix = urlsplit(self._waba_base_url()).path
        try:
            port = parsed_url.port
        except ValueError:
            raise ValueError("refusing untrusted Plivo WABA URL") from None
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != "api.plivo.com"
            or port not in (None, 443)
            or parsed_url.username is not None
            or parsed_url.password is not None
            or not parsed_url.path.startswith(expected_path_prefix)
        ):
            raise ValueError("refusing untrusted Plivo WABA URL")

    def _read_json(self, url: str) -> object:
        credentials = (
            f"{self._profile['auth_id']}:{self._profile['auth_token']}"
        ).encode()
        authorization = base64.b64encode(credentials).decode("ascii")
        current_url = url
        redirects = 0

        while True:
            self._validate_waba_url(current_url)
            request = Request(
                current_url,
                headers={"Authorization": f"Basic {authorization}"},
                method="GET",
            )
            try:
                response = self._opener(
                    request,
                    timeout=WABA_READ_TIMEOUT_SECONDS,
                )
            except HTTPError as error:
                if error.code not in _REDIRECT_CODES:
                    raise
                location = error.headers.get("Location")
                if not location:
                    raise ValueError(
                        "Plivo WABA redirect is missing Location"
                    ) from None
                redirects += 1
                if redirects > MAX_WABA_REDIRECTS:
                    raise ValueError(
                        "Plivo WABA redirect limit exceeded"
                    ) from None
                current_url = urljoin(current_url, location)
                self._validate_waba_url(current_url)
                continue

            with response:
                return json.loads(response.read())

    def list_remote_templates(self) -> list[dict]:
        url = self._waba_base_url()
        templates: list[dict] = []
        visited_urls: set[str] = set()
        page_count = 0

        while url:
            if url in visited_urls:
                raise ValueError("remote template pagination cycle detected")
            if page_count >= MAX_WABA_PAGES:
                raise ValueError("remote template page limit exceeded")
            visited_urls.add(url)
            page_count += 1

            payload = self._read_json(url)
            if not isinstance(payload, Mapping):
                raise ValueError(
                    "remote template list response must be a mapping"
                )

            page = payload.get(
                "templates",
                payload.get("objects", payload.get("data", [])),
            )
            if not isinstance(page, list) or not all(
                isinstance(template, dict) for template in page
            ):
                raise ValueError(
                    "remote template list must contain dictionaries"
                )
            if len(templates) + len(page) > MAX_WABA_OBJECTS:
                raise ValueError("remote template object limit exceeded")
            templates.extend(page)

            meta = payload.get("meta", {})
            if not isinstance(meta, Mapping):
                raise ValueError(
                    "remote template pagination metadata must be a mapping"
                )
            next_url = meta.get("next")
            url = urljoin(url, next_url) if next_url else ""

        return templates

    def get_remote_template(self, template_id: str) -> dict:
        encoded_template_id = quote(str(template_id), safe="")
        payload = self._read_json(
            f"{self._waba_base_url()}{encoded_template_id}/"
        )
        if not isinstance(payload, dict):
            raise ValueError("remote template response must be a dictionary")
        return payload

    def sync_remote_templates(self) -> dict[str, dict]:
        synchronized = {}
        for summary in self.list_remote_templates():
            template_id = summary.get("template_id", summary.get("id"))
            if template_id is None:
                raise ValueError("remote template summary is missing its ID")
            template = normalize_template(
                self.get_remote_template(str(template_id)),
                source="waba",
            )
            synchronized[template["name"]] = template
        return synchronized
