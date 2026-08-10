#!/usr/bin/env python3
"""Local REST helper for the lacp-agent-builder Codex skill."""

from __future__ import annotations

import argparse
import base64
import copy
import getpass
import hashlib
import json
import os
import socket
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


BACKUP_FORMAT = "lacp-portable-backup"
BACKUP_VERSION = 1
CONFIG_VERSION = 1
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "auth_value",
    "authorization",
    "cookie",
    "credentials",
    "password",
    "secret",
    "static_headers",
    "token",
}


class LacpError(RuntimeError):
    pass


@dataclass(frozen=True)
class Profile:
    name: str
    url: str
    api_key: str


def config_path() -> Path:
    explicit = os.environ.get("LACP_AGENT_BUILDER_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "lacp-agent-builder" / "config.json"


def normalize_url(raw: str, allow_http: bool = False) -> str:
    value = raw.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise LacpError("LACP URL must be an absolute http(s) URL")
    host = (parsed.hostname or "").lower()
    local = host in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not local and not allow_http:
        raise LacpError("remote LACP URLs must use HTTPS; pass --allow-http only for a trusted test network")
    if parsed.query or parsed.fragment:
        raise LacpError("LACP URL must not contain a query or fragment")
    return value


def _load_config(path: Path | None = None) -> dict[str, Any]:
    path = path or config_path()
    if not path.exists():
        return {"version": CONFIG_VERSION, "profiles": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LacpError(f"could not read LACP profile file: {exc}") from exc
    if value.get("version") != CONFIG_VERSION or not isinstance(value.get("profiles"), dict):
        raise LacpError("unsupported LACP profile file")
    return value


def _atomic_private_json(path: Path, value: Any, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise LacpError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_path, path)
        path.chmod(0o600)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def save_profile(name: str, url: str, api_key: str, allow_http: bool = False) -> Profile:
    name = name.strip()
    if not name:
        raise LacpError("profile name is required")
    key = api_key.strip()
    if not key:
        raise LacpError("LACP API key is required")
    normalized = normalize_url(url, allow_http=allow_http)
    path = config_path()
    config = _load_config(path)
    config["profiles"][name] = {"url": normalized, "api_key": key}
    _atomic_private_json(path, config, overwrite=True)
    return Profile(name=name, url=normalized, api_key=key)


def load_profile(name: str) -> Profile:
    env_url = os.environ.get("LACP_URL")
    env_key = os.environ.get("LACP_API_KEY")
    if env_url or env_key:
        if not env_url or not env_key:
            raise LacpError("LACP_URL and LACP_API_KEY must be set together")
        return Profile(name="environment", url=normalize_url(env_url, allow_http=True), api_key=env_key)
    config = _load_config()
    raw = config["profiles"].get(name)
    if not isinstance(raw, dict):
        raise LacpError(f"LACP profile '{name}' is not configured")
    key = str(raw.get("api_key", "")).strip()
    if not key:
        raise LacpError(f"LACP profile '{name}' has no API key")
    return Profile(name=name, url=normalize_url(str(raw.get("url", "")), allow_http=True), api_key=key)


class LacpClient:
    def __init__(self, profile: Profile, timeout: float = 30.0):
        self.profile = profile
        self.base_url = profile.url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, body: Any | None = None) -> tuple[bytes, str]:
        data = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.profile.api_key}",
            "User-Agent": "lacp-agent-builder/1",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace").strip()
            raise LacpError(f"LACP {method} {path} failed with HTTP {exc.code}: {detail or exc.reason}") from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise LacpError(f"could not reach LACP at {self.base_url}: {exc}") from exc

    def json(self, method: str, path: str, body: Any | None = None) -> Any:
        raw, _ = self.request(method, path, body)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LacpError(f"LACP {method} {path} returned invalid JSON") from exc

    def bytes(self, path: str) -> bytes:
        return self.request("GET", path)[0]


def _optional(client: LacpClient, path: str, warnings: list[str]) -> Any | None:
    try:
        return client.json("GET", path)
    except LacpError as exc:
        warnings.append(str(exc))
        return None


def inventory(client: LacpClient) -> dict[str, Any]:
    warnings: list[str] = []
    result = {
        "url": client.base_url,
        "platform": _optional(client, "/api/plugin-manifest", warnings),
        "models": _optional(client, "/v1/models", warnings),
        "runtimes": _optional(client, "/api/runtime-harnesses", warnings),
        "built_in_runtimes": _optional(client, "/api/agent-runtimes", warnings),
        "agents": _optional(client, "/api/agents", warnings),
        "skills": _optional(client, "/api/skills", warnings),
        "rules": _optional(client, "/api/rules", warnings),
        "routines": _optional(client, "/api/routines", warnings),
        "platform_tools": _optional(client, "/api/platform-mcps", warnings),
        "mcp_servers": _optional(client, "/v1/mcp/server", warnings),
    }
    result["warnings"] = warnings
    return result


