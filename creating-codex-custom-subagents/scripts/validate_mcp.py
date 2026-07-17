#!/usr/bin/env python3
"""Validate MCP server configuration embedded in Codex TOML."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print("Python 3.11+ is required", file=sys.stderr)
    raise SystemExit(3)

APPROVALS = {"auto", "prompt", "writes", "approve"}
SECRET_RE = re.compile(r"(?i)(authorization\s*=|bearer\s+[A-Za-z0-9._-]{12,}|api[_-]?key\s*=\s*['\"][^'\"]+|token\s*=\s*['\"][^'\"]+)")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def validate(path: Path, check_environment: bool) -> list[Finding]:
    findings: list[Finding] = []
    path = path.expanduser().resolve()
    if not path.is_file():
        return [Finding("ERROR", "not-found", f"TOML not found: {path}")]
    try:
        raw = path.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        return [Finding("ERROR", "toml-invalid", str(exc))]

    if SECRET_RE.search(raw):
        findings.append(Finding("ERROR", "possible-secret", "Possible embedded credential or Authorization header detected"))

    servers = data.get("mcp_servers", {})
    if not isinstance(servers, dict):
        return findings + [Finding("ERROR", "servers-type", "mcp_servers must be a table")]
    if not servers:
        findings.append(Finding("WARN", "servers-empty", "No mcp_servers entries found"))

    for server_name, config in servers.items():
        prefix = f"mcp_servers.{server_name}"
        if not isinstance(config, dict):
            findings.append(Finding("ERROR", "server-type", f"{prefix} must be a table"))
            continue
        has_url = isinstance(config.get("url"), str) and bool(config.get("url"))
        has_command = isinstance(config.get("command"), str) and bool(config.get("command"))
        if has_url == has_command:
            findings.append(Finding("ERROR", "transport", f"{prefix} must configure exactly one of url or command"))

        if has_url:
            parsed = urlparse(config["url"])
            if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                findings.append(Finding("ERROR", "url-invalid", f"Invalid MCP URL: {config['url']}"))
            elif parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
                findings.append(Finding("WARN", "http-insecure", f"Non-local MCP URL should use HTTPS: {config['url']}"))

        if has_command and check_environment:
            command = config["command"]
            if not (Path(command).is_file() or shutil.which(command)):
                findings.append(Finding("ERROR", "command-missing", f"MCP command not found: {command}"))
            cwd = config.get("cwd")
            if cwd and not Path(os.path.expandvars(os.path.expanduser(cwd))).is_dir():
                findings.append(Finding("ERROR", "cwd-missing", f"MCP cwd not found: {cwd}"))

        env_names: list[str] = []
        bearer = config.get("bearer_token_env_var")
        if bearer is not None:
            if not isinstance(bearer, str) or not bearer:
                findings.append(Finding("ERROR", "bearer-env-type", f"{prefix}.bearer_token_env_var must be a non-empty string"))
            else:
                env_names.append(bearer)
        for field in ("env_http_headers", "http_headers"):
            value = config.get(field)
            if value is not None and not isinstance(value, dict):
                findings.append(Finding("ERROR", "headers-type", f"{prefix}.{field} must be a table"))
            if field == "env_http_headers" and isinstance(value, dict):
                env_names.extend(str(v) for v in value.values())
        env_vars = config.get("env_vars", [])
        if isinstance(env_vars, list):
            for value in env_vars:
                if isinstance(value, str):
                    env_names.append(value)
                elif isinstance(value, dict) and isinstance(value.get("name"), str):
                    env_names.append(value["name"])
                else:
                    findings.append(Finding("ERROR", "env-vars-entry", f"Invalid env_vars entry in {prefix}"))
        elif env_vars is not None:
            findings.append(Finding("ERROR", "env-vars-type", f"{prefix}.env_vars must be an array"))

        if check_environment:
            for env_name in sorted(set(env_names)):
                if env_name not in os.environ:
                    findings.append(Finding("ERROR", "environment-missing", f"Required environment variable is not set: {env_name}"))

        for field in ("enabled_tools", "disabled_tools"):
            value = config.get(field)
            if value is not None and (not isinstance(value, list) or not all(isinstance(item, str) for item in value)):
                findings.append(Finding("ERROR", "tools-type", f"{prefix}.{field} must be an array of strings"))

        approval = config.get("default_tools_approval_mode")
        if approval is not None and approval not in APPROVALS:
            findings.append(Finding("ERROR", "approval-invalid", f"Unsupported approval mode in {prefix}: {approval}"))
        tools = config.get("tools", {})
        if tools is not None and not isinstance(tools, dict):
            findings.append(Finding("ERROR", "tool-overrides-type", f"{prefix}.tools must be a table"))
        elif isinstance(tools, dict):
            for tool_name, tool_config in tools.items():
                mode = tool_config.get("approval_mode") if isinstance(tool_config, dict) else None
                if mode is not None and mode not in APPROVALS:
                    findings.append(Finding("ERROR", "tool-approval-invalid", f"Unsupported approval mode for {prefix}.tools.{tool_name}: {mode}"))

        for field in ("startup_timeout_sec", "tool_timeout_sec"):
            value = config.get(field)
            if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                findings.append(Finding("ERROR", "timeout-invalid", f"{prefix}.{field} must be positive"))

    if not any(f.level == "ERROR" for f in findings):
        findings.append(Finding("INFO", "mcp-config-valid", "MCP configuration is structurally valid."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("toml_path", type=Path)
    parser.add_argument("--check-environment", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = validate(args.toml_path, args.check_environment)
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
