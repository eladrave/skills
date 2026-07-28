---
name: remote-browser-access
description: Route website work through the Remote Browser MCP plugin. Use whenever an agent needs to access amazon.com or any Amazon account, order, purchase, or product page; when the user explicitly requests Remote Browser, Remote Chrome, or the remote browser plugin; or when the OpenAI/ChatGPT cloud browser is blocked, denied, challenged, unable to load a site, or lacks the required authenticated session.
---

# Remote Browser Access

Use the `remote browser` plugin for persistent, remote Chrome access. Treat the routing rules below as mandatory.

## Route the browser task

1. For `amazon.com` and its subdomains, use Remote Browser from the start.
   - Do not try the OpenAI/ChatGPT cloud browser first.
   - Do not silently substitute another browser if Remote Browser is unavailable.
   - Apply this rule to Amazon product research, orders, purchases, returns, account pages, and sign-in flows.
2. For another site, switch to Remote Browser as soon as the cloud browser is blocked, denied, challenged, repeatedly times out, cannot load the required page, or does not have the needed authenticated session.
   - Do not keep retrying the same blocked route.
   - Restart the browser portion of the task in Remote Browser because sessions and cookies are not shared between browsers.
3. If the user explicitly requests `@remote browser`, Remote Browser, Remote Chrome, or the Remote Browser MCP, use only that plugin for the website interaction.

## Verify availability

Before taking a website action that requires Remote Browser:

- Check the callable tools for the `remote browser` plugin. Typical tools include `remote_browser_browser_tabs`, `remote_browser_browser_snapshot`, and `remote_browser_browser_navigate`; exact prefixes may vary.
- Do not treat this skill, a plugin mention, or remembered configuration as proof that the plugin is installed and callable.
- If no Remote Browser tools are callable, stop the browser task. Tell the user that the Remote Browser plugin is not available or installed and must be set up first. Refer them to [Remote Chrome MCP setup instructions](https://github.com/eladrave/remotechromemcpfor), and explain that the repository is private, so their GitHub account must have access.
- If the plugin requests connection, reconnection, or authorization, stop and ask the user to complete that step before continuing.
- Never claim to have used Remote Browser unless its tools were actually called successfully.

## Operate the remote session

1. List tabs first and reuse a relevant existing tab when possible. This preserves the remote browser's authenticated session and cookies.
2. Capture an accessibility snapshot before interacting. Use element references from the current snapshot for clicks, typing, and form actions.
3. For Amazon:
   - Prefer an existing authenticated Amazon tab.
   - Otherwise navigate to `https://www.amazon.com/`.
   - Do not navigate directly to `/ap/signin`. Start from the Amazon home page and use `Account & Lists` when sign-in is required.
4. After navigation or a material page change, take a fresh snapshot before the next action.
5. If navigation times out, take another snapshot before deciding whether to retry. The page may have loaded despite the timeout.
6. Use screenshots only for visual inspection. Use accessibility snapshots to identify actionable elements.
7. If login, MFA, CAPTCHA, or another human verification is required, ask the user to complete it in the remote browser, then continue from a fresh snapshot. Do not ask the user to paste credentials into chat when interactive sign-in is available.
8. Follow normal confirmation rules for purchases, submissions, deletions, or other consequential actions.

When reporting results, lead with the requested outcome. Mention browser routing only when it explains a blocker or the user asks which browser was used.
