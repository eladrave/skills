#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Google Chrome"
SELF_URL="${DROIDDESK_INSTALLER_URL:-https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-chrome.sh}"
NEEDS_MENU_SYNC=1
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-install-chrome.log"
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

  if (( NEEDS_MENU_SYNC )) && [[ -f "$HOME/proot-menu-sync.sh" ]]; then
    info "Synchronizing the DroidDesk application menu."
    bash "$HOME/proot-menu-sync.sh" "$distro" || warn "Installation succeeded, but menu synchronization failed. Run: bash ~/proot-menu-sync.sh $distro"
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
  [[ "$arch" == "arm64" ]] || die "This package requires arm64, but dpkg reports '$arch'."
}

download() {
  local url=$1 output=$2
  if ! curl --fail --show-error --location --retry 3 --retry-delay 2 --connect-timeout 20 --output "$output" "$url"; then
    die "Download failed: $url"
  fi
  [[ -s "$output" ]] || die "The downloaded file is empty: $url"
}

install_desktop_wrapper() {
  local wrapper_tmp desktop desktop_tmp
  wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
  cat > "$wrapper_tmp" <<'WRAPPER'
#!/usr/bin/env sh
# Chrome's normal Linux namespace sandbox cannot initialize inside Android PRoot.
exec /usr/bin/google-chrome-stable --no-sandbox "$@"
WRAPPER
  run_root install -m 0755 "$wrapper_tmp" /usr/local/bin/google-chrome-droiddesk

  desktop=/usr/share/applications/google-chrome.desktop
  [[ -f "$desktop" ]] || die "Chrome installed, but its desktop launcher was not found at $desktop."
  desktop_tmp=$(mktemp); TEMP_PATHS+=("$desktop_tmp")
  awk '
    /^Exec=(\/usr\/bin\/)?google-chrome(-stable)?([[:space:]]|$)/ {
      sub(/^Exec=(\/usr\/bin\/)?google-chrome(-stable)?/, "Exec=/usr/local/bin/google-chrome-droiddesk")
    }
    { print }
  ' "$desktop" > "$desktop_tmp"
  grep -q '^Exec=/usr/local/bin/google-chrome-droiddesk' "$desktop_tmp" || die "Could not update the Chrome desktop launcher."
  run_root install -m 0644 "$desktop_tmp" "$desktop"
}

main() {
  if is_termux_host; then
    run_from_termux
  fi

  require_arm64_debian
  require_root_access
  info "Installing prerequisites."
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update
  run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl

  local deb package_name package_arch version
  deb=$(mktemp --suffix=.deb); TEMP_PATHS+=("$deb")
  info "Downloading the official Google Chrome stable ARM64 package."
  download "https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb" "$deb"

  package_name=$(dpkg-deb --field "$deb" Package 2>/dev/null || true)
  package_arch=$(dpkg-deb --field "$deb" Architecture 2>/dev/null || true)
  [[ "$package_name" == "google-chrome-stable" ]] || die "Unexpected Debian package name '$package_name'. Refusing to install."
  [[ "$package_arch" == "arm64" ]] || die "Unexpected Debian package architecture '$package_arch'. Refusing to install."

  info "Installing $package_name."
  if ! run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"; then
    warn "The first installation attempt failed. Repairing package dependencies and retrying."
    run_root dpkg --configure -a || true
    run_root env DEBIAN_FRONTEND=noninteractive apt-get --fix-broken install -y
    run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"
  fi

  command -v google-chrome-stable >/dev/null 2>&1 || die "The package installed, but google-chrome-stable is not on PATH."
  version=$(google-chrome-stable --version 2>/dev/null || true)
  [[ -n "$version" ]] || die "Chrome was installed, but its version check failed."
  install_desktop_wrapper

  ok "Installed: $version"
  warn "Chrome must use --no-sandbox inside PRoot. Use it only for trusted sites because renderer isolation is disabled."
  if [[ "${DROIDDESK_INSTALL_FROM_HOST:-0}" != "1" ]]; then
    info "From the Termux host, synchronize the launcher with: bash ~/proot-menu-sync.sh"
  fi
}

main "$@"
