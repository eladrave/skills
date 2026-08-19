# Amazon Transaction MCP plugin

This directory is a portable local marketplace for the `amazon-transaction-mcp` plugin. The
plugin bundles the Amazon workflow skill with the remote, read-only MCP connection.

The repository contains no Amazon username, password, cookie, OTP, bearer token, or tokenized
URL. Supply the permanent MCP token separately on each trusted machine.

## Contents

```text
plugin/
├── .agents/plugins/marketplace.json
└── plugins/amazon-transaction-mcp/
    ├── .codex-plugin/plugin.json
    ├── .mcp.json
    └── skills/amazon-transaction-mcp/
        ├── SKILL.md
        └── agents/openai.yaml
```

## Install in Codex

Prerequisites:

- A current Codex CLI or Codex in the ChatGPT desktop app.
- Git access to the private `eladrave/skills` repository.
- The permanent Amazon Transaction MCP token from the private
  `Amazon_transaction_mcp.md` document in the Google Drive `Codex` folder.

Clone only the required part of the repository if desired:

```bash
git clone --filter=blob:none --sparse https://github.com/eladrave/skills.git
cd skills
git sparse-checkout set amazon-transaction-mcp/plugin
```

Provide the token to the Codex host process. Use a shell profile or trusted secret manager for
persistence; never write the token into this repository or the plugin files.

```bash
export AMAZON_TRANSACTION_MCP_TOKEN='<permanent bearer token>'
```

Register the cloned local marketplace and install the plugin:

```bash
codex plugin marketplace add "$PWD/amazon-transaction-mcp/plugin"
codex plugin add amazon-transaction-mcp@amazon-transactions
codex plugin list
```

Start a new Codex session after installation so the bundled skill and MCP server are loaded. A
safe first test is:

```text
Use $amazon-transaction-mcp to check Amazon authentication status without a live check.
```

Then test the bounded order workflow:

```text
Use $amazon-transaction-mcp to get last week's orders and the price for each item.
```

If a desktop-launched Codex process does not inherit shell variables, configure
`AMAZON_TRANSACTION_MCP_TOKEN` through that host's trusted environment or secret manager before
restarting the app. Do not replace it with credentials committed to `.mcp.json`.

## Install or use in ChatGPT

ChatGPT and Codex share the public plugin directory, but a private Git/local marketplace can vary
by surface.

For the ChatGPT desktop app, first perform the Codex marketplace registration above, restart the
desktop app, open **Plugins**, choose the **Amazon Transactions** marketplace, and install
**Amazon Transaction MCP**. Ensure the desktop host inherits
`AMAZON_TRANSACTION_MCP_TOKEN`, then start a new chat.

For ChatGPT on the web, use the already-supported private MCP connection:

1. Open **Settings → Security and login** and enable **Developer mode**.
2. Open **Plugins**, select the plus button, and create an MCP connection.
3. Use the permanent tokenized MCP URL recorded in the private
   `Amazon_transaction_mcp.md` Drive document and select **No Authentication**.
4. Select **Refresh** or **Scan tools** after connecting or after a deployment.
5. Start a new chat. The MCP hosts the same `amazon-transaction-mcp` skill, so ChatGPT imports
   the workflow together with the six Amazon tools.

The GitHub marketplace bundle is not a public-directory listing. One-click installation from the
universal ChatGPT/Codex plugin directory requires a separate OpenAI plugin submission and review.
A ChatGPT developer-mode connection also receives a workspace-specific `plugin_asdk_app...` ID;
that ID is deliberately not committed here.

## Update

Pull the repository, then reinstall the marketplace entry:

```bash
git pull --ff-only
codex plugin add amazon-transaction-mcp@amazon-transactions
```

Start a new Codex session or ChatGPT chat after reinstalling. In ChatGPT developer mode, also use
**Refresh** or **Scan tools** if MCP metadata or the hosted skill changed.

## Remove

```bash
codex plugin remove amazon-transaction-mcp@amazon-transactions
codex plugin marketplace remove amazon-transactions
```

Removing the plugin does not rotate the permanent MCP token or delete the server's persisted Amazon
cookies. Manage those only through the production runbook.

## Security notes

- Treat the bearer token and tokenized URL as passwords.
- Never paste the token into Git, screenshots, tickets, logs, or prompts.
- Never ask the user for their Amazon password; it is already stored server-side.
- OTP codes are single-use. Submit one only when `amazon_authenticate` returns `otp_required`.
- Stop automatic retries when authentication returns `operator_required`.
- Recipient, payment, and link fields remain disabled unless explicitly requested.
