import pytest

from plivo_whatsapp_lib.templates import (
    build_ephemeral_template,
    extract_parameters,
    normalize_template,
    search_templates,
    unsupported_dynamic_components,
    validate_sendable_template,
    validate_values,
)


def manual_template(name, parameter_keys, *, kind="positional"):
    body = " ".join(f"{{{{{key}}}}}" for key in parameter_keys)
    return {
        "template_id": None,
        "name": name,
        "language": "en",
        "category": None,
        "status": "UNKNOWN",
        "quality_score": None,
        "source": "manual",
        "components": [{"type": "BODY", "text": body}] if body else [],
        "parameters": [
            {"kind": kind, "key": key, "component": "body"}
            for key in parameter_keys
        ],
    }


def task_template():
    template = manual_template("task_completes", ["1", "2"])
    template["components"] = [
        {
            "type": "BODY",
            "text": "The task {{1}} was completed. The result is {{2}}.",
        }
    ]
    return template


def balance_template():
    template = manual_template(
        "balance_update",
        ["customer_name", "balance"],
        kind="named",
    )
    template["components"] = [
        {
            "type": "BODY",
            "text": "Hello {{customer_name}}, balance {{balance}}.",
        }
    ]
    return template


def test_build_ephemeral_template_infers_positional_parameters():
    template = build_ephemeral_template(
        "task_completes",
        "en_US",
        "The task {{1}} was completed. The result is {{2}}.",
    )
    assert template["source"] == "ephemeral"
    assert template["status"] == "UNVERIFIED"
    assert [item["key"] for item in template["parameters"]] == ["1", "2"]


def test_build_ephemeral_template_infers_named_parameters():
    template = build_ephemeral_template(
        "balance_update",
        "en-US",
        "Hello {{customer_name}}, balance {{balance}}.",
    )
    assert [item["key"] for item in template["parameters"]] == [
        "customer_name",
        "balance",
    ]


def test_build_ephemeral_template_rejects_duplicate_positional_parameters():
    with pytest.raises(ValueError, match=r"duplicate.*1"):
        build_ephemeral_template(
            "task_completes",
            "en_US",
            "Task {{1}} repeats {{1}}",
        )


def test_build_ephemeral_template_rejects_duplicate_named_parameters():
    with pytest.raises(ValueError, match=r"duplicate.*customer_name"):
        build_ephemeral_template(
            "balance_update",
            "en-US",
            "Hello {{customer_name}} again {{customer_name}}",
        )


@pytest.mark.parametrize(
    "text",
    [
        "Task {{0}}",
        "Task {{ customer }}",
    ],
)
def test_build_ephemeral_template_rejects_invalid_body_markers(text):
    with pytest.raises(ValueError, match=r"invalid.*marker"):
        build_ephemeral_template("task_completes", "en_US", text)


def test_build_ephemeral_template_rejects_unmatched_opening_marker():
    with pytest.raises(ValueError, match=r"unmatched.*opening"):
        build_ephemeral_template("task_completes", "en_US", "Task {{1")


def test_build_ephemeral_template_rejects_unmatched_closing_marker():
    with pytest.raises(ValueError, match=r"unmatched.*closing"):
        build_ephemeral_template("task_completes", "en_US", "Task 1}}")


def test_search_templates_matches_name_and_body_text():
    catalog = {
        "task_completes": task_template(),
        "balance_update": balance_template(),
    }
    assert list(search_templates(catalog, "completed")) == ["task_completes"]
    assert list(search_templates(catalog, "BALANCE")) == ["balance_update"]


def test_validate_sendable_template_accepts_unverified_ephemeral_template():
    template = build_ephemeral_template(
        "task_completes",
        "en_US",
        "Task {{1}} result {{2}}",
    )

    validate_sendable_template(template)


def test_validate_sendable_template_rejects_legacy_manual_template():
    with pytest.raises(
        ValueError,
        match=(
            "legacy manual templates cannot be sent; provide exact template "
            "text for an ephemeral send"
        ),
    ):
        validate_sendable_template(task_template())


def test_validate_sendable_template_rejects_wrong_ephemeral_status():
    template = build_ephemeral_template(
        "task_completes",
        "en_US",
        "Task {{1}} result {{2}}",
    )
    template["status"] = "APPROVED"

    with pytest.raises(ValueError, match="UNVERIFIED"):
        validate_sendable_template(template)


def test_extracts_positional_body_parameters_in_numeric_order():
    components = [{"type": "BODY", "text": "Task {{1}} result {{2}}"}]
    assert extract_parameters(components) == [
        {"kind": "positional", "key": "1", "component": "body"},
        {"kind": "positional", "key": "2", "component": "body"},
    ]


def test_sorts_positional_body_parameters_by_number_not_text_order():
    components = [{"type": "BODY", "text": "{{3}} {{2}} {{1}}"}]
    assert [item["key"] for item in extract_parameters(components)] == [
        "1",
        "2",
        "3",
    ]


