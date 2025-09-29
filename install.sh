#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified OS prerequisite installer and PyPNM bootstrapper
# Usage: ./install.sh [venv_dir]
# Env var: SKIP_UNIT_TEST=0 ./install.sh → run unit tests
# ────────────────────────────────────────────────────────────────────────────────

VENV_DIR="${1:-.env}"
PROJECT_ROOT="$(pwd)"
SKIP_UNIT_TEST="${SKIP_UNIT_TEST:-1}"  # default: skip tests

# ────────────────────────────────────────────────────────────────────────────────
# 1) Detect package manager and OS
# ────────────────────────────────────────────────────────────────────────────────
echo "🔍 Detecting package manager..."
if   command -v apt-get >/dev/null 2>&1; then
  PM="apt-get"; PM_UPDATE="sudo apt-get update"; PM_INSTALL="sudo apt-get install -y"
  echo "ℹ️  Detected Debian/Ubuntu (apt-get)"

elif command -v dnf >/dev/null 2>&1; then
  PM="dnf"; PM_UPDATE="sudo dnf makecache"; PM_INSTALL="sudo dnf install -y"
  echo "ℹ️  Detected Fedora/RHEL (dnf)"

elif command -v yum >/dev/null 2>&1; then
  PM="yum"; PM_UPDATE="sudo yum makecache"; PM_INSTALL="sudo yum install -y"
  echo "ℹ️  Detected RHEL/CentOS (yum)"

elif command -v zypper >/dev/null 2>&1; then
  PM="zypper"; PM_UPDATE="sudo zypper refresh"; PM_INSTALL="sudo zypper install -y"
  echo "ℹ️  Detected SUSE/openSUSE (zypper)"

elif command -v apk >/dev/null 2>&1; then
  PM="apk"; PM_UPDATE=""; PM_INSTALL="sudo apk add --no-cache"
  echo "ℹ️  Detected Alpine (apk)"

elif command -v brew >/dev/null 2>&1; then
  PM="brew"; PM_UPDATE="brew update"; PM_INSTALL="brew install"
  echo "ℹ️  Detected macOS (brew)"

else
  PM="none"
  echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."
fi

# ────────────────────────────────────────────────────────────────────────────────
# 2) Update package cache
# ────────────────────────────────────────────────────────────────────────────────
if [[ "$PM" != "none" && -n "${PM_UPDATE:-}" ]]; then
  echo "🔄 Updating package cache..."
  $PM_UPDATE || true
fi

# ────────────────────────────────────────────────────────────────────────────────
# 3) Install OS prerequisites
# ────────────────────────────────────────────────────────────────────────────────
echo "✅ Installing OS prerequisites..."

# ssh
if ! command -v ssh >/dev/null 2>&1; then
  echo "🔧 Installing ssh..."
  case "$PM" in
    apt-get) $PM_INSTALL openssh-client ;;
    dnf|yum) $PM_INSTALL openssh-clients ;;
    zypper|apk|brew) $PM_INSTALL openssh ;;
  esac
fi

# sshpass
if ! command -v sshpass >/dev/null 2>&1; then
  echo "🔧 Installing sshpass..."
  $PM_INSTALL sshpass
fi

# Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3.x not found. Please install Python before continuing."
  exit 1
fi

echo "🔧 Ensuring python3-venv is installed..."
case "$PM" in
  apt-get) $PM_INSTALL python3-venv ;;
  dnf|yum|zypper) $PM_INSTALL python3-virtualenv ;;
  apk)     $PM_INSTALL python3 ;;
  brew)    $PM_INSTALL python ;;
esac

# ────────────────────────────────────────────────────────────────────────────────
# 4) Bootstrap PyPNM
# ────────────────────────────────────────────────────────────────────────────────
echo "🛠  Creating virtual environment in '$VENV_DIR'…"
python3 -m venv "$VENV_DIR"

echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Upgrading pip, setuptools, wheel…"
python -m pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM (with dev dependencies)…"
python -m pip install -e "$PROJECT_ROOT"[dev]

echo "🔧 Configuring PYTHONPATH (if script exists)…"
if [[ -f "$PROJECT_ROOT/scripts/install_py_path.sh" ]]; then
  "$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT"
fi

# ────────────────────────────────────────────────────────────────────────────────
# 5) Run Unit Tests (optional)
# ────────────────────────────────────────────────────────────────────────────────
if [ "$SKIP_UNIT_TEST" -ne 1 ]; then
  echo "🧪 Running unit tests inside virtual environment…"
  cd "$PROJECT_ROOT" || exit 1
  python -m pytest -v
  TEST_EXIT_CODE=$?

  if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "❌ Unit tests failed. Please review the output above."
    deactivate
    exit $TEST_EXIT_CODE
  else
    echo "✅ All unit tests passed!"
  fi
fi
