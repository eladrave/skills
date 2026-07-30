# SimpleFIN Finance

A skills-only ChatGPT and Codex plugin that retrieves read-only account balances
and transactions from SimpleFIN Bridge. It includes a zero-dependency Python
client suitable for interactive analysis and local desktop scheduled tasks.

## Security model

- The SimpleFIN Setup Token is entered only into a local password-style prompt.
- The resulting Access URL is saved in `.simplefin/access-url` with mode `0600`.
- Credentials are removed from request URLs and sent only in the HTTPS
  `Authorization` header.
- Credentials are never printed or included in JSON results.
- The client accepts HTTPS endpoints only and defaults to `*.simplefin.org`.
- The integration is read-only.

Do not commit `.simplefin/access-url`. Add `.simplefin/` to the project
`.gitignore`.

## Automatic first-use setup

When the skill is invoked interactively, it first checks whether SimpleFIN is
configured. If configuration is missing, it asks for a one-time Setup Token,
claims it through the client's hidden terminal prompt, stores the resulting
Access URL, verifies the connection, and continues the original request.

The Setup Token can be pasted into the interactive ChatGPT conversation because
the skill claims it immediately and it becomes invalid after a successful
claim. Never paste the long-lived Access URL into ChatGPT.

Unattended scheduled runs cannot complete this interactive step. Run the skill
once interactively before enabling its schedule.

## Manual setup alternative

1. Create a Setup Token at
   <https://bridge.simplefin.org/simplefin/create>.
2. In the project that the scheduled task will use, run:

   ```bash
   python3 /path/to/simplefin-finance/skills/simplefin-finance/scripts/simplefin.py setup
   ```

3. Paste the token into the private terminal prompt. The command claims it once
   and stores the Access URL at `.simplefin/access-url`.
4. Add the secret directory to the project's ignore file:

   ```text
   .simplefin/
   ```

5. Test account access:

   ```bash
   python3 /path/to/simplefin-finance/skills/simplefin-finance/scripts/simplefin.py accounts
   ```

## Test the client

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills tests
```

The tests use mocked HTTPS responses and never require a real SimpleFIN token.

## Scheduled-task boundary

This version is intended for a ChatGPT/Codex desktop scheduled task attached to
a local project. The computer and desktop app must be running, the project must
remain available, and the task must have permission to run Python and make
outbound HTTPS requests.

A web-only cloud scheduled task does not have access to the project's local
secret file. Supporting that execution mode requires a hosted authenticated MCP
server or another documented cloud secret-injection mechanism.