def _items(value: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get(key), list):
        return []
    return [item for item in value[key] if isinstance(item, dict)]


def _redact(value: Any, path: str = "") -> tuple[Any, list[str]]:
    redacted: list[str] = []
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            if key.lower() in SENSITIVE_KEYS:
                if item not in (None, "", {}, []):
                    redacted.append(child)
                output[key] = {} if isinstance(item, dict) else [] if isinstance(item, list) else None
            else:
                output[key], nested = _redact(item, child)
                redacted.extend(nested)
        return output, redacted
    if isinstance(value, list):
        output = []
        for index, item in enumerate(value):
            cleaned, nested = _redact(item, f"{path}[{index}]")
            output.append(cleaned)
            redacted.extend(nested)
        return output, redacted
    return value, redacted


MCP_CREATE_FIELDS = {
    "server_name", "alias", "description", "instructions", "url", "spec_path", "transport",
    "auth_type", "credentials", "mcp_info", "mcp_access_groups", "allowed_tools",
    "tool_name_to_display_name", "tool_name_to_description", "extra_headers", "static_headers",
    "env_vars", "status", "command", "args", "env", "authorization_url", "token_url",
    "registration_url", "oauth2_flow", "allow_all_keys", "available_on_public_internet",
    "delegate_auth_to_upstream", "oauth_passthrough", "is_byok", "byok_description",
    "byok_api_key_help_url", "source_url", "timeout", "approval_status", "submitted_by",
    "review_notes",
}


def _sanitize_mcp(server: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    payload = {key: copy.deepcopy(value) for key, value in server.items() if key in MCP_CREATE_FIELDS}
    cleaned, redacted = _redact(payload, f"mcp_servers.{server.get('server_id', 'unknown')}")
    return {"source_id": server.get("server_id"), "definition": cleaned}, redacted


def _without_masked_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_masked_keys(item)
            for key, item in value.items()
            if key != "masked_api_key"
        }
    if isinstance(value, list):
        return [_without_masked_keys(item) for item in value]
    return value


def _restore_prerequisites(archive: dict[str, Any]) -> dict[str, Any]:
    resources = archive.get("resources", {})
    providers = resources.get("providers") or {}
    runtimes = resources.get("runtime_harnesses") or {}
    vault = resources.get("vault_keys") or {}
    return {
        "providers_requiring_secret_reentry": [
            {"id": item.get("id"), "api_base": item.get("api_base")}
            for item in providers.get("connected_providers", [])
            if isinstance(item, dict)
        ],
        "runtimes_requiring_secret_or_account_reconnection": [
            {
                "alias": item.get("alias"),
                "api_spec": item.get("api_spec"),
                "api_base": item.get("api_base"),
                "codex_profile_type": item.get("codex_profile_type"),
            }
            for item in runtimes.get("harnesses", [])
            if isinstance(item, dict) and item.get("connected")
        ],
        "global_vault_keys_requiring_values": [
            item.get("key") for item in vault.get("global", []) if isinstance(item, dict)
        ],
        "personal_vault_keys_requiring_values": {
            owner: [item.get("key") for item in items if isinstance(item, dict)]
            for owner, items in vault.get("personal", {}).items()
            if isinstance(items, list)
        },
        "redacted_mcp_or_inline_fields": archive.get("secrets", {}).get("redacted_paths", []),
    }


