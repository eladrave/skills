#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Warp Terminal"
SELF_URL="${DROIDDESK_INSTALLER_URL:-https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-warp.sh}"
NEEDS_MENU_SYNC=1
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-install-warp.log"
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
  [[ "${PREFIX:-}" == *com.termux* ]] && ! is_debian_environment
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
  is_debian_environment || die "This installer supports DroidDesk's Debian, Ubuntu, or Kali PRoot environments."
  local arch
  arch=$(dpkg --print-architecture)
  [[ "$arch" == "arm64" ]] || die "The Warp package requires arm64, but dpkg reports '$arch'."
}

download() {
  local url=$1 output=$2
  if ! curl --fail --show-error --location --retry 3 --retry-delay 2 --connect-timeout 20 --output "$output" "$url"; then
    die "Download failed: $url"
  fi
  [[ -s "$output" ]] || die "The downloaded file is empty: $url"
}

check_glibc() {
  local glibc
  glibc=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $NF}' || true)
  [[ -n "$glibc" ]] || die "Could not determine the glibc version. Warp requires glibc 2.31 or newer."
  dpkg --compare-versions "$glibc" ge 2.31 || die "Warp requires glibc 2.31 or newer, but this PRoot has $glibc."
  ok "glibc $glibc satisfies Warp's minimum requirement."
}

install_desktop_wrapper() {
  local wrapper_tmp desktop desktop_tmp
  wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
  cat > "$wrapper_tmp" <<'WRAPPER'
#!/usr/bin/env sh
# Warp uses wgpu. The GL backend is the most compatible option with DroidDesk's
# Termux-X11 and Mesa setup.
export WGPU_BACKEND="${WGPU_BACKEND:-gl}"
if [ -z "${XDG_RUNTIME_DIR:-}" ] || [ "$XDG_RUNTIME_DIR" = "/tmp" ]; then
  XDG_RUNTIME_DIR="/tmp/xdg-runtime-$(id -u)"
  export XDG_RUNTIME_DIR
  mkdir -p "$XDG_RUNTIME_DIR"
  chmod 0700 "$XDG_RUNTIME_DIR" 2>/dev/null || true
fi
exec /usr/bin/warp-terminal "$@"
WRAPPER
  run_root install -m 0755 "$wrapper_tmp" /usr/local/bin/warp-terminal-droiddesk

  desktop=$(find /usr/share/applications -maxdepth 1 -type f -iname '*warp*.desktop' -print -quit)
  [[ -n "$desktop" && -f "$desktop" ]] || die "Warp installed, but no Warp desktop launcher was found in /usr/share/applications."
  desktop_tmp=$(mktemp); TEMP_PATHS+=("$desktop_tmp")
  awk '
    /^Exec=(\/usr\/bin\/)?warp-terminal([[:space:]]|$)/ {
      sub(/^Exec=(\/usr\/bin\/)?warp-terminal/, "Exec=/usr/local/bin/warp-terminal-droiddesk")
    }
    { print }
  ' "$desktop" > "$desktop_tmp"
  grep -q '^Exec=/usr/local/bin/warp-terminal-droiddesk' "$desktop_tmp" || die "Could not update the Warp desktop launcher."
  run_root install -m 0644 "$desktop_tmp" "$desktop"
}

main() {
  if is_termux_host; then
    run_from_termux
  fi

  require_arm64_debian
  require_root_access
  check_glibc
  info "Installing Warp graphics and runtime prerequisites."
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update
  run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates curl dbus-x11 libegl1 libgl1 libgles2 libvulkan1 mesa-utils

  local deb package_name package_arch version
  deb=$(mktemp --suffix=.deb); TEMP_PATHS+=("$deb")
  info "Downloading the official Warp Terminal ARM64 Debian package."
  download "https://app.warp.dev/download?package=deb_arm64" "$deb"

  package_name=$(dpkg-deb --field "$deb" Package 2>/dev/null || true)
  package_arch=$(dpkg-deb --field "$deb" Architecture 2>/dev/null || true)
  [[ "$package_name" == "warp-terminal" ]] || die "Unexpected Debian package name '$package_name'. Refusing to install."
  [[ "$package_arch" == "arm64" ]] || die "Unexpected Debian package architecture '$package_arch'. Refusing to install."

  info "Installing $package_name."
  if ! run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"; then
    warn "The first installation attempt failed. Repairing package dependencies and retrying."
    run_root dpkg --configure -a || true
    run_root env DEBIAN_FRONTEND=noninteractive apt-get --fix-broken install -y
    run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"
  fi

  [[ -x /usr/bin/warp-terminal ]] || die "The package installed, but /usr/bin/warp-terminal was not created."
  version=$(dpkg-query -W -f='${Version}' warp-terminal 2>/dev/null || true)
  [[ -n "$version" ]] || die "Warp installed, but its package version could not be verified."
  install_desktop_wrapper

  ok "Installed Warp Terminal $version."
  warn "Warp requires OpenGL ES 3.0+ or Vulkan. Installation can succeed even if a particular phone's GPU stack cannot render Warp."
  if [[ -n "${DISPLAY:-}" ]] && command -v glxinfo >/dev/null 2>&1; then
    if timeout 10 glxinfo -B >/dev/null 2>&1; then
      ok "The active X11 session exposes an OpenGL renderer."
    else
      warn "The active X11 OpenGL check failed. Warp may need DroidDesk GPU troubleshooting."
    fi
  fi
  if [[ "${DROIDDESK_INSTALL_FROM_HOST:-0}" != "1" ]]; then
    info "From the Termux host, synchronize the launcher with: bash ~/proot-menu-sync.sh"
  fi
}

main "$@"
