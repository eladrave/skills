# DroidDesk application installers

These installers target ARM64 Android devices running [DroidDesk](https://github.com/orailnoor/DroidDesk). They support:

- The standalone DroidDesk APK and its optional Debian PRoot environment.
- The older Termux plus Termux-X11 setup with a generated `~/start-proot.sh` launcher.
- Direct execution from inside a Debian-family PRoot environment.

## Standalone DroidDesk prerequisite

On a non-rooted phone using the standalone DroidDesk APK, first open **Add applications** in DroidDesk and install **Debian (PRoot)**.

Every installer checks for DroidDesk's generated `$PREFIX/bin/start-debian` launcher. If Debian PRoot is missing, the installer stops without changing anything and tells you how to add it.

Official Linux packages such as Chrome and Warp require glibc and cannot run directly in DroidDesk's native Android/Bionic environment. PRoot provides the required Debian environment without rooting the phone.

## Available installers

| Script | Purpose | Special handling |
|---|---|---|
| `install-deb.sh` | Install a local ARM64 or architecture-independent `.deb` package | Validates metadata and architecture, installs dependencies, verifies installation, and bridges eligible GUI launchers into the DroidDesk menu |
| `install-chrome.sh` | Install Google Chrome stable for ARM64 | Adds the required `--no-sandbox` PRoot launcher and a native DroidDesk menu entry |
| `add-chrome-shortcut.sh` | Add shortcuts for an existing Chrome installation | Does not reinstall Chrome; creates both an XFCE application-menu entry and desktop icon |
| `install-codex.sh` | Install OpenAI Codex CLI | Tests the Codex sandbox and creates an explicit `codex-proot` fallback when required |
| `install-warp.sh` | Install Warp Terminal for ARM64 | Checks glibc, adds graphics environment settings, and creates a native DroidDesk menu entry |

## Install a local `.deb` package

Pass the package path after `bash -s --`. The `--` separates Bash options from the package filename.

Android normally stores downloaded files in `/storage/emulated/0/Download`:

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
  | bash -s -- "/storage/emulated/0/Download/application.deb"
```

Paths containing spaces are supported when quoted:

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
  | bash -s -- "/storage/emulated/0/Download/My Application.deb"
```

The shorthand `/Downloads/filename.deb` and `/Download/filename.deb` are also recognized. When possible, the installer resolves them to Android's actual Downloads directory and reports the resolved path.

When already inside Debian PRoot, supply the path visible from Debian:

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
  | bash -s -- "/tmp/application.deb"
```

The generic installer performs the following checks and actions:

1. Confirms that exactly one readable, non-empty file was provided.
2. Detects standalone DroidDesk, the older Termux host, or Debian PRoot.
3. Checks that Debian PRoot was installed from **Add applications** when using standalone DroidDesk.
4. Copies the package through DroidDesk's Debian-visible temporary directory when necessary.
5. Validates the Debian archive, package name, version, and architecture.
6. Accepts packages matching Debian's current architecture, normally `arm64`, or architecture-independent `all` packages.
7. Displays the package SHA-256 checksum when `sha256sum` is available.
8. Uses `apt-get` to install the local package and resolve repository dependencies.
9. Repairs partial dependency state and retries once if the first installation fails.
10. Verifies that `dpkg` reports the package as fully installed.
11. Creates native DroidDesk UI menu bridges for eligible `.desktop` launchers when invoked from the standalone APK.
12. Removes temporary package copies and menu metadata.

The package itself must come from a trusted source. Debian packages can execute maintainer scripts as root during installation.

## Install Google Chrome

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-chrome.sh | bash
```

On the standalone APK, the installer adds **Google Chrome (Debian)** to the DroidDesk UI menu and refreshes the XFCE panel. You can also run Chrome from the Debian terminal with:

```bash
google-chrome-droiddesk
```

Chrome's normal Linux namespace sandbox cannot initialize inside Android PRoot. The installer creates a launcher using `--no-sandbox`. This weakens renderer isolation, so Chrome should only be used with trusted sites in this environment.

### Add shortcuts without reinstalling Chrome

If Chrome is already installed, run this from DroidDesk's normal terminal, not from inside the Debian shell:

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/add-chrome-shortcut.sh | bash
```

This verifies the existing Debian Chrome installation, recreates the `--no-sandbox` compatibility wrapper, adds **Google Chrome (Debian)** to the XFCE application menu, creates a desktop icon, and refreshes the panel and desktop. It does not download or reinstall Chrome.

## Install OpenAI Codex CLI

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-codex.sh | bash
```

Authenticate after installation:

```bash
codex login --device-auth
```

Check authentication later:

```bash
codex login status
```

The installer tests whether the Codex Linux command sandbox can initialize under PRoot. If it cannot, the installer creates `codex-proot`. That fallback retains Codex approval prompts but deliberately disables its operating-system sandbox. The normal `codex` command is never silently weakened.

## Install Warp Terminal

```bash
curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-warp.sh | bash
```

On the standalone APK, the installer adds **Warp Terminal (Debian)** to the DroidDesk UI menu and refreshes the XFCE panel. You can also run Warp from the Debian terminal with:

```bash
warp-terminal-droiddesk
```

Warp requires glibc 2.31 or newer and either OpenGL ES 3.0 or newer, or Vulkan. Installation can succeed even when a phone's GPU stack cannot render Warp correctly.

## Shared behavior

All installers provide:

- Fail-fast error handling with a diagnostic log in the active temporary directory.
- Automatic environment detection and handoff into Debian PRoot.
- ARM64 and Debian-family validation where applicable.
- HTTPS downloads with redirects, retries, and empty-download detection.
- Package identity and architecture validation before installing downloaded packages.
- One controlled dependency-repair attempt when `apt` reports a partial installation.
- Idempotent package reinstallation and native menu-bridge updates.

## Troubleshooting

### Debian PRoot is missing

If the installer reports that `$PREFIX/bin/start-debian` is missing:

1. Return to the DroidDesk main interface.
2. Open **Add applications**.
3. Install **Debian (PRoot)**.
4. Open the terminal and rerun the installer command.

### Package path was not found

Confirm the downloaded filename:

```bash
ls -l /storage/emulated/0/Download
```

Then pass the complete quoted path. Android uses `Download` in the filesystem path, not `Downloads`.

If DroidDesk cannot read the directory, confirm that Android storage access is enabled for the DroidDesk application.

### Package architecture is incompatible

DroidDesk phones normally require an ARM64 package marked `arm64`. Packages marked `amd64`, `x86_64`, `i386`, or `armhf` cannot be installed by this script. Packages marked `all` are accepted.

### Package installed but does not start

Installation and runtime compatibility are different. A package may depend on systemd, Linux namespaces, kernel interfaces, hardware acceleration, or sandboxing that Android PRoot does not provide. Use a specialized installer when application-specific adjustments are needed.

### Application is not visible in the UI menu

For Chrome and Warp, rerun the specialized installer. It recreates the native bridge and restarts the XFCE panel.

The generic installer creates menu items only for package-owned `.desktop` files that contain a visible name and executable command. Command-line packages, hidden launchers, and packages without `.desktop` files are intentionally not added to the UI menu.

Standalone menu bridges are stored under:

```text
~/.local/share/applications/droiddesk-debian/
~/.local/share/droiddesk-debian-wrappers/
```

Applications launched from these entries run inside Debian PRoot. Their logs are written to the active native temporary directory as `droiddesk-<application>.log`.

### Review the diagnostic log

The scripts write logs to the active temporary directory. Typical paths are:

```text
/tmp/droiddesk-install-deb.log
/tmp/droiddesk-install-chrome.log
/tmp/droiddesk-add-chrome-shortcut.log
/tmp/droiddesk-install-codex.log
/tmp/droiddesk-install-warp.log
```
