#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from plivo_whatsapp_lib.bootstrap import (
    ensure_sdk,
    sdk_available,
    venv_python,
)
from plivo_whatsapp_lib.cli import main


def _requires_gateway(argv: list[str]) -> bool:
    if "-h" in argv or "--help" in argv:
        return False
    if not argv:
        return False
    if argv[0] in {"send-text", "send-template", "status"}:
        return True
    return len(argv) > 1 and argv[:2] == ["template", "sync"]


def run(
    argv: list[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    sdk_available_fn: Callable[[], bool] = sdk_available,
    ensure_sdk_fn: Callable = ensure_sdk,
    venv_python_fn: Callable[[], Path] = venv_python,
    execv_fn: Callable[[str, list[str]], object] = os.execv,
    main_fn: Callable[[list[str]], int] = main,
    current_executable: Path | str | None = None,
) -> int:
    """Bootstrap gateway commands into the isolated SDK interpreter."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not _requires_gateway(arguments):
        return main_fn(arguments)

    target_python = venv_python_fn()
    if not sdk_available_fn():
        try:
            target_python = ensure_sdk_fn(
                confirm=lambda prompt: input_fn(f"{prompt} Type yes to confirm: ") == "yes",
            )
        except (PermissionError, RuntimeError) as error:
            output_fn(f"Error: {str(error).replace(chr(10), ' ')}")
            return 1

    active_python = Path(current_executable or sys.executable)
    if active_python.resolve() == Path(target_python).resolve():
        return main_fn(arguments)

    script = Path(__file__).resolve()
    executable = str(target_python)
    execv_fn(
        executable,
        [executable, str(script), *arguments],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
