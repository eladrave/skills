from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCE_TEXT = (SKILL_DIR / "references" / "plivo-python.md").read_text(
    encoding="utf-8"
)


def test_documentation_describes_only_the_read_only_template_surface() -> None:
    for forbidden in (
        "template add",
        "template remove",
        "template set-default",
    ):
        assert forbidden not in SKILL_TEXT
        assert forbidden not in REFERENCE_TEXT

    combined_text = SKILL_TEXT + REFERENCE_TEXT
    for required in (
        "template sync",
        "template search",
        "template inspect-text",
        "send-template",
        "send-text",
        "status --message-uuid",
        "~/.local/share/plivo-whatsapp/venv",
        "python -m pip install",
    ):
        assert required in combined_text


def test_reference_has_synchronized_and_ephemeral_template_examples() -> None:
    assert (
        "template sync --profile NAME" in REFERENCE_TEXT
        and "template search" in REFERENCE_TEXT
        and "--profile NAME --query task" in REFERENCE_TEXT
        and "template show" in REFERENCE_TEXT
        and "--profile NAME --name task_completes" in REFERENCE_TEXT
    )
    assert (
        "# No-WABA ephemeral send" in REFERENCE_TEXT
        and "--template task_completes --language en_US" in REFERENCE_TEXT
        and "--template-text 'The task {{1}} was completed. Result: {{2}}.'"
        in REFERENCE_TEXT
    )


def test_required_workflow_documents_the_complete_status_command() -> None:
    workflow_text = SKILL_TEXT.split("## Required Workflow", 1)[1].split(
        "## Template Discovery Quick Start",
        1,
    )[0]

    assert (
        "status --message-uuid UUID --message-kind freeform|template"
        in workflow_text
    )
