# Plugins in ChatGPT and Codex

_Last verified against official OpenAI documentation on July 17, 2026._

## Summary

A **plugin is the installable distribution package**, while a **Skill is a reusable workflow that can be included inside a plugin**.

A plugin can package one or more of the following:

- Skills
- Apps
- App templates

A plugin may also be skill-only. Apps remain the integrations that connect ChatGPT or Codex to external systems, data, and actions. Plugins make those capabilities easier to discover, install, configure, and manage as a workflow package.

For this project, plugin packaging is optional. The current `creating-codex-custom-subagents` folder is already a usable standalone Skill package. Converting it into a plugin becomes useful mainly for broader distribution, workspace administration, or bundling related Skills and Apps.

## Main components

| Component | What it represents | Example for this project |
|---|---|---|
| **Skill** | Reusable instructions, workflow logic, examples, scripts, and references | `creating-codex-custom-subagents/SKILL.md` |
| **App** | Connection to external tools, data, or actions, commonly through MCP | GitHub, Google Drive, or an internal subagent-management service |
| **App template** | An administrator-configurable blueprint for creating an organization-specific App | A template that asks for an MCP URL, authentication configuration, and allowed domains |
| **Plugin** | An installable workflow package containing Skills, Apps, and optional App templates | A future "Codex Subagent Generator" plugin |
| **Custom subagent** | A spawned Codex session configured by a TOML file | `.codex/agents/repository_analyzer.toml` |
| **MCP server** | A service that implements callable tools and exposes them through MCP | `create_agent`, `validate_agent`, or `discover_mcp_tools` |

## Skills

A Skill tells ChatGPT or Codex how to perform a repeatable task consistently. A Skill can contain:

```text
SKILL.md
scripts/
references/
assets/
```

A Skill may include:

- Detailed procedures
- Decision rules
- Examples
- Templates
- Reference material
- Executable scripts
- Validators and test utilities

The current project is already a complete Skill package:

```text
creating-codex-custom-subagents/
├── SKILL.md
├── README.md
├── scripts/
└── references/
```

It can be installed and used directly without being converted into a plugin.

## Apps

An App connects ChatGPT or Codex to an external system. Depending on its implementation and workspace configuration, an App can:

- Search or retrieve data
- Invoke external tools
- Perform authenticated actions
- Synchronize or index content
- Display an interactive interface

Apps are commonly backed by MCP. Authentication and source-system permissions still apply. A plugin does not grant access that the user does not already have in the connected system.

For example, a future App associated with this project could provide deterministic operations such as:

```text
validate_codex_configuration
discover_mcp_tools
test_mcp_authentication
install_agent
run_agent_evaluation
```

That could make some operations more deterministic than relying only on shell commands and model reasoning.

## Plugins

A Plugin packages the capabilities needed for a workflow. Conceptually, a plugin for this project could look like:

```text
Codex Subagent Generator Plugin
├── Skill: create custom Codex subagents
├── Skill: evaluate custom Codex subagents
├── App: MCP validation or agent-management service
└── App template: configure an organization-specific MCP service
```

A plugin can provide:

- Installation and discovery through the Plugin Directory
- A single installable package containing multiple related Skills
- Required and optional App dependencies
- App setup templates
- Workspace-wide installation policies
- Role-based availability
- Central enablement and administration
- A more polished onboarding and update experience

Plugin installation does not override App security. Existing App access controls, action restrictions, approvals, authentication, and source-system permissions continue to apply.

## Why plugin packaging was suggested

This project has grown beyond a minimal `SKILL.md`. It now includes:

- A detailed guided workflow
- Multiple Python validators
- Agent TOML templates
- Companion Skill templates
- MCP configuration support
- Authentication collection
- MCP connectivity validation
- Behavioral evaluation procedures
- Support for optionally generating MCP servers, hooks, or Python utilities

A plugin could package all of these capabilities as one installable product. A user could install a "Codex Subagent Generator" workflow instead of manually cloning a repository and copying a Skill directory.

It could also bundle several related Skills later:

```text
Codex Subagent Toolkit Plugin
├── creating-codex-custom-subagents
├── testing-codex-custom-subagents
├── auditing-codex-custom-subagents
├── debugging-codex-mcp
└── migrating-agent-configurations
```

If an actual App is added, the plugin could declare it as required or optional and guide workspace administrators through configuration.

## Is plugin packaging necessary now?

No.

For the current use case, the standalone Skill is the better fit because:

- The project is maintained in a personal GitHub Skills repository.
- It currently has one primary workflow.
- It does not require a permanently hosted App.
- It can be installed directly into Codex.
- The Skill, scripts, and references are already portable.

The earlier suggestion that plugin packaging was the recommended distribution mechanism should be interpreted narrowly. It is appropriate for broader product-style distribution, not required for every reusable Skill.

## When plugin packaging becomes worthwhile

Revisit plugin packaging when one or more of these conditions become true:

1. The project should be discoverable and installable through the Plugin Directory.
2. It needs organization-wide installation and role-based management.
3. Several related Skills should be distributed as one product.
4. The workflow includes a managed App or App template.
5. A polished installation, onboarding, configuration, and update experience is important.
6. The same workflow should be distributed consistently across ChatGPT and Codex surfaces.

## How MCP relates to this project

The Skill allows the user to configure MCP servers for the generated custom subagent. This does not require the Subagent Generator itself to be packaged as a plugin.

### Current architecture, Skill only

```text
Subagent Generator Skill
        |
        | asks the user for MCP configuration
        v
Generated custom-agent TOML
        |
        v
User's MCP server
```

The generated agent TOML may contain configuration similar to:

```toml
[mcp_servers.company_data]
url = "https://mcp.example.com"
bearer_token_env_var = "COMPANY_MCP_TOKEN"
required = true
enabled_tools = ["search_documents", "read_document"]
```

This architecture works without plugin packaging.

### Possible future plugin architecture

```text
Subagent Generator Plugin
├── Subagent Generator Skill
├── MCP validation App
└── Custom MCP App template
```

In that architecture, the plugin itself could include an App that performs standardized MCP discovery, authentication testing, schema inspection, health checks, or agent installation.

## Recommendation

Keep this project as a standalone Skill for now.

Consider converting it into a plugin only when broader distribution, workspace management, multiple related Skills, or a managed App justify the extra packaging and administration.

The Skill remains the core workflow and intellectual asset. Plugin conversion should be treated as a future distribution step, not as a redesign of the Skill.

## Official references

- Plugins in ChatGPT and Codex: https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex
- Skills in ChatGPT: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- Apps in ChatGPT: https://help.openai.com/en/articles/11487775-apps-in-chatgpt
