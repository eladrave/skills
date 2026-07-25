import subprocess
import sys
from pathlib import Path

import pytest

from plivo_whatsapp_lib.bootstrap import (
    ensure_sdk,
    sdk_available,
    venv_path,
    venv_python,
)


class RecordingRunner:
    def __init__(self, python_path: Path):
        self.python_path = python_path
        self.config_path = python_path.parents[1] / "pyvenv.cfg"
        self.calls = []
        self.kwargs = []
        self.fail_on_call = None
        self.returncode = 1

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        self.kwargs.append(kwargs)
        if command[1:3] == ["-m", "venv"]:
            self.python_path.parent.mkdir(parents=True, exist_ok=True)
            self.python_path.touch()
            self.config_path.touch()
        if self.fail_on_call == len(self.calls):
            raise subprocess.CalledProcessError(
                self.returncode,
                command,
                output=b"sensitive output",
                stderr=b"SECRET_ENV=must-not-leak",
            )
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")


@pytest.fixture
def recording_runner(tmp_path):
    return RecordingRunner(venv_python(tmp_path))


def test_venv_path_is_isolated_from_project(tmp_path):
    assert venv_path(tmp_path) == (
        tmp_path / ".local" / "share" / "plivo-whatsapp" / "venv"
    )
    assert venv_python(tmp_path) == venv_path(tmp_path) / "bin" / "python"


def test_sdk_available_is_false_without_isolated_python(
    tmp_path, recording_runner
):
    assert sdk_available(tmp_path, runner=recording_runner) is False
    assert recording_runner.calls == []


def test_sdk_available_checks_import_in_isolated_python(
    tmp_path, recording_runner
):
    python = venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.touch()
    (venv_path(tmp_path) / "pyvenv.cfg").touch()

    assert sdk_available(tmp_path, runner=recording_runner) is True
    assert recording_runner.calls == [
        [str(python), "-c", "import plivo"],
    ]
    assert recording_runner.kwargs == [
        {"check": True, "capture_output": True},
    ]


def test_sdk_available_is_false_when_import_fails(
    tmp_path, recording_runner
):
    python = venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.touch()
    (venv_path(tmp_path) / "pyvenv.cfg").touch()
    recording_runner.fail_on_call = 1

    assert sdk_available(tmp_path, runner=recording_runner) is False


def test_sdk_available_does_not_execute_unverified_python(
    tmp_path, recording_runner
):
    python = venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.touch()

    assert sdk_available(tmp_path, runner=recording_runner) is False
    assert recording_runner.calls == []


def test_ensure_sdk_requires_confirmation(tmp_path, recording_runner):
    with pytest.raises(PermissionError, match="declined"):
        ensure_sdk(
            tmp_path,
            confirm=lambda _: False,
            runner=recording_runner,
        )
    assert recording_runner.calls == []
    assert not venv_path(tmp_path).parent.exists()


def test_ensure_sdk_fails_closed_without_confirmation_callback(
    tmp_path, recording_runner
):
    with pytest.raises(PermissionError, match="declined"):
        ensure_sdk(tmp_path, runner=recording_runner)
    assert recording_runner.calls == []
    assert not venv_path(tmp_path).parent.exists()


def test_ensure_sdk_creates_venv_and_installs_only_plivo(
    tmp_path, recording_runner
):
    python = ensure_sdk(
        tmp_path,
        confirm=lambda _: True,
        runner=recording_runner,
    )
    assert recording_runner.calls == [
        [sys.executable, "-m", "venv", str(venv_path(tmp_path))],
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "plivo",
        ],
        [str(python), "-c", "import plivo"],
    ]
    assert recording_runner.kwargs == [
        {"check": True, "capture_output": True},
        {"check": True, "capture_output": True},
        {"check": True, "capture_output": True},
    ]


def test_ensure_sdk_installs_into_existing_venv_without_recreating_it(
    tmp_path, recording_runner
):
    python = venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.touch()
    (venv_path(tmp_path) / "pyvenv.cfg").touch()
    recording_runner.fail_on_call = 1

    def fail_first_import_then_succeed(command, **kwargs):
        try:
            return recording_runner(command, **kwargs)
        finally:
            recording_runner.fail_on_call = None

    assert ensure_sdk(
        tmp_path,
        confirm=lambda _: True,
        runner=fail_first_import_then_succeed,
    ) == python
    assert recording_runner.calls == [
        [str(python), "-c", "import plivo"],
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "plivo",
        ],
        [str(python), "-c", "import plivo"],
    ]


def test_ensure_sdk_refuses_unverified_existing_python(
    tmp_path, recording_runner
):
    python = venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.touch()

    with pytest.raises(RuntimeError, match="isolated environment"):
        ensure_sdk(
            tmp_path,
            confirm=lambda _: True,
            runner=recording_runner,
        )

    assert recording_runner.calls == []


@pytest.mark.parametrize(
    ("fail_on_call", "category"),
    [
        (1, "virtual environment creation"),
        (2, "Plivo SDK installation"),
        (3, "Plivo SDK import check"),
    ],
)
def test_ensure_sdk_reports_safe_failure_category_and_status(
    tmp_path,
    recording_runner,
    fail_on_call,
    category,
):
    recording_runner.fail_on_call = fail_on_call
    recording_runner.returncode = 17

    with pytest.raises(RuntimeError) as error:
        ensure_sdk(
            tmp_path,
            confirm=lambda _: True,
            runner=recording_runner,
        )

    message = str(error.value)
    assert category in message
    assert "exit status 17" in message
    assert "SECRET_ENV" not in message
    assert "sensitive output" not in message


def test_ensure_sdk_sanitizes_process_launch_failures(tmp_path):
    def failing_runner(*_args, **_kwargs):
        raise OSError("SECRET_ENV=must-not-leak")

    with pytest.raises(RuntimeError) as error:
        ensure_sdk(
            tmp_path,
            confirm=lambda _: True,
            runner=failing_runner,
        )

    message = str(error.value)
    assert "virtual environment creation" in message
    assert "could not start" in message
    assert "SECRET_ENV" not in message