def _backup_digest(archive: dict[str, Any]) -> str:
    payload = copy.deepcopy(archive)
    payload.pop("integrity", None)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def create_backup(client: LacpClient) -> dict[str, Any]:
    warnings: list[str] = []
    agents_response = client.json("GET", "/api/agents")
    skills_response = client.json("GET", "/api/skills")
    rules_response = client.json("GET", "/api/rules")
    routines_response = client.json("GET", "/api/routines")
    agents = _items(agents_response, "agents")
    agent_entries: list[dict[str, Any]] = []
    redacted_paths: list[str] = []
    owners: set[str] = set()
    for raw_agent in agents:
        agent, redacted = _redact(raw_agent, f"agents.{raw_agent.get('id', 'unknown')}")
        redacted_paths.extend(redacted)
        owner = agent.get("owner_id")
        if isinstance(owner, str) and owner:
            owners.add(owner)
        agent_id = quote(str(raw_agent.get("id", "")), safe="")
        memory = _optional(client, f"/api/agents/{agent_id}/memory", warnings)
        files_response = _optional(client, f"/api/agents/{agent_id}/files", warnings)
        files: list[dict[str, Any]] = []
        for metadata in _items(files_response, "files"):
            file_path = str(metadata.get("path", ""))
            encoded_path = quote(file_path, safe="/")
            try:
                content = client.bytes(f"/api/agents/{agent_id}/files/{encoded_path}")
            except LacpError as exc:
                warnings.append(str(exc))
                continue
            files.append({
                "path": file_path,
                "encoding": metadata.get("encoding", "utf8"),
                "content_base64": base64.b64encode(content).decode("ascii"),
                "size_bytes": len(content),
            })
        agent_entries.append({
            "agent": agent,
            "memory": _items(memory, "memories"),
            "files": files,
            "source_kind": "managed" if "session_id" in raw_agent else "configured",
        })

    mcp_response = _optional(client, "/v1/mcp/server", warnings)
    mcp_servers: list[dict[str, Any]] = []
    for server in _items(mcp_response, "data"):
        sanitized, redacted = _sanitize_mcp(server)
        mcp_servers.append(sanitized)
        redacted_paths.extend(redacted)

    vault = {"global": [], "personal": {}}
    global_vault = _optional(client, "/api/vault/global", warnings)
    vault["global"] = _items(global_vault, "keys")
    for owner in sorted(owners):
        personal = _optional(client, f"/api/vault/{quote(owner, safe='')}", warnings)
        vault["personal"][owner] = _items(personal, "keys")

    providers = _optional(client, "/api/providers", warnings)
    runtime_harnesses = _optional(client, "/api/runtime-harnesses", warnings)
    built_in_runtimes = _optional(client, "/api/agent-runtimes", warnings)
    warnings.append("The portable backup contains agent prompts, memory, and files and is not encrypted.")
    archive: dict[str, Any] = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "url": client.base_url,
            "platform": _optional(client, "/api/plugin-manifest", warnings),
        },
        "resources": {
            "models": _optional(client, "/v1/models", warnings),
            "providers": _without_masked_keys(providers),
            "runtime_harnesses": _without_masked_keys(runtime_harnesses),
            "built_in_runtimes": _without_masked_keys(built_in_runtimes),
            "mcp_proxy_setting": _optional(client, "/v1/mcp/settings/proxy-base-url", warnings),
            "mcp_servers": mcp_servers,
            "vault_keys": vault,
            "skills": _items(skills_response, "skills"),
            "rules": _items(rules_response, "rules"),
            "agents": agent_entries,
            "routines": _items(routines_response, "routines"),
        },
        "secrets": {
            "included": False,
            "redacted_paths": sorted(set(redacted_paths)),
            "note": "Re-enter provider, runtime, MCP, OAuth, and vault secret values on the target.",
        },
        "warnings": warnings,
    }
    archive["integrity"] = {"algorithm": "sha256", "sha256": _backup_digest(archive)}
    archive["prerequisites"] = _restore_prerequisites(archive)
    archive["integrity"]["sha256"] = _backup_digest(archive)
    return archive


def write_backup(path: Path, archive: dict[str, Any], force: bool = False) -> None:
    _atomic_private_json(path.expanduser(), archive, overwrite=force)


def read_backup(path: Path) -> dict[str, Any]:
    try:
        archive = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LacpError(f"could not read backup: {exc}") from exc
    if archive.get("format") != BACKUP_FORMAT or archive.get("version") != BACKUP_VERSION:
        raise LacpError("unsupported LACP backup format")
    expected = archive.get("integrity", {}).get("sha256")
    actual = _backup_digest(archive)
    if not expected or expected != actual:
        raise LacpError("backup integrity check failed")
    return archive


def _agent_create_payload(agent: dict[str, Any], owner_id: str | None = None) -> dict[str, Any]:
    source = copy.deepcopy(agent)
    payload: dict[str, Any] = {}
    for key in (
        "name", "description", "model", "system", "prompt", "tools", "vault_keys",
        "setup_commands", "max_runtime_minutes", "on_failure", "config", "harness",
        "skill_ids", "rule_ids",
    ):
        if key in source and source[key] is not None:
            payload[key] = source[key]
    payload["owner_id"] = owner_id or source.get("owner_id") or "restored-user"
    config = payload.setdefault("config", {})
    if not isinstance(config, dict):
        config = {}
        payload["config"] = config
    if source.get("mcp_servers") and "mcp_servers" not in config:
        config["mcp_servers"] = source["mcp_servers"]
    if source.get("skills") and "skills" not in config:
        config["skills"] = source["skills"]
    runtime = source.get("runtime") or (source.get("config") or {}).get("runtime")
    if runtime:
        payload["runtime"] = runtime
    cron = source.get("cron")
    if cron:
        payload["schedule"] = {"cron": cron, "timezone": source.get("timezone") or "UTC"}
    return payload


def _without_sub_agents(config: Any) -> tuple[dict[str, Any], list[str]]:
    value = copy.deepcopy(config) if isinstance(config, dict) else {}
    entries = value.pop("sub_agents", value.pop("subAgents", []))
    refs: list[str] = []
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, str):
                refs.append(entry)
            elif isinstance(entry, dict):
                candidate = entry.get("agent_id") or entry.get("agentId") or entry.get("id")
                if isinstance(candidate, str) and candidate:
                    refs.append(candidate)
    return value, refs