def test_rejects_gapped_positional_body_parameters():
    with pytest.raises(ValueError, match="contiguous.*1"):
        extract_parameters(
            [{"type": "BODY", "text": "Task {{1}} result {{3}}"}]
        )


def test_extracts_named_body_parameters_in_text_order():
    components = [
        {"type": "BODY", "text": "Hi {{customer_name}}, balance {{balance}}"}
    ]
    assert extract_parameters(components) == [
        {"kind": "named", "key": "customer_name", "component": "body"},
        {"kind": "named", "key": "balance", "component": "body"},
    ]


def test_rejects_mixed_named_and_positional_body_parameters():
    with pytest.raises(ValueError, match="mix"):
        extract_parameters([{"type": "BODY", "text": "{{1}} {{customer}}"}])


def test_validate_values_rejects_missing_and_extra_keys():
    template = manual_template("task_completes", ["1", "2"])
    with pytest.raises(ValueError, match="missing.*2"):
        validate_values(template, {"1": "Task"})
    with pytest.raises(ValueError, match="extra.*3"):
        validate_values(template, {"1": "Task", "2": "Done", "3": "unused"})


def test_validate_values_builds_positional_parameters_in_template_order():
    template = manual_template("task_completes", ["1", "2"])
    assert validate_values(template, {"2": "Done", "1": "Task"}) == [
        {"type": "text", "text": "Task"},
        {"type": "text", "text": "Done"},
    ]


def test_validate_values_builds_named_parameters_with_names():
    template = manual_template(
        "balance_update",
        ["customer_name", "balance"],
        kind="named",
    )
    assert validate_values(
        template,
        {"balance": "$5.00", "customer_name": "Shelly"},
    ) == [
        {
            "type": "text",
            "text": "Shelly",
            "parameter_name": "customer_name",
        },
        {"type": "text", "text": "$5.00", "parameter_name": "balance"},
    ]


@pytest.mark.parametrize("value", ["", "   ", None, 42])
def test_validate_values_rejects_empty_or_non_string_values(value):
    template = manual_template("task_completes", ["1"])

    with pytest.raises(ValueError, match="non-empty string"):
        validate_values(template, {"1": value})


@pytest.mark.parametrize(
    "language",
    ["English", " en-US", "en-US ", "en--US", "en__US"],
)
def test_normalize_template_rejects_invalid_exact_language_format(language):
    with pytest.raises(ValueError, match="BCP-47"):
        normalize_template(
            {
                "name": "task_completes",
                "language": language,
                "components": [],
            },
            source="manual",
        )


@pytest.mark.parametrize("language", ["en_US", "en-US", "en"])
def test_normalize_template_preserves_authoritative_provider_language(language):
    result = normalize_template(
        {
            "name": "task_completes",
            "language": language,
            "components": [],
        },
        source="manual",
    )

    assert result["language"] == language


def test_normalize_template_preserves_exact_language_and_status():
    result = normalize_template(
        {
            "template_id": "123",
            "name": "task_completes",
            "language": "en",
            "status": "APPROVED",
            "category": "UTILITY",
            "components": [{"type": "BODY", "text": "{{1}} {{2}}"}],
        },
        source="waba",
    )
    assert result["language"] == "en"
    assert result["status"] == "APPROVED"
    assert [p["key"] for p in result["parameters"]] == ["1", "2"]


def test_normalize_manual_template_uses_unknown_status_and_preserves_components():
    raw = {
        "name": "task_completes",
        "language": "en-US",
        "status": "APPROVED",
        "components": [{"type": "body", "text": "Task {{1}}"}],
    }
    result = normalize_template(raw, source="manual")

    assert result == {
        "template_id": None,
        "name": "task_completes",
        "language": "en-US",
        "category": None,
        "status": "UNKNOWN",
        "quality_score": None,
        "source": "manual",
        "components": [{"type": "body", "text": "Task {{1}}"}],
        "parameters": [
            {"kind": "positional", "key": "1", "component": "body"}
        ],
    }
    assert result["components"] is not raw["components"]


def test_dynamic_media_and_buttons_are_reported_not_silently_dropped():
    template = {
        "components": [
            {"type": "HEADER", "format": "IMAGE"},
            {
                "type": "BUTTONS",
                "buttons": [{"type": "URL", "url": "https://x/{{1}}"}],
            },
        ]
    }
    assert unsupported_dynamic_components(template) == [
        "HEADER:IMAGE",
        "BUTTONS:URL",
    ]


def test_carousel_is_reported_as_an_unsupported_dynamic_component():
    template = {"components": [{"type": "CAROUSEL", "cards": []}]}
    assert unsupported_dynamic_components(template) == ["CAROUSEL"]
