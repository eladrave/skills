"""Template normalization, parameter validation, and immutable catalogs."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping


_PARAMETER_PATTERN = re.compile(
    r"\{\{([A-Za-z_][A-Za-z0-9_]*|[1-9][0-9]*)\}\}"
)
_LANGUAGE_PATTERN = re.compile(
    r"[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{1,8})*"
)
_ALLOWED_SOURCES = {"manual", "waba", "ephemeral"}
_ALLOWED_STATUSES = {
    "APPROVED",
    "UNKNOWN",
    "UNVERIFIED",
    "PENDING",
    "REJECTED",
    "PAUSED",
    "DISABLED",
}
_DYNAMIC_HEADER_FORMATS = {"DOCUMENT", "IMAGE", "VIDEO"}


def _component_type(component: Mapping) -> str:
    component_type = component.get("type", "")
    return component_type.upper() if isinstance(component_type, str) else ""


def _extract_body_parameter_keys(
    text: str,
    seen_keys: set[str],
) -> list[str]:
    keys = []
    position = 0

    while True:
        opening = text.find("{{", position)
        closing = text.find("}}", position)
        if closing != -1 and (opening == -1 or closing < opening):
            raise ValueError("unmatched closing BODY parameter marker")
        if opening == -1:
            return keys
        if closing == -1:
            raise ValueError("unmatched opening BODY parameter marker")

        match = _PARAMETER_PATTERN.match(text, opening)
        if match is None:
            raise ValueError("invalid BODY parameter marker")

        key = match.group(1)
        if key in seen_keys:
            raise ValueError(f"duplicate BODY parameter key: {key}")
        seen_keys.add(key)
        keys.append(key)
        position = match.end()


def extract_parameters(components: list[dict]) -> list[dict]:
    """Validate and extract body parameters in the order required for sending."""
    keys: list[str] = []
    kinds: set[str] = set()
    seen_keys: set[str] = set()

    for component in components:
        if _component_type(component) != "BODY":
            continue
        text = component.get("text", "")
        if not isinstance(text, str):
            raise ValueError("BODY component text must be a string")
        for key in _extract_body_parameter_keys(text, seen_keys):
            kind = "positional" if key.isdigit() else "named"
            kinds.add(kind)
            keys.append(key)

    if len(kinds) > 1:
        raise ValueError("cannot mix named and positional body parameters")

    if kinds == {"positional"}:
        keys.sort(key=int)
        expected_keys = [str(index) for index in range(1, len(keys) + 1)]
        if keys != expected_keys:
            raise ValueError(
                "positional template parameters must be contiguous from 1"
            )

    kind = next(iter(kinds), None)
    if kind is None:
        return []
    return [
        {"kind": kind, "key": key, "component": "body"}
        for key in keys
    ]


def normalize_template(raw: dict, source: str) -> dict:
    """Normalize a manual or WABA template without altering source data."""
    if source not in _ALLOWED_SOURCES:
        raise ValueError(f"unsupported template source: {source}")

    name = raw.get("name")
    language = raw.get("language")
    if not isinstance(name, str) or not name.strip() or name != name.strip():
        raise ValueError("template name must be a non-empty string")
    if (
        not isinstance(language, str)
        or _LANGUAGE_PATTERN.fullmatch(language) is None
    ):
        raise ValueError(
            "template language must be an exact Plivo language code "
            "(BCP-47 or provider locale)"
        )

    components = raw.get("components", [])
    if not isinstance(components, list) or not all(
        isinstance(component, dict) for component in components
    ):
        raise ValueError("template components must be a list of dictionaries")

    if source == "manual":
        raw_status = "UNKNOWN"
    elif source == "ephemeral":
        raw_status = "UNVERIFIED"
    else:
        raw_status = raw.get("status", "UNKNOWN")
    if not isinstance(raw_status, str):
        raise ValueError("template status must be a string")
    status = raw_status.upper()
    if status not in _ALLOWED_STATUSES:
        raise ValueError(f"unsupported template status: {raw_status}")

    template_id = (
        None
        if source == "ephemeral"
        else raw.get("template_id", raw.get("id"))
    )
    if template_id is not None:
        template_id = str(template_id)

    category = raw.get("category")
    if category is not None and not isinstance(category, str):
        raise ValueError("template category must be a string or None")
    quality_score = raw.get("quality_score")
    if quality_score is not None and not isinstance(quality_score, dict):
        raise ValueError("template quality_score must be a dictionary or None")

    normalized = {
        "template_id": template_id,
        "name": name,
        "language": language,
        "category": category,
        "status": status,
        "quality_score": copy.deepcopy(quality_score),
        "source": source,
        "components": copy.deepcopy(components),
        "parameters": extract_parameters(components),
    }
    validate_template(normalized)
    return normalized


def build_ephemeral_template(name: str, language: str, text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("template text must be a non-empty string")
    template = normalize_template(
        {
            "name": name,
            "language": language,
            "components": [{"type": "BODY", "text": text}],
        },
        source="ephemeral",
    )
    template["status"] = "UNVERIFIED"
    validate_template(template)
    return template


def search_templates(
    templates: Mapping[str, dict],
    query: str,
) -> dict[str, dict]:
    needle = query.strip().casefold()
    if not needle:
        raise ValueError("template search query must not be empty")
    matches = {}
    for name, template in templates.items():
        searchable = [name, template.get("language", "")]
        searchable.extend(
            component.get("text", "")
            for component in template.get("components", [])
            if isinstance(component, Mapping)
        )
        if any(needle in str(value).casefold() for value in searchable):
            matches[name] = copy.deepcopy(template)
    return matches


def validate_template(template: object) -> None:
    """Validate the complete normalized template schema."""
    if not isinstance(template, Mapping):
        raise ValueError("template must be a mapping")

    required = {
        "template_id",
        "name",
        "language",
        "category",
        "status",
        "quality_score",
        "source",
        "components",
        "parameters",
    }
    missing = sorted(required - set(template))
    if missing:
        raise ValueError(
            f"template is missing required fields: {', '.join(missing)}"
        )

    name = template["name"]
    if not isinstance(name, str) or not name.strip() or name != name.strip():
        raise ValueError("template name must be a non-empty string")

    language = template["language"]
    if (
        not isinstance(language, str)
        or _LANGUAGE_PATTERN.fullmatch(language) is None
    ):
        raise ValueError(
            "template language must be an exact Plivo language code "
            "(BCP-47 or provider locale)"
        )

    source = template["source"]
    if source not in _ALLOWED_SOURCES:
        raise ValueError(f"unsupported template source: {source}")

    status = template["status"]
    if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
        raise ValueError(f"unsupported template status: {status}")
    if source == "manual" and status != "UNKNOWN":
        raise ValueError("manual template status must be UNKNOWN")
    if source == "ephemeral" and status != "UNVERIFIED":
        raise ValueError("ephemeral template status must be UNVERIFIED")

    template_id = template["template_id"]
    if source == "waba":
        if (
            not isinstance(template_id, str)
            or not template_id.strip()
            or template_id != template_id.strip()
        ):
            raise ValueError(
                "synchronized template_id must be a non-empty string"
            )
    elif template_id is not None:
        raise ValueError(f"{source} template_id must be None")

    category = template["category"]
    if category is not None and (
        not isinstance(category, str) or not category.strip()
    ):
        raise ValueError("template category must be a string or None")

    quality_score = template["quality_score"]
    if quality_score is not None and not isinstance(quality_score, dict):
        raise ValueError(
            "template quality_score must be a dictionary or None"
        )

    components = template["components"]
    if not isinstance(components, list) or not all(
        isinstance(component, dict) for component in components
    ):
        raise ValueError(
            "template components must be a list of dictionaries"
        )
    for component in components:
        if not _component_type(component):
            raise ValueError(
                "every template component type must be a non-empty string"
            )

    parameters = template["parameters"]
    if not isinstance(parameters, list) or not all(
        isinstance(parameter, dict) for parameter in parameters
    ):
        raise ValueError(
            "template parameters must be a list of dictionaries"
        )
    expected_parameters = extract_parameters(components)
    if parameters != expected_parameters:
        raise ValueError(
            "template parameters must exactly match body components"
        )


def validate_values(
    template: dict,
    values: dict[str, str],
) -> list[dict]:
    """Validate exact template values and build Plivo SDK parameters."""
    validate_template(template)
    parameters = template.get("parameters", [])
    expected_keys = [parameter["key"] for parameter in parameters]
    expected = set(expected_keys)
    provided = set(values)

    missing = [key for key in expected_keys if key not in provided]
    if missing:
        raise ValueError(
            f"missing template parameter values: {', '.join(missing)}"
        )

    extra = sorted(provided - expected)
    if extra:
        raise ValueError(
            f"extra template parameter values: {', '.join(extra)}"
        )

    result = []
    for parameter in parameters:
        key = parameter["key"]
        value = values[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"template parameter {key} must be a non-empty string"
            )
        item = {"type": "text", "text": value}
        if parameter["kind"] == "named":
            item["parameter_name"] = key
        elif parameter["kind"] != "positional":
            raise ValueError(f"unsupported parameter kind: {parameter['kind']}")
        result.append(item)
    return result


def _contains_parameter(value: object) -> bool:
    if isinstance(value, str):
        return _PARAMETER_PATTERN.search(value) is not None
    if isinstance(value, Mapping):
        return any(_contains_parameter(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_parameter(item) for item in value)
    return False


def unsupported_dynamic_components(template: dict) -> list[str]:
    """List dynamic components not supported by the body-only send helper."""
    unsupported: list[str] = []

    for component in template.get("components", []):
        component_type = _component_type(component)
        if component_type == "HEADER":
            raw_format = component.get("format", "TEXT")
            header_format = (
                raw_format.upper() if isinstance(raw_format, str) else "UNKNOWN"
            )
            if (
                header_format in _DYNAMIC_HEADER_FORMATS
                or _contains_parameter(component)
            ):
                unsupported.append(f"HEADER:{header_format}")
        elif component_type == "BUTTONS":
            for button in component.get("buttons", []):
                if not isinstance(button, Mapping) or not _contains_parameter(button):
                    continue
                raw_button_type = button.get("type", "UNKNOWN")
                button_type = (
                    raw_button_type.upper()
                    if isinstance(raw_button_type, str)
                    else "UNKNOWN"
                )
                label = f"BUTTONS:{button_type}"
                if label not in unsupported:
                    unsupported.append(label)
        elif component_type == "CAROUSEL":
            unsupported.append("CAROUSEL")

    return unsupported


def validate_sendable_template(template: dict) -> None:
    """Reject deterministic template-send failures before confirmation."""
    validate_template(template)
    source = template.get("source")
    status = template.get("status")
    if source == "waba" and status != "APPROVED":
        raise ValueError(
            "synchronized WABA templates must have status APPROVED"
        )
    if source == "ephemeral" and status != "UNVERIFIED":
        raise ValueError("ephemeral templates must have status UNVERIFIED")
    if source == "manual":
        raise ValueError(
            "legacy manual templates cannot be sent; provide exact template "
            "text for an ephemeral send"
        )

    unsupported = unsupported_dynamic_components(template)
    if unsupported:
        raise ValueError(
            "unsupported dynamic template components: "
            + ", ".join(unsupported)
        )
