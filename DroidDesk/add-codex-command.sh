#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Codex command bridge updater"
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-add-codex-command.log"
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
  printf '%s[ERROR]%s %s failed at line %s (exit %s).\n' "$RED" "$RESET" "$APP_NAME" "$line" "$status" >&2
  printf 'Diagnostic log: %s\n' "$LOG_FILE" >&2
  exit "$status"
}

trap cleanup EXIT
trap 'on_error "$LINENO"' ERR

if [[ -w "$LOG_DIR" ]]; then
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

standalone_prefix() {
  if [[ -n "${PREFIX:-}" ]]; then
    printf '%s\n' "$PREFIX"
  else
    printf '%s/usr\n' "${HOME%/home}"
  fi
}

verify_environment() {
  if [[ -r /etc/debian_version ]]; then
    die "Run this updater from the terminal inside DroidDesk's XFCE desktop, not from inside the Debian shell."
  fi
  if [[ "${PREFIX:-}" != */com.orailnoor.droiddesk/files/usr && "$HOME" != */com.orailnoor.droiddesk/files/home ]]; then
    die "The standalone DroidDesk APK was not detected. Run this from the terminal inside its XFCE desktop."
  fi
}

verify_codex_inside_debian() {
  local launcher=$1
  info "Verifying the existing Codex installation inside Debian PRoot."
  if ! "$launcher" <<'DROIDDESK_DEBIAN'; then
set -Eeuo pipefail
if [[ ! -x /usr/local/bin/codex ]]; then
  printf '%s\n' '[ERROR] Codex is not installed at /usr/local/bin/codex inside Debian PRoot.' >&2
  exit 44
fi
/usr/local/bin/codex --version
DROIDDESK_DEBIAN
    die "Codex could not be verified inside Debian. Install Codex first, then rerun this updater."
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

main() {
  local prefix launcher version
  (( $# == 0 )) || die "This script does not accept arguments."
  verify_environment
  prefix=$(standalone_prefix)
  launcher="$prefix/bin/start-debian"
  [[ -x "$launcher" ]] || die "Debian PRoot is required. In DroidDesk, open Add applications, install 'Debian (PRoot)', then rerun this command."
  command -v install >/dev/null 2>&1 || die "The native 'install' command is missing from DroidDesk."

  verify_codex_inside_debian "$launcher"
  create_native_commands "$prefix" "$launcher"
  version=$("$prefix/bin/$CODEX_HOST_COMMAND" --version 2>/dev/null || true)
  [[ -n "$version" ]] || die "The native Codex bridge was created, but its version check failed."
  ok "Native bridge verified: $version"
  info "Authenticate from this XFCE terminal with: $CODEX_HOST_COMMAND login --device-auth"
}

main "$@"
