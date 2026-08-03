#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Google Chrome shortcut updater"
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-add-chrome-shortcut.log"
TEMP_PATHS=()

if [[ -t 1 ]]; then
  RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; BLUE=$'\033[0;34m'; RESET=$'\033[0m'
else
  RED=""; GREEN=""; BLUE=""; RESET=""
fi

info() { printf '%s[INFO]%s %s\n' "$BLUE" "$RESET" "$*"; }
ok() { printf '%s[ OK ]%s %s\n' "$GREEN" "$RESET" "$*"; }
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
    die "Run this shortcut updater from DroidDesk's normal terminal, not from inside the Debian shell."
  fi
  if [[ "${PREFIX:-}" != */com.orailnoor.droiddesk/files/usr && "$HOME" != */com.orailnoor.droiddesk/files/home ]]; then
    die "The standalone DroidDesk APK was not detected. Run this from its normal terminal."
  fi
}

prepare_chrome_inside_debian() {
  local launcher=$1
  info "Verifying the existing Chrome installation inside Debian PRoot."
  if ! "$launcher" <<'DROIDDESK_DEBIAN'; then
set -Eeuo pipefail
if [[ ! -x /usr/bin/google-chrome-stable ]]; then
  printf '%s\n' '[ERROR] Google Chrome is not installed inside Debian PRoot.' >&2
  exit 44
fi

install -d -m 0755 /usr/local/bin
cat > /usr/local/bin/google-chrome-droiddesk <<'CHROME_WRAPPER'
#!/usr/bin/env sh
# Chrome's normal Linux namespace sandbox cannot initialize inside Android PRoot.
exec /usr/bin/google-chrome-stable --no-sandbox "$@"
CHROME_WRAPPER
chmod 0755 /usr/local/bin/google-chrome-droiddesk

desktop=/usr/share/applications/google-chrome.desktop
if [[ -f "$desktop" ]]; then
  desktop_tmp=$(mktemp)
  trap 'rm -f -- "$desktop_tmp"' EXIT
  awk '
    /^Exec=(\/usr\/bin\/)?google-chrome(-stable)?([[:space:]]|$)/ {
      sub(/^Exec=(\/usr\/bin\/)?google-chrome(-stable)?/, "Exec=/usr/local/bin/google-chrome-droiddesk")
    }
    { print }
  ' "$desktop" > "$desktop_tmp"
  install -m 0644 "$desktop_tmp" "$desktop"
fi

/usr/bin/google-chrome-stable --version
DROIDDESK_DEBIAN
    die "Chrome could not be verified inside Debian. Install Chrome first, then rerun this shortcut updater."
  fi
}

create_native_shortcuts() {
  local prefix=$1 launcher rootfs menu_dir wrapper_dir desktop_dir
  local wrapper menu_entry desktop_entry icon_value icon_candidate wrapper_tmp desktop_tmp
  launcher="$prefix/bin/start-debian"
  rootfs="$prefix/var/lib/proot-distro/installed-rootfs/debian"
  menu_dir="$HOME/.local/share/applications/droiddesk-debian"
  wrapper_dir="$HOME/.local/share/droiddesk-debian-wrappers"
  desktop_dir="$HOME/Desktop"
  wrapper="$wrapper_dir/google-chrome.sh"
  menu_entry="$menu_dir/droiddesk-debian-google-chrome.desktop"
  desktop_entry="$desktop_dir/Google Chrome (Debian).desktop"
  mkdir -p "$menu_dir" "$wrapper_dir" "$desktop_dir" "${prefix%/usr}/tmp"

  wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
  {
    printf '#!%s\n' "$prefix/bin/bash"
    printf '%s\n' 'set -uo pipefail'
    printf 'START_DEBIAN=%q\n' "$launcher"
    printf 'DEFAULT_LOG_DIR=%q\n' "${prefix%/usr}/tmp"
    cat <<'NATIVE_WRAPPER'
APP_COMMAND=/usr/local/bin/google-chrome-droiddesk
LOG_DIR="${TMPDIR:-$DEFAULT_LOG_DIR}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="$DEFAULT_LOG_DIR"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/droiddesk-google-chrome.log"
{
  printf 'exec %s' "$APP_COMMAND"
  for argument in "$@"; do
    printf ' %q' "$argument"
  done
  printf '\n'
} | "$START_DEBIAN" >> "$LOG_FILE" 2>&1
status=$?
if (( status != 0 )) && command -v notify-send >/dev/null 2>&1; then
  notify-send "Google Chrome failed" "See $LOG_FILE"
fi
exit "$status"
NATIVE_WRAPPER
  } > "$wrapper_tmp"
  install -m 0755 "$wrapper_tmp" "$wrapper"

  icon_value="application-x-executable"
  for icon_candidate in \
    "$rootfs/opt/google/chrome/product_logo_128.png" \
    "$rootfs/usr/share/icons/hicolor/128x128/apps/google-chrome.png" \
    "$rootfs/usr/share/pixmaps/google-chrome.png"; do
    if [[ -f "$icon_candidate" ]]; then
      icon_value="$icon_candidate"
      break
    fi
  done

  desktop_tmp=$(mktemp); TEMP_PATHS+=("$desktop_tmp")
  {
    printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Version=1.0'
    printf '%s\n' 'Name=Google Chrome (Debian)'
    printf '%s\n' 'Comment=Google Chrome running inside DroidDesk Debian PRoot'
    printf 'Exec=%s %%U\n' "$wrapper"
    printf 'TryExec=%s\n' "$wrapper"
    printf 'Icon=%s\n' "$icon_value"
    printf '%s\n' 'Terminal=false' 'Categories=Network;WebBrowser;' 'StartupNotify=true' 'NoDisplay=false' 'X-DroidDesk-PRoot=true'
  } > "$desktop_tmp"
  install -m 0644 "$desktop_tmp" "$menu_entry"
  install -m 0755 "$desktop_tmp" "$desktop_entry"

  if command -v gio >/dev/null 2>&1; then
    gio set -t string "$desktop_entry" metadata::trusted true >/dev/null 2>&1 || true
  fi
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
  if command -v pgrep >/dev/null 2>&1 && pgrep -x xfce4-panel >/dev/null 2>&1; then
    xfce4-panel --restart >/dev/null 2>&1 &
  fi
  if command -v xfdesktop >/dev/null 2>&1; then
    xfdesktop --reload >/dev/null 2>&1 || true
  fi

  ok "Added Google Chrome (Debian) to the DroidDesk UI menu."
  ok "Created desktop shortcut: $desktop_entry"
}

main() {
  local prefix launcher
  (( $# == 0 )) || die "This script does not accept arguments."
  verify_environment
  prefix=$(standalone_prefix)
  launcher="$prefix/bin/start-debian"
  [[ -x "$launcher" ]] || die "Debian PRoot is required. In DroidDesk, open Add applications, install 'Debian (PRoot)', then rerun this command."
  command -v install >/dev/null 2>&1 || die "The native 'install' command is missing from DroidDesk."

  prepare_chrome_inside_debian "$launcher"
  create_native_shortcuts "$prefix"
  info "Use the Google Chrome (Debian) icon from the desktop or application menu."
}

main "$@"
