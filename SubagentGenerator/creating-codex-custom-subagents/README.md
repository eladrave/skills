# Creating Codex Custom Subagents

An installable Codex Skill that guides the design, creation, installation, extension, validation, and behavioral evaluation of custom Codex subagents.

When invoked, the Skill can generate the complete bundle required by the agent, including:

- A personal or project custom-agent TOML
- A companion Skill when a reusable workflow is useful
- Deterministic Python or other scripts under the companion Skill when needed
- MCP server configuration for existing formal tools
- A new MCP server implementation when the user is defining new typed tools and MCP is the appropriate mechanism
- Hooks when code must run at lifecycle events
- Tests, validators, examples, installation instructions, and rollback steps

The package explicitly separates:

- Custom agent TOML for a specialized spawned Codex session
- Companion Skills for reusable procedures and resources
- Skill scripts for deterministic local Python or other utilities
- MCP servers for typed tools and external services
- Hooks for automatic lifecycle execution
- Codex SDK or external orchestration for programmatic control

## Tool and MCP support

The user can ask that the generated agent use an MCP server. The Skill will collect the relevant configuration, including:

- Existing server or new server implementation
- Streamable HTTP or STDIO transport
- URL, or command, arguments, and working directory
- OAuth, ChatGPT session authentication, bearer-token environment variable, environment-backed headers, STDIO environment variables, or no authentication
- OAuth scopes and callback requirements
- Required and prohibited tool names
- Tool input and output contracts
- Side effects, idempotency, and authorization requirements
- Server and per-tool approval modes
- Startup and tool timeouts
- Safe read-only and approved write smoke tests

Secrets are never written directly into generated TOML, Skills, scripts, tests, or logs. The workflow asks for environment variable names or initiates the supported OAuth flow.

The Skill does not treat configuration as proof of operation. It requires static validation, Codex initialization, spawned-agent tool discovery, a real safe MCP tool call, output validation, error-path testing, and write cleanup where applicable.

A custom agent TOML can select and configure tools from an MCP server. It cannot define a brand-new tool schema or implementation by itself. For a new tool, the Skill designs and implements an MCP server, then connects the generated subagent to it.

## Install for the current user

```bash
mkdir -p ~/.agents/skills
cp -R SubagentGenerator/creating-codex-custom-subagents ~/.agents/skills/
```

Codex scans `$HOME/.agents/skills` for user Skills. Restart Codex if the Skill does not appear immediately.

Invoke it explicitly with:

```text
$creating-codex-custom-subagents
```

Or ask Codex to create, refine, extend, test, or troubleshoot a custom subagent.

## Install for one repository

```bash
mkdir -p .agents/skills
cp -R SubagentGenerator/creating-codex-custom-subagents .agents/skills/
```

## Package contents

- `SKILL.md`: complete guided workflow
- `references/agent-requirements-template.md`: Agent Contract template
- `references/capability-selection.md`: TOML, Skill, script, MCP, hook, and SDK decision guide
- `references/custom-agent-template.toml`: custom agent starter
- `references/companion-skill-template.md`: companion Skill starter
- `references/python-tool-contract.md`: deterministic Python contract checklist
- `references/mcp-tool-and-integration-contract.md`: MCP requirements, authentication, tool definition, and runtime validation runbook
- `references/subagent-hook-template.toml`: lifecycle hook reference
- `references/evaluation-matrix.md`: behavioral evaluation plan
- `scripts/validate_agent.py`: agent TOML and linked-Skill validator
- `scripts/validate_mcp.py`: MCP configuration and local environment validator
- `scripts/validate_skill.py`: Skill structure and Python syntax validator

## Version-sensitive Skill path note

Current official Codex documentation is inconsistent about `skills.config.path`. The configuration reference describes the Skill directory containing `SKILL.md`, while current Skill and subagent examples show the `SKILL.md` file itself. This package accepts either existing form during static validation and requires runtime discovery testing on the target Codex version.

## Validate this package

```bash
python3 scripts/validate_skill.py . --strict
```

## Validate a generated agent

```bash
python3 scripts/validate_agent.py /path/to/agent.toml --strict
```

## Validate MCP configuration

```bash
python3 scripts/validate_mcp.py /path/to/agent-or-config.toml --check-environment --strict
```

Static validation is not the final MCP test. The Skill also requires the generated agent to be spawned in a fresh Codex session and to complete a real safe tool call.
