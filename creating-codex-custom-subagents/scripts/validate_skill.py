#!/usr/bin/env python3
"""Validate a Codex Skill directory and bundled Python syntax."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data, "\n".join(lines[end + 1 :])


def validate(skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    skill_dir = skill_dir.expanduser().resolve()
    manifest = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [Finding("ERROR", "not-directory", f"Not a directory: {skill_dir}")]
    if not manifest.is_file():
        return [Finding("ERROR", "manifest-missing", f"Missing {manifest}")]

    try:
        text = manifest.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
    except (OSError, UnicodeError, ValueError) as exc:
        return [Finding("ERROR", "manifest-invalid", str(exc))]

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not name:
        findings.append(Finding("ERROR", "name-missing", "Frontmatter requires name"))
    elif not NAME_RE.fullmatch(name):
        findings.append(Finding("ERROR", "name-format", "Name may contain only letters, numbers, and hyphens"))
    elif skill_dir.name != name:
        findings.append(Finding("WARN", "directory-name-mismatch", f"Directory '{skill_dir.name}' differs from name '{name}'"))

    if not description:
        findings.append(Finding("ERROR", "description-missing", "Frontmatter requires description"))
    elif not description.lower().startswith("use when"):
        findings.append(Finding("WARN", "description-trigger", "Description should begin with 'Use when'"))

    if len(body.strip()) < 80:
        findings.append(Finding("WARN", "body-short", "SKILL.md body is unusually short"))

    for script in sorted((skill_dir / "scripts").rglob("*.py")) if (skill_dir / "scripts").is_dir() else []:
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            findings.append(Finding("ERROR", "python-syntax", f"{script}: {exc}"))
        else:
            findings.append(Finding("INFO", "python-syntax-valid", f"Python syntax is valid: {script}"))

    if not any(item.level == "ERROR" for item in findings):
        findings.append(Finding("INFO", "skill-structure-valid", "Skill metadata and directory structure are structurally valid."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_directory", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = validate(args.skill_directory)
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