def _rewrite_mcp(value: Any, id_map: dict[str, str], target_url: str) -> Any:
    if isinstance(value, dict):
        output = {key: _rewrite_mcp(item, id_map, target_url) for key, item in value.items()}
        for key in ("name", "mcp_server_name"):
            if isinstance(output.get(key), str) and output[key] in id_map:
                output[key] = id_map[output[key]]
        if isinstance(output.get("url"), str):
            for old, new in id_map.items():
                marker = f"/mcp/{old}"
                if marker in output["url"]:
                    output["url"] = f"{target_url}/mcp/{new}"
                    break
        return output
    if isinstance(value, list):
        return [_rewrite_mcp(item, id_map, target_url) for item in value]
    return value


def _unique_name(base: str, used: set[str]) -> str:
    candidate = f"{base} (restored)"
    index = 2
    while candidate in used:
        candidate = f"{base} (restored {index})"
        index += 1
    used.add(candidate)
    return candidate


def _conflict_name(name: str, existing: dict[str, dict[str, Any]], policy: str, used: set[str]) -> tuple[str, dict[str, Any] | None]:
    match = existing.get(name)
    if not match:
        used.add(name)
        return name, None
    if policy == "fail":
        raise LacpError(f"target already contains '{name}'")
    if policy == "skip":
        return name, match
    return _unique_name(name, used), None


def _restore_plan(client: LacpClient, archive: dict[str, Any], conflict: str) -> dict[str, Any]:
    resources = archive["resources"]
    preflight_warnings: list[str] = []
    target_agents = _items(client.json("GET", "/api/agents"), "agents")
    target_skills = _items(client.json("GET", "/api/skills"), "skills")
    target_rules = _items(client.json("GET", "/api/rules"), "rules")
    target_routines = _items(client.json("GET", "/api/routines"), "routines")
    target_runtime_response = _optional(client, "/api/runtime-harnesses", preflight_warnings)
    target_runtimes = {
        str(item.get("alias")): item
        for item in _items(target_runtime_response, "harnesses")
        if item.get("alias")
    }
    def source_runtime(entry: dict[str, Any]) -> str | None:
        agent = entry.get("agent") if isinstance(entry.get("agent"), dict) else {}
        config = agent.get("config") if isinstance(agent.get("config"), dict) else {}
        value = agent.get("runtime") or config.get("runtime")
        return str(value) if value else None

    required_runtimes = sorted(
        {runtime for entry in resources.get("agents", []) if (runtime := source_runtime(entry))}
    )
    runtime_prerequisites = [
        {
            "alias": alias,
            "present": alias in target_runtimes,
            "connected": bool(target_runtimes.get(alias, {}).get("connected")),
        }
        for alias in required_runtimes
    ]
    target_mcp_response = _optional(client, "/v1/mcp/server", preflight_warnings)
    target_mcp = _items(target_mcp_response, "data")
    source_mcp_names = {
        str(item.get("definition", {}).get("server_name") or item.get("definition", {}).get("alias") or "")
        for item in resources.get("mcp_servers", [])
    }
    target_mcp_names = {
        str(item.get("server_name") or item.get("alias") or "") for item in target_mcp
    }
    conflicts = {
        "mcp_servers": sorted((source_mcp_names & target_mcp_names) - {""}),
        "agents": sorted(set(entry["agent"].get("name", "") for entry in resources["agents"]) & {item.get("name", "") for item in target_agents}),
        "skills": sorted({item.get("name", "") for item in resources["skills"]} & {item.get("name", "") for item in target_skills}),
        "rules": sorted({item.get("name", "") for item in resources["rules"]} & {item.get("name", "") for item in target_rules}),
        "routines": sorted({item.get("name", "") for item in resources["routines"]} & {item.get("name", "") for item in target_routines}),
    }
    blocked_reasons: list[str] = []
    if conflict == "fail" and any(conflicts.values()):
        blocked_reasons.append("target contains conflicting names")
    if resources.get("mcp_servers") and target_mcp_response is None:
        blocked_reasons.append("target key cannot access MCP server administration required by this backup")
    if blocked_reasons:
        state = "blocked"
    else:
        state = "ready"
    return {
        "mode": "dry-run",
        "state": state,
        "target": client.base_url,
        "counts": {
            "mcp_servers": len(resources.get("mcp_servers", [])),
            "skills": len(resources.get("skills", [])),
            "rules": len(resources.get("rules", [])),
            "agents": len(resources.get("agents", [])),
            "routines": len(resources.get("routines", [])),
            "memories": sum(len(item.get("memory", [])) for item in resources.get("agents", [])),
            "files": sum(len(item.get("files", [])) for item in resources.get("agents", [])),
        },
        "conflict_policy": conflict,
        "conflicts": conflicts,
        "secrets": archive.get("secrets", {}),
        "prerequisites": archive.get("prerequisites", _restore_prerequisites(archive)),
        "target_runtime_prerequisites": runtime_prerequisites,
        "source_warnings": archive.get("warnings", []),
        "preflight_warnings": preflight_warnings,
        "blocked_reasons": blocked_reasons,
        "status_behavior": "agents and routines remain paused unless --restore-status is used",
    }


