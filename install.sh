#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified OS prerequisite installer and PyPNM bootstrapper
# Usage: ./install.sh [venv_dir]
# Env:   SKIP_UNIT_TEST=0 to run tests (default 1 = skip)
# ────────────────────────────────────────────────────────────────────────────────

VENV_DIR="${1:-.env}"
PROJECT_ROOT="$(pwd)"
SKIP_UNIT_TEST="${SKIP_UNIT_TEST:-1}"  # 1=skip tests (default), 0=run tests

echo "🔍 Detecting package manager..."
PM="none"; PM_UPDATE=""; PM_INSTALL=""
if   command -v apt-get >/dev/null 2>&1;  then PM="apt-get"; PM_UPDATE="sudo apt-get update";  PM_INSTALL="sudo apt-get install -y";  echo "ℹ️  Debian/Ubuntu (apt-get)"
elif command -v dnf      >/dev/null 2>&1; then PM="dnf";     PM_UPDATE="sudo dnf makecache";    PM_INSTALL="sudo dnf install -y";     echo "ℹ️  Fedora/RHEL (dnf)"
elif command -v yum      >/dev/null 2>&1; then PM="yum";     PM_UPDATE="sudo yum makecache";    PM_INSTALL="sudo yum install -y";     echo "ℹ️  RHEL/CentOS (yum)"
elif command -v zypper   >/dev/null 2>&1; then PM="zypper";  PM_UPDATE="sudo zypper refresh";   PM_INSTALL="sudo zypper install -y";  echo "ℹ️  SUSE/openSUSE (zypper)"
elif command -v apk      >/dev/null 2>&1; then PM="apk";                                        PM_INSTALL="sudo apk add --no-cache"; echo "ℹ️  Alpine (apk)"
elif command -v brew     >/dev/null 2>&1; then PM="brew";    PM_UPDATE="brew update";           PM_INSTALL="brew install";            echo "ℹ️  macOS (brew)"
else echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."; fi

if [[ "$PM" != "none" && -n "${PM_UPDATE:-}" ]]; then
  echo "🔄 Updating package cache..."; $PM_UPDATE || true
fi

echo "✅ Installing OS prerequisites..."
if ! command -v ssh >/dev/null 2>&1; then
  if [[ "$PM" == "none" ]]; then echo "⚠️  No package manager; cannot auto-install 'ssh'."
  else
    echo "🔧 Installing ssh..."
    case "$PM" in
      apt-get) $PM_INSTALL openssh-client ;;
      dnf|yum) $PM_INSTALL openssh-clients ;;
      zypper)  $PM_INSTALL openssh ;;
      apk)     $PM_INSTALL openssh ;;
      brew)    $PM_INSTALL openssh ;;
    esac
  fi
fi

if ! command -v sshpass >/dev/null 2>&1; then
  if [[ "$PM" == "none" ]]; then echo "⚠️  No package manager; cannot auto-install 'sshpass'."
  else
    echo "🔧 Installing sshpass..."
    $PM_INSTALL sshpass || echo "⚠️  Could not install sshpass automatically; continuing."
  fi
fi

PYTHON_VERSION="$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3")"
PYTHON_CMD="python${PYTHON_VERSION}"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then PYTHON_CMD="python3"
  else echo "❌ Python 3.x not found in PATH."; exit 1; fi
fi

echo "🔧 Ensuring venv support is available..."
case "$PM" in
  apt-get) $PM_INSTALL "python${PYTHON_VERSION}-venv" || true ;;
  dnf|yum) $PM_INSTALL python3-virtualenv || true ;;
  zypper)  $PM_INSTALL python3-virtualenv || true ;;
  apk)     $PM_INSTALL python3 || true ;;
  brew)    $PM_INSTALL python || true ;;
  *)       echo "⚠️  Skipping venv package install for unknown PM." ;;
esac

echo "🛠  Creating virtual environment in '$VENV_DIR'…"
"$PYTHON_CMD" -m venv "$VENV_DIR"

echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Upgrading pip, setuptools, wheel…"
pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM extras: dev + docs…"
# IMPORTANT: includes mkdocs, mkdocs-material, pymdown-extensions from [docs]
pip install -e "$PROJECT_ROOT"[dev,docs]

echo "🔎 Verifying MkDocs install…"
if command -v mkdocs >/dev/null 2>&1; then
  mkdocs --version
else
  echo "❌ mkdocs not found in PATH even after install."
  echo "   Try: pip install 'mkdocs>=1.6' 'mkdocs-material>=9.5' && hash -r"
  exit 1
fi

echo "🔧 (Optional) Configuring PYTHONPATH…"
"$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT" || true

if [[ "${SKIP_UNIT_TEST:-1}" -ne 1 ]]; then
  echo "🧪 Running unit tests…"
  if [[ -z "${VIRTUAL_ENV:-}" ]]; then source "$VENV_DIR/bin/activate"; fi
  cd "$PROJECT_ROOT"
  if ! command -v pytest >/dev/null 2>&1; then pip install pytest; fi
  pytest -v
  echo "✅ All unit tests passed!"
else
  echo "⏭️  Skipping unit tests (set SKIP_UNIT_TEST=0 to enable)."
fi

echo "✅ Bootstrap complete."
echo "👉 Next: source '$VENV_DIR/bin/activate' and try: mkdocs serve"
