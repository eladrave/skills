# DroidDesk application installers

These standalone installers target ARM64 Android devices running DroidDesk. They can be invoked from the normal Termux shell or from inside DroidDesk's Debian-family PRoot environment.

## Install Google Chrome

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-chrome.sh | bash
```

Chrome's Linux sandbox cannot initialize inside Android PRoot. The installer creates a DroidDesk launcher that uses `--no-sandbox` and clearly reports the resulting security limitation.

## Install OpenAI Codex CLI

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-codex.sh | bash
```

After installation, authenticate with:

```bash
codex login --device-auth
```

The installer tests the Codex Linux sandbox. If Bubblewrap cannot initialize under PRoot, it adds an explicit `codex-proot` fallback that retains approval prompts but disables the OS sandbox. The normal `codex` command is never silently weakened.

## Install Warp Terminal

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-warp.sh | bash
```

Warp officially requires glibc 2.31 or newer and either OpenGL ES 3.0+ or Vulkan. The installer checks glibc, installs the ARM64 Debian package and graphics libraries, adds an X11/OpenGL compatibility wrapper, and synchronizes the DroidDesk launcher.

## Behavior shared by all installers

- Fail-fast error handling with a diagnostic log in the active temporary directory.
- ARM64 and Debian-family environment validation.
- Automatic detection of DroidDesk's configured PRoot distro when launched from Termux.
- HTTPS downloads with redirect handling, retries, and non-empty file validation.
- Package identity and architecture checks before installing downloaded Debian packages.
- Dependency repair and one controlled retry when `apt` reports a partial installation.
- Idempotent reinstallation and launcher updates.