def _maps_by_name(items: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    mapping = {str(item.get("name")): item for item in items if item.get("name")}
    return mapping, set(mapping)


def restore_backup(
    client: LacpClient,
    archive: dict[str, Any],
    *,
    apply: bool = False,
    conflict: str = "fail",
    owner_id: str | None = None,
    restore_status: bool = False,
    restore_instance_settings: bool = False,
) -> dict[str, Any]:
    plan = _restore_plan(client, archive, conflict)
    if not apply:
        return plan
    if plan["state"] != "ready":
        raise LacpError("restore is blocked by target conflicts")
    resources = archive["resources"]
    warnings: list[str] = list(archive.get("warnings", []))
    mappings: dict[str, dict[str, str]] = {"mcp_servers": {}, "skills": {}, "rules": {}, "agents": {}}
    skipped: dict[str, list[str]] = {"mcp_servers": [], "skills": [], "rules": [], "agents": [], "routines": []}

    existing_mcp_response = _optional(client, "/v1/mcp/server", warnings)
    existing_mcp = _items(existing_mcp_response, "data")
    mcp_by_name = {
        str(item.get("server_name") or item.get("alias")): item
        for item in existing_mcp
        if item.get("server_name") or item.get("alias")
    }
    used_mcp = set(mcp_by_name)
    for entry in resources.get("mcp_servers", []):
        definition = copy.deepcopy(entry.get("definition", {}))
        old_id = str(entry.get("source_id", ""))
        name = str(definition.get("server_name") or definition.get("alias") or old_id)
        chosen, existing = _conflict_name(name, mcp_by_name, conflict, used_mcp)
        if existing:
            mappings["mcp_servers"][old_id] = str(existing["server_id"])
            skipped["mcp_servers"].append(old_id)
            continue
        if chosen != name:
            if definition.get("server_name"):
                definition["server_name"] = chosen
            else:
                definition["alias"] = chosen
        created = client.json("POST", "/v1/mcp/server", definition)
        mappings["mcp_servers"][old_id] = str(created["server_id"])

    existing_skills = _items(client.json("GET", "/api/skills"), "skills")
    skill_by_name, used_skills = _maps_by_name(existing_skills)
    for source in resources.get("skills", []):
        old_id = str(source.get("id", ""))
        name, existing = _conflict_name(str(source.get("name", "")), skill_by_name, conflict, used_skills)
        if existing:
            mappings["skills"][old_id] = str(existing["id"])
            skipped["skills"].append(old_id)
            continue
        payload = {key: source.get(key) for key in ("name", "content", "description", "owner_id")}
        payload["name"] = name
        created = client.json("POST", "/api/skills", payload)
        mappings["skills"][old_id] = str(created["id"])

    existing_rules = _items(client.json("GET", "/api/rules"), "rules")
    rule_by_name, used_rules = _maps_by_name(existing_rules)
    for source in resources.get("rules", []):
        old_id = str(source.get("id", ""))
        name, existing = _conflict_name(str(source.get("name", "")), rule_by_name, conflict, used_rules)
        if existing:
            mappings["rules"][old_id] = str(existing["id"])
            skipped["rules"].append(old_id)
            continue
        payload = {key: source.get(key) for key in ("name", "content", "description", "owner_id")}
        payload["name"] = name
        created = client.json("POST", "/api/rules", payload)
        mappings["rules"][old_id] = str(created["id"])

    existing_agents = _items(client.json("GET", "/api/agents"), "agents")
    agent_by_name, used_agents = _maps_by_name(existing_agents)
    pending: list[tuple[dict[str, Any], dict[str, Any], list[str]]] = []
    for entry in resources.get("agents", []):
        source = copy.deepcopy(entry["agent"])
        old_id = str(source.get("id", ""))
        name, existing = _conflict_name(str(source.get("name", "")), agent_by_name, conflict, used_agents)
        if existing:
            mappings["agents"][old_id] = str(existing["id"])
            skipped["agents"].append(old_id)
            continue
        source["name"] = name
        config, child_ids = _without_sub_agents(source.get("config"))
        source["config"] = _rewrite_mcp(config, mappings["mcp_servers"], client.base_url)
        source["tools"] = _rewrite_mcp(source.get("tools"), mappings["mcp_servers"], client.base_url)
        source["mcp_servers"] = _rewrite_mcp(source.get("mcp_servers"), mappings["mcp_servers"], client.base_url)
        source["skill_ids"] = [mappings["skills"].get(str(item), str(item)) for item in source.get("skill_ids", [])]
        source["rule_ids"] = [mappings["rules"].get(str(item), str(item)) for item in source.get("rule_ids", [])]
        payload = _agent_create_payload(source, owner_id=owner_id)
        created = client.json("POST", "/api/agents", payload)
        mappings["agents"][old_id] = str(created["id"])
        pending.append((entry, created, child_ids))

    restored_counts = {"mcp_servers": len(mappings["mcp_servers"]) - len(skipped["mcp_servers"]), "skills": len(mappings["skills"]) - len(skipped["skills"]), "rules": len(mappings["rules"]) - len(skipped["rules"]), "agents": len(mappings["agents"]) - len(skipped["agents"]), "routines": 0, "memories": 0, "files": 0}
    for entry, created, child_ids in pending:
        source = entry["agent"]
        new_id = str(created["id"])
        config, _ = _without_sub_agents(source.get("config"))
        config = _rewrite_mcp(config, mappings["mcp_servers"], client.base_url)
        mapped_children = [mappings["agents"][old] for old in child_ids if old in mappings["agents"]]
        if mapped_children:
            config["sub_agents"] = [{"agent_id": child} for child in mapped_children]
            ids = [item for item in config.get("platform_mcp_ids", []) if isinstance(item, str)]
            if "run_sub_agent" not in ids:
                ids.append("run_sub_agent")
            config["platform_mcp_ids"] = ids
        patch: dict[str, Any] = {"config": config}
        if restore_status and source.get("status"):
            patch["status"] = source["status"]
        client.json("PATCH", f"/api/agents/{quote(new_id, safe='')}", patch)
        for memory in entry.get("memory", []):
            client.json("POST", f"/api/agents/{quote(new_id, safe='')}/memory", {
                "key": memory.get("key"),
                "value": memory.get("value"),
                "always_on": bool(memory.get("always_on")),
            })
            restored_counts["memories"] += 1
        for file in entry.get("files", []):
            raw = base64.b64decode(file.get("content_base64", ""), validate=True)
            if file.get("encoding") == "utf8":
                body = {"content": raw.decode("utf-8"), "encoding": "utf8"}
            else:
                body = {"content_base64": base64.b64encode(raw).decode("ascii")}
            path = quote(str(file.get("path", "")), safe="/")
            client.json("PUT", f"/api/agents/{quote(new_id, safe='')}/files/{path}", body)
            restored_counts["files"] += 1

    existing_routines = _items(client.json("GET", "/api/routines"), "routines")
    routine_by_name, used_routines = _maps_by_name(existing_routines)
    for source in resources.get("routines", []):
        name, existing = _conflict_name(str(source.get("name", "")), routine_by_name, conflict, used_routines)
        if existing:
            skipped["routines"].append(str(source.get("id", "")))
            continue
        old_agent_id = str(source.get("agent_id", ""))
        new_agent_id = mappings["agents"].get(old_agent_id)
        if not new_agent_id:
            warnings.append(f"routine '{source.get('name')}' skipped because its agent was not restored")
            continue
        payload = {
            "agent_id": new_agent_id,
            "name": name,
            "prompt": source.get("prompt"),
            "cron": source.get("cron"),
            "timezone": source.get("timezone") or "UTC",
            "status": source.get("status") if restore_status else "paused",
        }
        client.json("POST", "/api/routines", payload)
        restored_counts["routines"] += 1

    if restore_instance_settings:
        setting = resources.get("mcp_proxy_setting")
        if isinstance(setting, dict):
            client.json("PUT", "/v1/mcp/settings/proxy-base-url", {"proxy_base_url": setting.get("proxy_base_url")})

    return {
        "mode": "applied",
        "target": client.base_url,
        "restored": restored_counts,
        "mappings": mappings,
        "skipped": skipped,
        "warnings": warnings,
        "secrets": archive.get("secrets", {}),
        "prerequisites": archive.get("prerequisites", _restore_prerequisites(archive)),
    }


def _resolve_mcp_attachments(client: LacpClient, agent: dict[str, Any], servers: dict[str, dict[str, Any]]) -> None:
    requested = agent.pop("mcp_server_ids", [])
    if not isinstance(requested, list):
        raise LacpError("mcp_server_ids must be a list")
    ids = []
    for raw in requested:
        server_id = str(raw)
        if server_id not in servers:
            raise LacpError(f"unknown MCP server ID: {server_id}")
        ids.append(server_id)
    config = agent.setdefault("config", {})
    if not isinstance(config, dict):
        raise LacpError("agent config must be an object")
    base_tools = [item for item in agent.get("tools", []) if not (isinstance(item, dict) and item.get("type") == "mcp_toolset")]
    mcp_servers = [{"type": "url", "name": item, "url": f"{client.base_url}/mcp/{item}"} for item in ids]
    tools = base_tools + [{"type": "mcp_toolset", "mcp_server_name": item} for item in ids]
    agent["tools"] = tools
    config["tools"] = tools
    config["mcp_servers"] = mcp_servers


def _runtime_catalog(client: LacpClient) -> dict[str, dict[str, Any]]:
    response = client.json("GET", "/api/runtime-harnesses")
    return {
        str(item.get("alias")): item
        for item in _items(response, "harnesses")
        if item.get("alias")
    }


def _model_ids(client: LacpClient, runtime: str) -> set[str]:
    query = urlencode({"runtime": runtime})
    response = client.json("GET", f"/v1/models?{query}")
    return {
        str(item.get("id"))
        for item in _items(response, "data")
        if item.get("id")
    }


def normalize_blueprint(client: LacpClient, blueprint: dict[str, Any]) -> dict[str, Any]:
    raw_agents = blueprint.get("agents")
    if not isinstance(raw_agents, list) or not raw_agents:
        raise LacpError("blueprint must contain a non-empty agents list")
    runtimes = _runtime_catalog(client)
    skills = {str(item.get("id")) for item in _items(client.json("GET", "/api/skills"), "skills")}
    rules = {str(item.get("id")) for item in _items(client.json("GET", "/api/rules"), "rules")}
    mcp_response = _optional(client, "/v1/mcp/server", [])
    servers = {str(item.get("server_id")): item for item in _items(mcp_response, "data")}
    models_by_runtime: dict[str, set[str]] = {}
    normalized: list[dict[str, Any]] = []
    refs: set[str] = set()
    for raw in raw_agents:
        if not isinstance(raw, dict):
            raise LacpError("each blueprint agent must be an object")
        agent = copy.deepcopy(raw)
        ref = str(agent.pop("ref", "")).strip()
        if not ref or ref in refs:
            raise LacpError("every blueprint agent requires a unique ref")
        refs.add(ref)
        for field in ("name", "owner_id", "runtime", "model", "system"):
            if not isinstance(agent.get(field), str) or not agent[field].strip():
                raise LacpError(f"agent '{ref}' requires {field}")
        runtime = agent["runtime"].strip()
        runtime_entry = runtimes.get(runtime)
        if runtime_entry is None:
            raise LacpError(f"agent '{ref}' uses unknown runtime: {runtime}")
        if not runtime_entry.get("connected"):
            raise LacpError(f"agent '{ref}' uses runtime that is not connected: {runtime}")
        if runtime not in models_by_runtime:
            models_by_runtime[runtime] = _model_ids(client, runtime)
        if agent["model"] not in models_by_runtime[runtime]:
            raise LacpError(f"agent '{ref}' uses unavailable model for {runtime}: {agent['model']}")
        skill_ids = agent.get("skill_ids", [])
        rule_ids = agent.get("rule_ids", [])
        if not isinstance(skill_ids, list) or any(str(item) not in skills for item in skill_ids):
            raise LacpError(f"agent '{ref}' contains an unknown skill ID")
        if not isinstance(rule_ids, list) or any(str(item) not in rules for item in rule_ids):
            raise LacpError(f"agent '{ref}' contains an unknown rule ID")
        allowed_tools = {
            str(item.get("id"))
            for item in runtime_entry.get("tools", [])
            if isinstance(item, dict) and item.get("id")
        }
        requested_tools = agent.get("tools", [])
        if not isinstance(requested_tools, list):
            raise LacpError(f"agent '{ref}' tools must be a list")
        if any(not isinstance(item, dict) or not isinstance(item.get("type"), str) for item in requested_tools):
            raise LacpError(f"agent '{ref}' tools must contain objects with a type")
        unknown_tools = [
            str(item.get("type"))
            for item in requested_tools
            if isinstance(item, dict)
            and item.get("type") != "mcp_toolset"
            and item.get("type") not in allowed_tools
        ]
        if unknown_tools:
            raise LacpError(f"agent '{ref}' uses unsupported tools for {runtime}: {', '.join(unknown_tools)}")
        children = agent.pop("sub_agents", [])
        if not isinstance(children, list):
            raise LacpError(f"agent '{ref}' sub_agents must be a list")
        _resolve_mcp_attachments(client, agent, servers)
        normalized.append({"ref": ref, "agent": agent, "sub_agents": [str(item) for item in children]})
    for entry in normalized:
        unknown = [item for item in entry["sub_agents"] if item not in refs]
        if unknown:
            raise LacpError(f"agent '{entry['ref']}' references unknown sub-agents: {', '.join(unknown)}")
        if entry["ref"] in entry["sub_agents"]:
            raise LacpError(f"agent '{entry['ref']}' cannot reference itself")
    graph = {entry["ref"]: entry["sub_agents"] for entry in normalized}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ref: str) -> None:
        if ref in visiting:
            raise LacpError("sub-agent relationships must not contain a cycle")
        if ref in visited:
            return
        visiting.add(ref)
        for child in graph[ref]:
            visit(child)
        visiting.remove(ref)
        visited.add(ref)

    for ref in graph:
        visit(ref)
    return {"agents": normalized}


