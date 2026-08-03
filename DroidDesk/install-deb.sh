#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Debian package installer"
SELF_URL="${DROIDDESK_INSTALLER_URL:-https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh}"
LOG_DIR="${TMPDIR:-/tmp}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/droiddesk-install-deb.log"
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

usage() {
  cat <<'USAGE'
Usage:
  curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
    | bash -s -- /path/to/package.deb

Examples:
  curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
    | bash -s -- /storage/emulated/0/Download/application.deb

  curl -fsSL https://raw.githubusercontent.com/eladrave/skills/main/DroidDesk/install-deb.sh \
    | bash -s -- "/storage/emulated/0/Download/My Application.deb"

The package must target ARM64 (arm64) or be architecture-independent (all).
USAGE
}

cleanup() {
  local path
  for path in "${TEMP_PATHS[@]:-}"; do
    [[ -n "$path" ]] && rm -f -- "$path" 2>/dev/null || true
  done
}

on_error() {
  local status=$? line=${1:-unknown}
  printf '%s[ERROR]%s %s failed at line %s (exit %s).\n' "$RED" "$RESET" "$APP_NAME" "$line" "$status" >&2
  if [[ -n "${LOG_FILE:-}" ]]; then
    printf 'Diagnostic log: %s\n' "$LOG_FILE" >&2
  fi
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

require_one_argument() {
  if (( $# != 1 )); then
    usage >&2
    die "Pass exactly one local .deb package path."
  fi
}

resolve_input_file() {
  local requested=$1 relative candidate

  if [[ -e "$requested" && ! -f "$requested" ]]; then
    die "The supplied path is not a regular file: $requested"
  fi
  if [[ -f "$requested" ]]; then
    [[ -r "$requested" ]] || die "The package exists but is not readable: $requested"
    printf '%s\n' "$requested"
    return 0
  fi

  case "$requested" in
    /Downloads/*)
      relative=${requested#/Downloads/}
      ;;
    /Download/*)
      relative=${requested#/Download/}
      ;;
    *)
      relative=""
      ;;
  esac

  if [[ -n "$relative" ]]; then
    for candidate in \
      "/storage/emulated/0/Download/$relative" \
      "/sdcard/Download/$relative" \
      "$HOME/storage/downloads/$relative"; do
      if [[ -f "$candidate" && -r "$candidate" ]]; then
        warn "Resolved '$requested' to Android's Downloads location: $candidate"
        printf '%s\n' "$candidate"
        return 0
      fi
    done
  fi

  die "Package not found or not readable: $requested. Android downloads are normally under /storage/emulated/0/Download/."
}

configured_distro() {
  local launcher="$HOME/start-proot.sh" distro=""
  [[ -r "$launcher" ]] || return 1
  distro=$(sed -n 's/^PROOT_DISTRO="\([^"]*\)".*/\1/p' "$launcher" | head -n 1)
  [[ -n "$distro" ]] || return 1
  printf '%s\n' "$distro"
}

run_from_standalone() {
  local source_path prefix launcher shared_tmp staged guest_path
  source_path=$1
  prefix=$(standalone_prefix)
  launcher="$prefix/bin/start-debian"
  shared_tmp="${prefix%/usr}/tmp"

  command -v curl >/dev/null 2>&1 || die "curl is missing. Install it from DroidDesk's Add applications screen."
  if [[ ! -x "$launcher" ]]; then
    die "Debian PRoot is required. In DroidDesk, open Add applications, install 'Debian (PRoot)', then rerun this command."
  fi

  mkdir -p "$shared_tmp" || die "Could not create DroidDesk's shared temporary directory: $shared_tmp"
  staged=$(mktemp "$shared_tmp/droiddesk-package.XXXXXX") || die "Could not create a temporary package file."
  TEMP_PATHS+=("$staged")
  cp -- "$source_path" "$staged" || die "Could not copy the package into DroidDesk's Debian-visible temporary directory."
  [[ -s "$staged" ]] || die "The supplied package is empty: $source_path"
  guest_path="/tmp/${staged##*/}"

  info "Detected the standalone DroidDesk APK."
  info "Copying the package into Debian PRoot and starting installation."
  if ! {
    printf '%s\n' 'export DROIDDESK_INSTALL_FROM_HOST=1'
    printf 'set -- %q\n' "$guest_path"
    curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 "$SELF_URL"
  } | "$launcher"; then
    die "Package installation inside DroidDesk's Debian PRoot failed."
  fi
  exit 0
}

run_from_termux() {
  local source_path distro guest_path
  source_path=$1
  guest_path="/tmp/droiddesk-package-$$.deb"

  command -v curl >/dev/null 2>&1 || die "curl is required in Termux. Install it with: pkg install curl"
  command -v proot-distro >/dev/null 2>&1 || die "proot-distro is missing. Re-run the DroidDesk setup or install it with: pkg install proot-distro"
  distro=$(configured_distro) || die "Could not determine PROOT_DISTRO from $HOME/start-proot.sh."
  proot-distro login "$distro" -- /bin/true >/dev/null 2>&1 || die "The configured PRoot distro '$distro' is not available."

  info "Detected the DroidDesk Termux host. Installing inside PRoot '$distro'."
  if ! curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 "$SELF_URL" \
    | proot-distro login "$distro" --user root --bind "$source_path:$guest_path" -- \
      env DROIDDESK_INSTALL_FROM_HOST=1 bash -s -- "$guest_path"; then
    die "Package installation inside PRoot '$distro' failed."
  fi
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
    sudo -n true >/dev/null 2>&1 || die "Passwordless sudo is unavailable. Enter the Debian PRoot as root and retry."
  fi
}

require_debian() {
  is_debian_environment || die "Unsupported environment. Run this from DroidDesk, its Termux host, or inside its Debian-family PRoot."
  command -v dpkg-deb >/dev/null 2>&1 || die "dpkg-deb is missing from this Debian environment."
  command -v dpkg-query >/dev/null 2>&1 || die "dpkg-query is missing from this Debian environment."
}

validate_package() {
  local deb=$1 package_name package_version package_arch system_arch

  dpkg-deb --info "$deb" >/dev/null 2>&1 || die "The supplied file is not a valid Debian binary package: $deb"
  package_name=$(dpkg-deb --field "$deb" Package 2>/dev/null || true)
  package_version=$(dpkg-deb --field "$deb" Version 2>/dev/null || true)
  package_arch=$(dpkg-deb --field "$deb" Architecture 2>/dev/null || true)
  system_arch=$(dpkg --print-architecture)

  [[ "$package_name" =~ ^[a-z0-9][a-z0-9+.-]*$ ]] || die "The package contains an invalid package name: '$package_name'."
  [[ -n "$package_version" ]] || die "The package does not declare a version."
  [[ "$package_arch" == "$system_arch" || "$package_arch" == "all" ]] ||
    die "Package '$package_name' targets '$package_arch', but this Debian environment is '$system_arch'."

  PACKAGE_NAME=$package_name
  PACKAGE_VERSION=$package_version
  PACKAGE_ARCH=$package_arch
}

show_checksum() {
  local deb=$1 checksum
  if command -v sha256sum >/dev/null 2>&1; then
    checksum=$(sha256sum "$deb" | awk '{print $1}')
    info "SHA-256: $checksum"
  fi
}

install_package() {
  local deb=$1 installed_status installed_version desktop_count

  info "Refreshing Debian package metadata."
  run_root env DEBIAN_FRONTEND=noninteractive apt-get update

  info "Installing $PACKAGE_NAME $PACKAGE_VERSION ($PACKAGE_ARCH) and its dependencies."
  if ! run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"; then
    warn "The first installation attempt failed. Repairing package dependencies and retrying once."
    run_root dpkg --configure -a || true
    run_root env DEBIAN_FRONTEND=noninteractive apt-get --fix-broken install -y
    run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$deb"
  fi

  installed_status=$(dpkg-query -W -f='${db:Status-Abbrev}' "$PACKAGE_NAME" 2>/dev/null || true)
  installed_version=$(dpkg-query -W -f='${Version}' "$PACKAGE_NAME" 2>/dev/null || true)
  [[ "$installed_status" == "ii " ]] || die "apt completed, but '$PACKAGE_NAME' is not fully installed (status: '${installed_status:-missing}')."
  [[ -n "$installed_version" ]] || die "Could not verify the installed version of '$PACKAGE_NAME'."

  ok "Installed $PACKAGE_NAME $installed_version."
  desktop_count=$(dpkg-query -L "$PACKAGE_NAME" 2>/dev/null | awk '/^\/usr\/share\/applications\/.*\.desktop$/ { count++ } END { print count+0 }')
  if (( desktop_count > 0 )); then
    info "The package installed $desktop_count desktop launcher(s). Reopen DroidDesk's Debian applications list if they are not immediately visible."
  fi
  warn "Installation does not guarantee runtime compatibility with Android PRoot. Packages may still require application-specific flags, libraries, graphics support, systemd, or unavailable kernel features."
}

main() {
  local requested source_path
  require_one_argument "$@"
  requested=$1
  if ! source_path=$(resolve_input_file "$requested"); then
    exit 1
  fi

  if is_standalone_droiddesk; then
    run_from_standalone "$source_path"
  fi
  if is_termux_host; then
    run_from_termux "$source_path"
  fi

  require_debian
  require_root_access
  [[ -s "$source_path" ]] || die "The supplied package is empty: $source_path"
  [[ "$source_path" == *.deb ]] || warn "The filename does not end in .deb. Validating its contents anyway."
  show_checksum "$source_path"
  validate_package "$source_path"
  info "Validated package: $PACKAGE_NAME $PACKAGE_VERSION ($PACKAGE_ARCH)."
  warn "Debian packages execute maintainer scripts as root. Install packages only from sources you trust."
  install_package "$source_path"
}

main "$@"
