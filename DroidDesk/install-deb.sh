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

encode_menu_field() {
  printf '%s' "$1" | base64 | tr -d '\n'
}

resolve_desktop_icon() {
  local icon=$1 candidate extension size
  [[ -n "$icon" ]] || return 1
  if [[ "$icon" == /* && -f "$icon" ]]; then
    printf '%s\n' "$icon"
    return 0
  fi
  for size in 512 256 192 128 96 64 48 32; do
    for extension in png svg xpm; do
      candidate="/usr/share/icons/hicolor/${size}x${size}/apps/${icon}.${extension}"
      if [[ -f "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done
  done
  for candidate in "/usr/share/pixmaps/$icon" "/usr/share/pixmaps/$icon.png" "/usr/share/pixmaps/$icon.svg"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  find /usr/share/icons /usr/share/pixmaps -type f \
    \( -name "$icon" -o -name "$icon.png" -o -name "$icon.svg" -o -name "$icon.xpm" \) \
    -print -quit 2>/dev/null
}

export_desktop_entries() {
  local package_name=$1 manifest=${DROIDDESK_MENU_MANIFEST:-}
  local desktop desktop_id name command icon terminal categories icon_path
  [[ -n "$manifest" ]] || return 0
  command -v base64 >/dev/null 2>&1 || { warn "Cannot export menu entries because base64 is missing inside Debian."; return 0; }
  : > "$manifest" || { warn "Cannot write the DroidDesk menu manifest: $manifest"; return 0; }

  while IFS= read -r desktop; do
    [[ -f "$desktop" ]] || continue
    grep -qi '^NoDisplay=true$' "$desktop" && continue
    grep -qi '^Hidden=true$' "$desktop" && continue
    desktop_id=$(basename "$desktop" .desktop)
    desktop_id=$(printf '%s' "$desktop_id" | tr -c 'a-zA-Z0-9._-' '-')
    name=$(sed -n 's/^Name=//p' "$desktop" | head -n 1)
    command=$(sed -n 's/^Exec=//p' "$desktop" | head -n 1)
    icon=$(sed -n 's/^Icon=//p' "$desktop" | head -n 1)
    terminal=$(sed -n 's/^Terminal=//p' "$desktop" | head -n 1)
    categories=$(sed -n 's/^Categories=//p' "$desktop" | head -n 1)
    [[ -n "$name" && -n "$command" ]] || continue
    command=$(printf '%s' "$command" | sed -E 's/[[:space:]]*%[fFuUdDnNickvm]//g; s/%%/%/g')
    [[ -n "$command" ]] || continue
    icon_path=$(resolve_desktop_icon "$icon" || true)
    [[ "$terminal" == "true" ]] || terminal="false"
    [[ -n "$categories" ]] || categories="Utility;"
    printf '%s|%s|%s|%s|%s|%s\n' \
      "$desktop_id" \
      "$(encode_menu_field "$name")" \
      "$(encode_menu_field "$command")" \
      "$(encode_menu_field "$icon_path")" \
      "$terminal" \
      "$(encode_menu_field "$categories")" >> "$manifest"
  done < <(dpkg-query -L "$package_name" 2>/dev/null | awk '/\/share\/applications\/[^/]+\.desktop$/')
}

decode_menu_field() {
  printf '%s' "$1" | base64 -d 2>/dev/null
}

install_standalone_menu_bridges() {
  local manifest=$1 prefix=$2 launcher rootfs desktop_dir wrapper_dir
  local desktop_id name64 command64 icon64 terminal categories64
  local name command icon_guest categories icon_value wrapper desktop wrapper_tmp desktop_tmp count=0

  [[ -s "$manifest" ]] || { warn "The package installed no eligible GUI desktop entries, so no DroidDesk menu item was added."; return 0; }
  command -v base64 >/dev/null 2>&1 || { warn "The package installed, but the native base64 command is missing, so its menu entry could not be created."; return 0; }
  launcher="$prefix/bin/start-debian"
  rootfs="$prefix/var/lib/proot-distro/installed-rootfs/debian"
  desktop_dir="$HOME/.local/share/applications/droiddesk-debian"
  wrapper_dir="$HOME/.local/share/droiddesk-debian-wrappers"
  mkdir -p "$desktop_dir" "$wrapper_dir"

  while IFS='|' read -r desktop_id name64 command64 icon64 terminal categories64; do
    [[ "$desktop_id" =~ ^[a-zA-Z0-9._-]+$ ]] || { warn "Skipping an invalid desktop entry identifier: $desktop_id"; continue; }
    name=$(decode_menu_field "$name64") || { warn "Skipping '$desktop_id': invalid encoded name."; continue; }
    command=$(decode_menu_field "$command64") || { warn "Skipping '$desktop_id': invalid encoded command."; continue; }
    icon_guest=$(decode_menu_field "$icon64") || icon_guest=""
    categories=$(decode_menu_field "$categories64") || categories="Utility;"
    [[ -n "$name" && -n "$command" ]] || continue
    [[ "$terminal" == "true" ]] || terminal="false"
    [[ -n "$categories" ]] || categories="Utility;"

    wrapper="$wrapper_dir/$desktop_id.sh"
    desktop="$desktop_dir/droiddesk-debian-$desktop_id.desktop"
    wrapper_tmp=$(mktemp); TEMP_PATHS+=("$wrapper_tmp")
    {
      printf '#!%s\n' "$prefix/bin/bash"
      printf '%s\n' 'set -uo pipefail'
      printf 'START_DEBIAN=%q\n' "$launcher"
      printf 'DEFAULT_LOG_DIR=%q\n' "${prefix%/usr}/tmp"
      printf 'APP_COMMAND=%q\n' "$command"
      printf 'APP_ID=%q\n' "$desktop_id"
      cat <<'WRAPPER'
LOG_DIR="${TMPDIR:-$DEFAULT_LOG_DIR}"
[[ -d "$LOG_DIR" ]] || LOG_DIR="$DEFAULT_LOG_DIR"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/droiddesk-$APP_ID.log"
{
  printf 'exec %s' "$APP_COMMAND"
  for argument in "$@"; do
    printf ' %q' "$argument"
  done
  printf '\n'
} | "$START_DEBIAN" >> "$LOG_FILE" 2>&1
status=$?
if (( status != 0 )) && command -v notify-send >/dev/null 2>&1; then
  notify-send "DroidDesk Debian application failed" "See $LOG_FILE"
fi
exit "$status"
WRAPPER
    } > "$wrapper_tmp"
    install -m 0755 "$wrapper_tmp" "$wrapper"

    icon_value="application-x-executable"
    if [[ "$icon_guest" == /* && -f "$rootfs$icon_guest" ]]; then
      icon_value="$rootfs$icon_guest"
    fi
    desktop_tmp=$(mktemp); TEMP_PATHS+=("$desktop_tmp")
    {
      printf '%s\n' '[Desktop Entry]'
      printf '%s\n' 'Type=Application' 'Version=1.0'
      printf 'Name=%s (Debian)\n' "$name"
      printf '%s\n' 'Comment=Runs inside DroidDesk Debian PRoot'
      printf 'Exec=%s %%U\n' "$wrapper"
      printf 'TryExec=%s\n' "$wrapper"
      printf 'Icon=%s\n' "$icon_value"
      printf 'Terminal=%s\n' "$terminal"
      printf 'Categories=%s\n' "$categories"
      printf '%s\n' 'StartupNotify=true' 'NoDisplay=false' 'X-DroidDesk-PRoot=true'
    } > "$desktop_tmp"
    install -m 0644 "$desktop_tmp" "$desktop"
    count=$((count + 1))
  done < "$manifest"

  if (( count > 0 )); then
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
    if command -v pgrep >/dev/null 2>&1 && pgrep -x xfce4-panel >/dev/null 2>&1; then
      xfce4-panel --restart >/dev/null 2>&1 &
    fi
    ok "Added $count Debian application launcher(s) to the DroidDesk UI menu."
  else
    warn "No usable DroidDesk UI menu launchers could be created."
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
  local source_path prefix launcher shared_tmp staged guest_path manifest guest_manifest
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
  manifest=$(mktemp "$shared_tmp/droiddesk-menu.XXXXXX") || die "Could not create a temporary menu manifest."
  TEMP_PATHS+=("$manifest")
  cp -- "$source_path" "$staged" || die "Could not copy the package into DroidDesk's Debian-visible temporary directory."
  [[ -s "$staged" ]] || die "The supplied package is empty: $source_path"
  guest_path="/tmp/${staged##*/}"
  guest_manifest="/tmp/${manifest##*/}"

  info "Detected the standalone DroidDesk APK."
  info "Copying the package into Debian PRoot and starting installation."
  if ! {
    printf '%s\n' 'export DROIDDESK_INSTALL_FROM_HOST=1'
    printf 'export DROIDDESK_MENU_MANIFEST=%q\n' "$guest_manifest"
    printf 'set -- %q\n' "$guest_path"
    curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 "$SELF_URL"
  } | "$launcher"; then
    die "Package installation inside DroidDesk's Debian PRoot failed."
  fi
  install_standalone_menu_bridges "$manifest" "$prefix"
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
  if [[ -f "$HOME/proot-menu-sync.sh" ]]; then
    info "Synchronizing the DroidDesk application menu."
    bash "$HOME/proot-menu-sync.sh" "$distro" || warn "Installation succeeded, but menu synchronization failed. Run: bash ~/proot-menu-sync.sh $distro"
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
  export_desktop_entries "$PACKAGE_NAME"
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
