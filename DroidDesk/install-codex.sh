#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="OpenAI Codex CLI"
SELF_URL="${DROIDDESK_INSTALLER_URL:-https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-codex.sh}"
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-install-codex.log"
TEMP_PATHS=()
CODEX_HOST_COMMAND=""
CODEX_PROOT_HOST_COMMAND=""

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

is_standalone_droiddesk() {
  ! is_debian_environment && {
    [[ "${PREFIX:-}" == */com.orailnoor.droiddesk/files/usr ]] ||
      [[ "$HOME" == */com.orailnoor.droiddesk/files/home ]]
  }
}

standalone_prefix() {
  if [[ -n "${PREFIX:-}" ]]; then
    printf '%s\n' "$PREFIX"
  else
    printf '%s/usr\n' "${HOME%/home}"
  fi
}

has_codex_proot_fallback() {
  local launcher=$1
  "$launcher" <<'DROIDDESK_DEBIAN' >/dev/null 2>&1
test -x /usr/local/bin/codex-proot
DROIDDESK_DEBIAN
}

install_command_bridge() {
  local prefix=$1 requested_name=$2 inner_command=$3
  local target_name=$requested_name target wrapper_tmp
  target="$prefix/bin/$target_name"
  if [[ -e "$target" ]] && ! grep -q '^# DROIDDESK_CODEX_BRIDGE=1$' "$target" 2>/dev/null; then
    target_name="$requested_name-droiddesk"
    target="$prefix/bin/$target_name"
    warn "$prefix/bin/$requested_name already exists and was not overwritten. Creating '$target_name' instead."
  fi

  wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
  {
    printf '#!%s\n' "$prefix/bin/bash"
    printf '%s\n' '# DROIDDESK_CODEX_BRIDGE=1' 'set -Eeuo pipefail'
    printf 'PREFIX_PATH=%q\n' "$prefix"
    printf 'INNER_COMMAND=%q\n' "$inner_command"
    cat <<'BRIDGE'
BASE_DIR="${PREFIX_PATH%/usr}"
HOST_TMP="$BASE_DIR/tmp"
PROOT_BIN="$PREFIX_PATH/bin/proot-distro"
[[ -x "$PROOT_BIN" ]] || { printf '%s\n' '[ERROR] proot-distro is missing.' >&2; exit 1; }
[[ -d "$PWD" ]] || { printf '%s\n' '[ERROR] The current directory is unavailable.' >&2; exit 1; }
mkdir -p "$HOST_TMP/proot" "$HOST_TMP/droiddesk-workspace"
export TMPDIR="$HOST_TMP"
exec "$PROOT_BIN" login debian \
  --bind "$HOST_TMP:/tmp" \
  --bind "$PWD:/tmp/droiddesk-workspace" \
  --env PROOT_TMP_DIR="$HOST_TMP/proot" \
  --env PROOT_LOADER="$PREFIX_PATH/libexec/proot/loader" \
  --env PROOT_LOADER_32="$PREFIX_PATH/libexec/proot/loader32" -- \
  env DISPLAY="${DISPLAY:-:0}" TERM="${TERM:-xterm-256color}" \
  /bin/bash -c 'cd /tmp/droiddesk-workspace && exec "$0" "$@"' "$INNER_COMMAND" "$@"
BRIDGE
  } > "$wrapper_tmp"
  install -m 0755 "$wrapper_tmp" "$target"

  case "$requested_name" in
    codex) CODEX_HOST_COMMAND=$target_name ;;
    codex-proot) CODEX_PROOT_HOST_COMMAND=$target_name ;;
  esac
}

create_native_commands() {
  local prefix=$1 launcher=$2
  install_command_bridge "$prefix" codex /usr/local/bin/codex
  ok "Created interactive XFCE command: $CODEX_HOST_COMMAND"
  if has_codex_proot_fallback "$launcher"; then
    install_command_bridge "$prefix" codex-proot /usr/local/bin/codex-proot
    ok "Created explicit no-sandbox fallback command: $CODEX_PROOT_HOST_COMMAND"
    warn "$CODEX_PROOT_HOST_COMMAND retains approval prompts but has full access to files visible inside Debian PRoot."
  fi
}

run_from_standalone() {
  local prefix launcher version
  prefix=$(standalone_prefix)
  launcher="$prefix/bin/start-debian"
  command -v curl >/dev/null 2>&1 || die "curl is missing from DroidDesk's native environment. Install it from DroidDesk's Add applications screen."
  if [[ ! -x "$launcher" ]]; then
    die "The standalone DroidDesk APK needs its Debian PRoot first. In DroidDesk, open Add applications, install 'Debian (PRoot)', then rerun this command."
  fi

  info "Detected the standalone DroidDesk APK. Installing $APP_NAME inside its Debian PRoot."
  if ! { printf '%s\n' 'export DROIDDESK_INSTALL_FROM_HOST=1'; \
    curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 "$SELF_URL"; } | "$launcher"; then
    die "$APP_NAME installation inside the standalone DroidDesk Debian PRoot failed."
  fi
  create_native_commands "$prefix" "$launcher"
  version=$("$prefix/bin/$CODEX_HOST_COMMAND" --version 2>/dev/null || true)
  [[ -n "$version" ]] || die "The native Codex bridge was created, but its version check failed."
  ok "$APP_NAME installation completed inside Debian."
  ok "Native bridge verified: $version"
  info "From the XFCE terminal, authenticate with: $CODEX_HOST_COMMAND login --device-auth"
  exit 0
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
  if is_standalone_droiddesk; then
    run_from_standalone
  fi
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
