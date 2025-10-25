#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified OS prerequisite installer and PyPNM bootstrapper
# Usage: ./install.sh [venv_dir]
# ────────────────────────────────────────────────────────────────────────────────

VENV_DIR="${1:-.env}"
PROJECT_ROOT="$(pwd)"
SKIP_UNIT_TEST="${SKIP_UNIT_TEST:-1}"  # 1 = skip tests (default), 0 = run tests

# ────────────────────────────────────────────────────────────────────────────────
# 1) Detect package manager and OS
# ────────────────────────────────────────────────────────────────────────────────
echo "🔍 Detecting package manager..."
PM="none"; PM_UPDATE=""; PM_INSTALL=""

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
  echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."
fi

# ────────────────────────────────────────────────────────────────────────────────
# 2) Update package cache (if supported)
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
  if [[ "$PM" == "none" ]]; then
    echo "⚠️  Package manager not detected; cannot auto-install 'ssh'."
  else
    echo "🔧 Installing ssh..."
    case "$PM" in
      apt-get) $PM_INSTALL openssh-client ;;
      dnf|yum) $PM_INSTALL openssh-clients ;;
      zypper)  $PM_INSTALL openssh       ;;
      apk)     $PM_INSTALL openssh       ;;
      brew)    $PM_INSTALL openssh       ;;
    esac
  fi
fi

# sshpass
if ! command -v sshpass >/dev/null 2>&1; then
  if [[ "$PM" == "none" ]]; then
    echo "⚠️  Package manager not detected; cannot auto-install 'sshpass'."
  else
    echo "🔧 Installing sshpass..."
    # Note: On macOS, sshpass may be unavailable in official taps.
    $PM_INSTALL sshpass || echo "⚠️  Could not install sshpass automatically; continuing."
  fi
fi

# Python detection and venv install
PYTHON_VERSION="$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3")"
PYTHON_CMD="python${PYTHON_VERSION}"
PYTHON_VENV_PKG="python${PYTHON_VERSION}-venv"

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  # Fallback to plain python3 if python3.X isn't present
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
  else
    echo "❌ Python 3.x is not installed or not in PATH."
    echo "   Please install Python 3.x before running this script."
    exit 1
  fi
fi

echo "🔧 Ensuring venv support is available..."
case "$PM" in
  apt-get) $PM_INSTALL "$PYTHON_VENV_PKG" || true ;;
  dnf|yum) $PM_INSTALL python3-virtualenv || true ;;
  zypper)  $PM_INSTALL python3-virtualenv || true ;;
  apk)     $PM_INSTALL python3 || true ;;
  brew)    $PM_INSTALL python || true ;;
  *)       echo "⚠️ Unknown/unsupported package manager for Python venv setup; assuming it's present." ;;
esac

# ────────────────────────────────────────────────────────────────────────────────
# 4) Bootstrap PyPNM (editable + dev deps)
# ────────────────────────────────────────────────────────────────────────────────
echo "🛠  Creating virtual environment in '$VENV_DIR'…"
"$PYTHON_CMD" -m venv "$VENV_DIR"

echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Upgrading pip, setuptools, wheel…"
pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM (with dev dependencies)…"
pip install -e "$PROJECT_ROOT"[dev]

echo "🔧 (Optional) Configuring PYTHONPATH…"
"$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT" || true

# ────────────────────────────────────────────────────────────────────────────────
# 5) Run Unit Tests (optional)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "${SKIP_UNIT_TEST:-1}" -ne 1 ]]; then
  echo "🧪 Running unit tests inside virtual environment…"

  if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "⚠️  Virtual environment not active. Activating now…"
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
  fi

  cd "$PROJECT_ROOT"

  # Run tests now, then capture exit code
  if command -v pytest >/dev/null 2>&1; then
    pytest -v
    TEST_EXIT_CODE=$?
  else
    echo "⚠️  pytest not found; installing…"
    pip install pytest
    pytest -v
    TEST_EXIT_CODE=$?
  fi

  if [[ $TEST_EXIT_CODE -ne 0 ]]; then
    echo "❌ Unit tests failed. Please review the output above."
    deactivate || true
    exit "$TEST_EXIT_CODE"
  else
    echo "✅ All unit tests passed!"
  fi
else
  echo "⏭️  Skipping unit tests (set SKIP_UNIT_TEST=0 to enable)."
fi
