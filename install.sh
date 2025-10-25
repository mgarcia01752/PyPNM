#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified dev/production installer for PyPNM
#
# Usage:
#   ./install.sh [--dev-mode | --production] [venv_dir]
#   ./install.sh -h | --help
#
# Modes:
#   --dev-mode     Editable install with extras [dev,docs] (includes MkDocs), runs tests by default.
#   --production   Non-editable base install (no docs), skips tests by default.
#
# Env:
#   SKIP_UNIT_TEST=0   Force run unit tests (overrides mode default)
#   SKIP_UNIT_TEST=1   Force skip unit tests (overrides mode default)
# ────────────────────────────────────────────────────────────────────────────────

print_help() {
  cat <<'EOF'
PyPNM installer

Usage:
  ./install.sh [--dev-mode | --production] [venv_dir]
  ./install.sh -h | --help

Modes:
  --dev-mode     Editable install with developer & docs extras (installs [dev,docs]),
                 enables unit tests by default, ideal for local development.
  --production   Non-editable, base-only install (no docs), skips unit tests by default.
                 Suitable for deployment targets.

Arguments:
  venv_dir       Optional path to create/use the virtual environment.
                 Defaults: .env (dev mode), .venv (production mode)

Environment:
  SKIP_UNIT_TEST=0   Run unit tests after install (overrides mode default)
  SKIP_UNIT_TEST=1   Do not run unit tests (overrides mode default)

Examples:
  ./install.sh --dev-mode
  ./install.sh --dev-mode .env-dev
  SKIP_UNIT_TEST=0 ./install.sh --production /opt/pypnm-venv

Notes:
  - The script attempts to detect your OS package manager and install prerequisites:
    ssh, sshpass, and Python venv support. If detection fails, install them manually.
EOF
}

# Defaults (overridden by args)
MODE="production"
VENV_DIR_DEFAULT_DEV=".env"
VENV_DIR_DEFAULT_PROD=".venv"

# Parse args
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --dev-mode)
      MODE="dev"; shift ;;
    --production)
      MODE="production"; shift ;;
    -*)
      echo "Unknown option: $1" >&2
      echo "Try './install.sh --help' for usage." >&2
      exit 2
      ;;
    *)
      ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]:-}"

# Resolve venv path
if [[ $# -ge 1 ]]; then
  VENV_DIR="$1"
else
  VENV_DIR=$([[ "$MODE" == "dev" ]] && echo "$VENV_DIR_DEFAULT_DEV" || echo "$VENV_DIR_DEFAULT_PROD")
fi

PROJECT_ROOT="$(pwd)"

# Decide test behavior
if [[ -z "${SKIP_UNIT_TEST:-}" ]]; then
  if [[ "$MODE" == "dev" ]]; then
    SKIP_UNIT_TEST=0
  else
    SKIP_UNIT_TEST=1
  fi
fi

echo "Mode: $MODE"
echo "Venv: $VENV_DIR"
echo "Skip unit tests: $SKIP_UNIT_TEST"

# ────────────────────────────────────────────────────────────────────────────────
# Detect package manager and basic OS deps
# ────────────────────────────────────────────────────────────────────────────────
PM="none"; PM_UPDATE=""; PM_INSTALL=""

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
  echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."
fi

# Update package cache
if [[ "$PM" != "none" && -n "${PM_UPDATE:-}" ]]; then
  echo "🔄 Updating package cache..."
  $PM_UPDATE || true
fi

echo "✅ Installing OS prerequisites..."

# OpenSSH client
if ! command -v ssh >/dev/null 2>&1; then
  echo "🔧 Installing ssh..."
  case "$PM" in
    apt-get) $PM_INSTALL openssh-client ;;
    dnf|yum) $PM_INSTALL openssh-clients ;;
    zypper|apk|brew) $PM_INSTALL openssh ;;
    none) echo "Please install OpenSSH client manually."; ;;
  esac
fi

# sshpass (note: on macOS it's in a tap)
if ! command -v sshpass >/dev/null 2>&1; then
  echo "🔧 Installing sshpass..."
  case "$PM" in
    apt-get|dnf|yum|zypper|apk) $PM_INSTALL sshpass || true ;;
    brew)
      if ! brew list sshpass >/dev/null 2>&1; then
        brew install hudochenkov/sshpass/sshpass || true
      fi
      ;;
    none) echo "Please install sshpass manually."; ;;
  esac
fi

# Python 3.x
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3.x not found. Please install Python before continuing."
  exit 1
fi

# venv / virtualenv support
echo "🔧 Ensuring Python venv support..."
case "$PM" in
  apt-get) $PM_INSTALL python3-venv || true ;;
  dnf|yum|zypper) $PM_INSTALL python3-virtualenv || true ;;
  apk) $PM_INSTALL python3 py3-virtualenv || true ;;
  brew) $PM_INSTALL python || true ;;
esac

# ────────────────────────────────────────────────────────────────────────────────
# Bootstrap PyPNM
# ────────────────────────────────────────────────────────────────────────────────
echo "🛠  Creating virtual environment in '$VENV_DIR'…"
python3 -m venv "$VENV_DIR"

echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Upgrading pip, setuptools, wheel…"
python -m pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM …"
if [[ "$MODE" == "dev" ]]; then
  # Editable install with dev + docs (MkDocs) extras
  python -m pip install -e "$PROJECT_ROOT"[dev,docs]
else
  # Non-editable base install for production
  python -m pip install "$PROJECT_ROOT"
fi

echo "🔧 Configuring PYTHONPATH (if script exists)…"
if [[ -f "$PROJECT_ROOT/scripts/install_py_path.sh" ]]; then
  "$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Run Unit Tests (optional)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "${SKIP_UNIT_TEST}" -ne 1 ]]; then
  echo "🧪 Running unit tests inside virtual environment…"
  cd "$PROJECT_ROOT"
  python -m pytest -v
  TEST_EXIT_CODE=$?
  if [[ $TEST_EXIT_CODE -ne 0 ]]; then
    echo "❌ Unit tests failed. Please review the output above."
    deactivate
    exit $TEST_EXIT_CODE
  else
    echo "✅ All unit tests passed!"
  fi
fi

echo "🎉 Done."
