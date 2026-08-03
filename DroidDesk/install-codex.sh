#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="OpenAI Codex CLI"
SELF_URL="${DROIDDESK_INSTALLER_URL:-https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-codex.sh}"
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-install-codex.log"
TEMP_PATHS=()

if [[ -t 1 ]]; then
  RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; BLUE=$'\033[0;34m'; RESET=$'\033[0m'
else
  RED=""; GREEN=""; YELLOW=""; BLUE=""; RESET=""
fi

info() { printf '%s[INFO]%s %s\n' "$BLUE" "$RESET" "$*"; }
ok() { printf '%s[ OK ]%s %s\n' "$GREEN" "$RESET" "$*"; }
warn() { printf '%s[WARN]%s %s\n' "$YELLOW" "$RESET" "$*" >&2; }
die() { printf '%s[ERROR]%s %s\n' "$RED" "$RESET" "$*" >&2; exit 1; }

cleanup() {
  local path
  for path in "${TEMP_PATHS[@]:-}"; do
    [[ -n "$path" ]] && rm -f -- "$path" 2>/dev/null || true
  done
}

on_error() {
  local status=$? line=${1:-unknown}
  printf '%s[ERROR]%s %s installation failed at line %s (exit %s).\n' "$RED" "$RESET" "$APP_NAME" "$line" "$status" >&2
  printf 'Diagnostic log: %s\n' "$LOG_FILE" >&2
  exit "$status"
}

trap cleanup EXIT
trap 'on_error "$LINENO"' ERR

if [[ -w "$LOG_DIR" ]]; then
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

is_debian_environment() {
  [[ -r /etc/debian_version ]] && command -v dpkg >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1
}

is_termux_host() {
  # Desktop terminals launched by DroidDesk do not always preserve Termux's
  # PREFIX variable. The generated PRoot launcher is the reliable marker.
  ! is_debian_environment && [[ -r "$HOME/start-proot.sh" ]]
}

configured_distro() {
  local launcher="$HOME/start-proot.sh" distro=""
  [[ -r "$launcher" ]] || return 1
  distro=$(sed -n 's/^PROOT_DISTRO="\([^"]*\)".*/\1/p' "$launcher" | head -n 1)
  [[ -n "$distro" ]] || return 1
  printf '%s\n' "$distro"
}

run_from_termux() {
  local distro
  command -v curl >/dev/null 2>&1 || die "curl is required in Termux. Install it with: pkg install curl"
  command -v proot-distro >/dev/null 2>&1 || die "proot-distro is missing. Re-run the DroidDesk setup or install it with: pkg install proot-distro"
  distro=$(configured_distro) || die "Could not determine PROOT_DISTRO from $HOME/start-proot.sh."
  proot-distro login "$distro" -- /bin/true >/dev/null 2>&1 || die "The configured PRoot distro '$distro' is not available."

  info "Detected the DroidDesk Termux host. Installing $APP_NAME inside PRoot '$distro'."
  if ! curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 "$SELF_URL" \
    | proot-distro login "$distro" --user root -- env DROIDDESK_INSTALL_FROM_HOST=1 bash -s; then
    die "$APP_NAME installation inside PRoot failed."
  fi
  ok "$APP_NAME installation completed."
  exit 0
}

run_root() {
  if (( EUID == 0 )); then
    "$@"
  else
    sudo -n "$@"
  fi
}

require_root_access() {
  if (( EUID != 0 )); then
    command -v sudo >/dev/null 2>&1 || die "Run this installer as root inside PRoot."
    sudo -n true >/dev/null 2>&1 || die "Passwordless sudo is unavailable. Start PRoot with: bash ~/start-proot.sh"
  fi
}

require_arm64_debian() {
  is_debian_environment || die "DroidDesk was not detected. Run this from the Termux host containing ~/start-proot.sh, or from inside its Debian-family PRoot."
  local arch
  arch=$(dpkg --print-architecture)
  [[ "$arch" == "arm64" ]] || die "This installer requires arm64, but dpkg reports '$arch'."
}

download() {
  local url=$1 output=$2
  if ! curl --fail --show-error --location --retry 3 --retry-delay 2 --connect-timeout 20 --output "$output" "$url"; then
    die "Download failed: $url"
  fi
  [[ -s "$output" ]] || die "The downloaded file is empty: $url"
}

install_proot_fallback() {
  local wrapper_tmp
  wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
  cat > "$wrapper_tmp" <<'WRAPPER'
#!/usr/bin/env sh
# PRoot can prevent Codex's Bubblewrap sandbox from initializing. This fallback
# preserves approval prompts but deliberately disables the Codex OS sandbox.
exec /usr/local/bin/codex --sandbox danger-full-access --ask-for-approval on-request "$@"
WRAPPER
  run_root install -m 0755 "$wrapper_tmp" /usr/local/bin/codex-proot
}

main() {
  if is_termux_host; then
    run_from_termux
  fi

  require_arm64_debian
  require_root_access
  info "Installing prerequisites."
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update
  run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl git

  local installer version sandbox_log
  installer=$(mktemp); TEMP_PATHS+=("$installer")
  info "Downloading the official OpenAI Codex installer."
  download "https://chatgpt.com/codex/install.sh" "$installer"
  grep -qi 'codex' "$installer" || die "The downloaded Codex installer did not have the expected contents."

  info "Installing Codex into /usr/local/bin."
  run_root env CODEX_NON_INTERACTIVE=1 CODEX_INSTALL_DIR=/usr/local/bin sh "$installer"
  [[ -x /usr/local/bin/codex ]] || die "The official installer completed, but /usr/local/bin/codex was not created."
  version=$(/usr/local/bin/codex --version 2>/dev/null || true)
  [[ -n "$version" ]] || die "Codex was installed, but its version check failed in this PRoot environment."
  ok "Installed: $version"

  sandbox_log=$(mktemp); TEMP_PATHS+=("$sandbox_log")
  info "Testing the Codex Linux command sandbox."
  if timeout 20 /usr/local/bin/codex sandbox linux -- /bin/true >"$sandbox_log" 2>&1; then
    ok "The Codex command sandbox initialized successfully."
    run_root rm -f /usr/local/bin/codex-proot
  else
    install_proot_fallback
    warn "The Codex Bubblewrap sandbox could not initialize under PRoot."
    warn "A fallback command was installed as: codex-proot"
    warn "codex-proot keeps approval prompts but has full access to files visible inside PRoot."
    if [[ -s "$sandbox_log" ]]; then
      warn "Sandbox diagnostic: $(tail -n 1 "$sandbox_log")"
    fi
  fi

  info "Authenticate with your ChatGPT account using: codex login --device-auth"
  info "Check authentication later using: codex login status"
}

main "$@"
