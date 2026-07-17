#!/usr/bin/env python3
"""Validate a custom Codex agent TOML and linked Skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print("Python 3.11+ is required", file=sys.stderr)
    raise SystemExit(3)

VALID_SANDBOX = {"read-only", "workspace-write", "danger-full-access"}
BUILTINS = {"default", "worker", "explorer"}
SECRET_RE = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]{12,}|api[_-]?key\s*=\s*['\"][^'\"]+|password\s*=\s*['\"][^'\"]+)")
PLACEHOLDER_RE = re.compile(r"\[(?:specific|narrow|required|allowed|prohibited|authoritative|fallback|applicable|domain)[^\]]*\]|CURRENT_SUPPORTED_MODEL")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def validate(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    path = path.expanduser().resolve()
    if not path.is_file():
        return [Finding("ERROR", "not-found", f"Agent TOML not found: {path}")]
    try:
        raw = path.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        return [Finding("ERROR", "toml-invalid", str(exc))]

    for key in ("name", "description", "developer_instructions"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(Finding("ERROR", f"{key}-missing", f"Required non-empty string field: {key}"))

    name = data.get("name", "")
    if isinstance(name, str):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            findings.append(Finding("WARN", "name-format", "Agent name should be snake_case"))
        if name in BUILTINS:
            findings.append(Finding("ERROR", "builtin-collision", f"Agent name collides with built-in: {name}"))
        if path.stem != name:
            findings.append(Finding("WARN", "filename-mismatch", f"Filename '{path.stem}' differs from agent name '{name}'"))

    sandbox = data.get("sandbox_mode")
    if sandbox is not None and sandbox not in VALID_SANDBOX:
        findings.append(Finding("ERROR", "sandbox-invalid", f"Unsupported sandbox_mode: {sandbox}"))

    if "entrypoint" in data:
        findings.append(Finding("ERROR", "entrypoint-unsupported", "Custom-agent TOML does not support a Python entrypoint"))

    if SECRET_RE.search(raw):
        findings.append(Finding("ERROR", "possible-secret", "Possible embedded credential detected"))
    if PLACEHOLDER_RE.search(raw):
        findings.append(Finding("WARN", "placeholder", "Unresolved template placeholder detected"))

    skills = data.get("skills", {})
    configs = skills.get("config", []) if isinstance(skills, dict) else []
    if isinstance(configs, dict):
        configs = [configs]
    if configs and not isinstance(configs, list):
        findings.append(Finding("ERROR", "skills-config-type", "skills.config must be an array of tables"))
    elif isinstance(configs, list):
        for index, item in enumerate(configs):
            if not isinstance(item, dict):
                findings.append(Finding("ERROR", "skill-config-entry", f"skills.config[{index}] must be a table"))
                continue
            skill_path = item.get("path")
            if not isinstance(skill_path, str) or not skill_path:
                findings.append(Finding("ERROR", "skill-path-missing", f"skills.config[{index}] requires path"))
                continue
            expanded = Path(os.path.expandvars(os.path.expanduser(skill_path)))
            candidates = [expanded] if expanded.name == "SKILL.md" else [expanded / "SKILL.md", expanded]
            if not any(candidate.is_file() and candidate.name == "SKILL.md" for candidate in candidates):
                findings.append(Finding("ERROR", "skill-not-found", f"Configured Skill does not resolve to SKILL.md: {skill_path}"))

    instructions = data.get("developer_instructions", "")
    if isinstance(instructions, str) and any(word in instructions.lower() for word in ("python", "script", "json report")):
        lower = instructions.lower()
        if "exit" not in lower or not any(word in lower for word in ("schema", "validate", "validation")):
            findings.append(Finding("WARN", "script-validation", "Python workflow should require exit-status and output validation"))

    if not any(f.level == "ERROR" for f in findings):
        findings.append(Finding("INFO", "agent-valid", "Agent TOML is structurally valid."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_toml", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = validate(args.agent_toml)
    errors = sum(f.level == "ERROR" for f in findings)
    warnings = sum(f.level == "WARN" for f in findings)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        for f in findings:
            print(f"{f.level:5} {f.code:28} {f.message}")
        print(f"\nSummary: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 2 if args.strict and warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
