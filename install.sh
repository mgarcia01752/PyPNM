#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified OS prerequisite installer and PyPNM bootstrapper
# Usage: ./install.sh [venv_dir]
# ────────────────────────────────────────────────────────────────────────────────

VENV_DIR="${1:-.env}"
PROJECT_ROOT="$(pwd)"

# ────────────────────────────────────────────────────────────────────────────────
# 1) Detect package manager and OS
# ────────────────────────────────────────────────────────────────────────────────
echo "🔍 Detecting package manager..."
if   command -v apt-get >/dev/null 2>&1; then
  PM="apt-get"; PM_UPDATE="sudo apt-get update";      PM_INSTALL="sudo apt-get install -y"
  echo "ℹ️  Detected Debian/Ubuntu (apt-get)"
elif command -v dnf     >/dev/null 2>&1; then
  PM="dnf";     PM_UPDATE="sudo dnf makecache";      PM_INSTALL="sudo dnf install -y"
  echo "ℹ️  Detected Fedora/RHEL (dnf)"
elif command -v yum     >/dev/null 2>&1; then
  PM="yum";     PM_UPDATE="sudo yum makecache";      PM_INSTALL="sudo yum install -y"
  echo "ℹ️  Detected RHEL/CentOS (yum)"
elif command -v zypper  >/dev/null 2>&1; then
  PM="zypper";  PM_UPDATE="sudo zypper refresh";     PM_INSTALL="sudo zypper install -y"
  echo "ℹ️  Detected SUSE/openSUSE (zypper)"
elif command -v apk     >/dev/null 2>&1; then
  PM="apk";     PM_UPDATE="";                        PM_INSTALL="sudo apk add --no-cache"
  echo "ℹ️  Detected Alpine (apk)"
elif command -v brew    >/dev/null 2>&1; then
  PM="brew";    PM_UPDATE="brew update";             PM_INSTALL="brew install"
  echo "ℹ️  Detected macOS (brew)"
else
  PM="none"
  echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."
fi

# ────────────────────────────────────────────────────────────────────────────────
# 2) Package installation helper
# ────────────────────────────────────────────────────────────────────────────────
install_package() {
  local logical_pkg="$1"; local cmd="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "🔧 Installing $logical_pkg..."
    case "$logical_pkg" in
      ssh)
        case "$PM" in
          apt-get) $PM_INSTALL openssh-client;;
          dnf|yum) $PM_INSTALL openssh-clients;;
          zypper)  $PM_INSTALL openssh;;
          apk)     $PM_INSTALL openssh;;
          brew)    $PM_INSTALL openssh;;
        esac;;
      sshpass)    $PM_INSTALL sshpass;;
      python3-venv)
        case "$PM" in
          apt-get) $PM_INSTALL python3-venv;;
          dnf|yum) $PM_INSTALL python3-virtualenv;;
          zypper)  $PM_INSTALL python3-virtualenv;;
          apk)     $PM_INSTALL python3;;
          brew)    $PM_INSTALL python;;
        esac;;
      *) echo "⚠️  Unknown package mapping for '$logical_pkg'";;
    esac
  fi
}

# ────────────────────────────────────────────────────────────────────────────────
# 3) Update package cache (if supported)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "$PM" != "none" && -n "${PM_UPDATE:-}" ]]; then
  echo "🔄 Updating package cache..."
  $PM_UPDATE || true
fi

# ────────────────────────────────────────────────────────────────────────────────
# 4) Ensure OS prerequisites
# ────────────────────────────────────────────────────────────────────────────────
echo "✅ Ensuring OS prerequisites are installed..."
install_package ssh        ssh
install_package sshpass    sshpass
install_package python3-venv python3

# ────────────────────────────────────────────────────────────────────────────────
# 5) Bootstrap PyPNM (editable + dev deps)
# ────────────────────────────────────────────────────────────────────────────────
echo "🛠  Creating virtual environment in '$VENV_DIR'…"
python3 -m venv "$VENV_DIR"

echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Upgrading pip, setuptools, wheel…"
pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM (with dev dependencies)…"
pip install -e "$PROJECT_ROOT"[dev]

echo "🔧 (Optional) Configuring PYTHONPATH…"
"$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT"

echo "🎉 Installation complete!"
echo "   Activate your venv any time with: source $VENV_DIR/bin/activate"
