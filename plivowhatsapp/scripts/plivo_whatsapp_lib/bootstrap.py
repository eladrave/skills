"""Consent-gated bootstrap for the isolated Plivo SDK environment."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


def venv_path(home: Path | None = None) -> Path:
    base = home if home is not None else Path.home()
    return base / ".local" / "share" / "plivo-whatsapp" / "venv"


def venv_python(home: Path | None = None) -> Path:
    return venv_path(home) / "bin" / "python"


def _is_isolated_environment(home: Path | None = None) -> bool:
    environment = venv_path(home)
    return venv_python(home).exists() and (
        environment / "pyvenv.cfg"
    ).is_file()


def sdk_available(
    home: Path | None = None,
    runner: Callable = subprocess.run,
) -> bool:
    python = venv_python(home)
    if not _is_isolated_environment(home):
        return False

    try:
        runner(
            [str(python), "-c", "import plivo"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def _run_checked(
    category: str,
    command: Sequence[str],
    runner: Callable,
) -> None:
    try:
        runner(
            list(command),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"{category} failed with exit status {error.returncode}"
        ) from None
    except OSError:
        raise RuntimeError(f"{category} could not start") from None


def ensure_sdk(
    home: Path | None = None,
    confirm: Callable[[str], bool] | None = None,
    runner: Callable = subprocess.run,
) -> Path:
    python = venv_python(home)
    if sdk_available(home, runner=runner):
        return python

    prompt = (
        "Install the official Plivo Python SDK in the isolated environment "
        f"at {venv_path(home)}?"
    )
    if confirm is None or not confirm(prompt):
        raise PermissionError("Plivo SDK installation declined")

    environment = venv_path(home)
    environment.parent.mkdir(parents=True, exist_ok=True)
    if python.exists() and not _is_isolated_environment(home):
        raise RuntimeError(
            "refusing to install through an unverified isolated environment"
        )
    if not python.exists():
        _run_checked(
            "virtual environment creation",
            [sys.executable, "-m", "venv", str(environment)],
            runner,
        )
        if not _is_isolated_environment(home):
            raise RuntimeError(
                "virtual environment creation did not produce a verified "
                "isolated environment"
            )

    _run_checked(
        "Plivo SDK installation",
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "plivo",
        ],
        runner,
    )
    _run_checked(
        "Plivo SDK import check",
        [str(python), "-c", "import plivo"],
        runner,
    )
    return python