def apply_blueprint(client: LacpClient, normalized: dict[str, Any]) -> dict[str, Any]:
    mappings: dict[str, str] = {}
    created: list[dict[str, Any]] = []
    try:
        for entry in normalized["agents"]:
            agent = copy.deepcopy(entry["agent"])
            config, _ = _without_sub_agents(agent.get("config"))
            agent["config"] = config
            row = client.json("POST", "/api/agents", agent)
            mappings[entry["ref"]] = str(row["id"])
            created.append(row)
        for entry in normalized["agents"]:
            if not entry["sub_agents"]:
                continue
            agent_id = mappings[entry["ref"]]
            config = copy.deepcopy(entry["agent"].get("config", {}))
            config["sub_agents"] = [{"agent_id": mappings[ref]} for ref in entry["sub_agents"]]
            ids = [item for item in config.get("platform_mcp_ids", []) if isinstance(item, str)]
            if "run_sub_agent" not in ids:
                ids.append("run_sub_agent")
            config["platform_mcp_ids"] = ids
            client.json("PATCH", f"/api/agents/{quote(agent_id, safe='')}", {"config": config})
    except LacpError:
        for row in reversed(created):
            try:
                client.json("DELETE", f"/api/agents/{quote(str(row['id']), safe='')}")
            except LacpError:
                pass
        raise
    return {"created": created, "mappings": mappings, "status": "paused"}


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a remote LACP through its REST API")
    sub = parser.add_subparsers(dest="command", required=True)

    configure = sub.add_parser("configure")
    configure.add_argument("--profile", default="default")
    configure.add_argument("--url", required=True)
    configure.add_argument("--key-stdin", action="store_true")
    configure.add_argument("--allow-http", action="store_true")

    for name in ("status", "inventory"):
        command = sub.add_parser(name)
        command.add_argument("--profile", default="default")

    create = sub.add_parser("create")
    create.add_argument("--profile", default="default")
    create.add_argument("--spec", type=Path, required=True)
    create.add_argument("--apply", action="store_true")

    backup = sub.add_parser("backup")
    backup.add_argument("--profile", default="default")
    backup.add_argument("--output", type=Path, required=True)
    backup.add_argument("--force", action="store_true")

    restore = sub.add_parser("restore")
    restore.add_argument("--profile", default="default")
    restore.add_argument("--input", type=Path, required=True)
    restore.add_argument("--apply", action="store_true")
    restore.add_argument("--conflict", choices=("fail", "skip", "rename"), default="fail")
    restore.add_argument("--owner-id")
    restore.add_argument("--restore-status", action="store_true")
    restore.add_argument("--restore-instance-settings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "configure":
            if args.key_stdin:
                key = sys.stdin.readline().rstrip("\r\n")
            else:
                key = getpass.getpass("LACP API key: ")
            profile = save_profile(args.profile, args.url, key, allow_http=args.allow_http)
            _json_print({"configured": True, "profile": profile.name, "url": profile.url})
            return 0

        profile = load_profile(args.profile)
        client = LacpClient(profile)
        if args.command == "status":
            health = client.json("GET", "/api/plugin-manifest")
            agents = client.json("GET", "/api/agents")
            _json_print({
                "authenticated": True,
                "configured": True,
                "profile": profile.name,
                "url": profile.url,
                "platform": health,
                "agent_count": len(_items(agents, "agents")),
            })
        elif args.command == "inventory":
            _json_print(inventory(client))
        elif args.command == "create":
            blueprint = json.loads(args.spec.read_text(encoding="utf-8"))
            normalized = normalize_blueprint(client, blueprint)
            _json_print(apply_blueprint(client, normalized) if args.apply else {"mode": "dry-run", **normalized})
        elif args.command == "backup":
            archive = create_backup(client)
            write_backup(args.output, archive, force=args.force)
            _json_print({
                "created": True,
                "output": str(args.output.expanduser().resolve()),
                "sha256": archive["integrity"]["sha256"],
                "counts": _restore_plan_counts(archive),
                "warnings": archive["warnings"],
                "redacted_paths": archive["secrets"]["redacted_paths"],
            })
        elif args.command == "restore":
            archive = read_backup(args.input)
            _json_print(restore_backup(
                client,
                archive,
                apply=args.apply,
                conflict=args.conflict,
                owner_id=args.owner_id,
                restore_status=args.restore_status,
                restore_instance_settings=args.restore_instance_settings,
            ))
        return 0
    except (LacpError, OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _restore_plan_counts(archive: dict[str, Any]) -> dict[str, int]:
    resources = archive["resources"]
    return {
        "mcp_servers": len(resources.get("mcp_servers", [])),
        "skills": len(resources.get("skills", [])),
        "rules": len(resources.get("rules", [])),
        "agents": len(resources.get("agents", [])),
        "routines": len(resources.get("routines", [])),
        "memories": sum(len(item.get("memory", [])) for item in resources.get("agents", [])),
        "files": sum(len(item.get("files", [])) for item in resources.get("agents", [])),
    }


if __name__ == "__main__":
    raise SystemExit(main())
