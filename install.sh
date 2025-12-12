#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# install.sh — Unified OS prerequisite installer and PyPNM bootstrapper
# Usage: ./install.sh [--demo-mode | --production] [--pnm-file-retrieval-setup] [venv_dir]
# ────────────────────────────────────────────────────────────────────────────────

VENV_DIR=".env"
DEMO_MODE="0"
PRODUCTION_MODE="0"
PNM_FILE_RETRIEVAL_SETUP="0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

usage() {
  cat <<EOF
PyPNM Installer And Bootstrap Script

Usage:
  ./install.sh [--demo-mode | --production] [--pnm-file-retrieval-setup] [venv_dir]
  ./install.sh --help

Options:
  --demo-mode     Enable demo mode by backing up the default
                  src/pypnm/settings/system.json into backup/src/pypnm/settings/system.json
                  and replacing it with demo/settings/system.json. The demo system.json
                  should point all relevant directories to the demo/ tree.

  --production    Revert to production settings by restoring the backed-up
                  backup/src/pypnm/settings/system.json back to
                  src/pypnm/settings/system.json. This assumes a prior backup exists
                  (created by running with --demo-mode or a normal install).

  --pnm-file-retrieval-setup
                  After installation completes, attempt to run the interactive
                  PNM File Retrieval setup helper:

                      tools/pnm_file_retrieval_setup.py

                  This lets you choose how PyPNM retrieves PNM files:
                  local / tftp / ftp / scp / sftp / http / https.

                  For CI safety, this step is only executed when:
                    • stdin is a TTY (real terminal), and
                    • CI/GITHUB_ACTIONS are not set.
                  In CI environments, the option is acknowledged but skipped.

  venv_dir        Optional virtual environment directory name. Defaults to ".env".

  --help, -h      Show this help message and exit.

Examples:
  ./install.sh
      Create a venv in ".env" and install PyPNM with dev/docs extras.

  ./install.sh .pyenv
      Create a venv in ".pyenv" instead of ".env".

  ./install.sh --demo-mode
      Install and then switch system.json to the demo configuration
      (backing up the current system.json first).

  ./install.sh --demo-mode .env-demo
      Create a venv in ".env-demo" and enable demo-mode system.json.

  ./install.sh --production
      Install and then restore system.json from the backup tree, returning
      the configuration to production mode.

  ./install.sh --pnm-file-retrieval-setup
      Install and then invoke the PNM File Retrieval setup helper at the end,
      when running in an interactive, non-CI environment.

After installation, you can also configure how PyPNM retrieves PNM files
(local/TFTP/FTP/SCP/SFTP/HTTP/HTTPS) manually by running:

  ./tools/pnm_file_retrieval_setup.py
EOF
}

for arg in "$@"; do
  case "$arg" in
    --demo-mode)
      DEMO_MODE="1"
      ;;
    --production)
      PRODUCTION_MODE="1"
      ;;
    --pnm-file-retrieval-setup)
      PNM_FILE_RETRIEVAL_SETUP="1"
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      VENV_DIR="$arg"
      ;;
  esac
done

if [[ "$DEMO_MODE" == "1" && "$PRODUCTION_MODE" == "1" ]]; then
  echo "❌ Cannot use --demo-mode and --production together."
  usage
  exit 1
fi

backup_system_settings() {
  echo "🗂  Creating backup of system settings…"
  local backup_root
  backup_root="${PROJECT_ROOT}/backup"
  local src_path
  src_path="${PROJECT_ROOT}/src/pypnm/settings/system.json"
  local dst_path
  dst_path="${backup_root}/src/pypnm/settings/system.json"

  if [[ ! -f "$src_path" ]]; then
    echo "⚠️  System settings file not found at '$src_path'; skipping backup."
    return
  fi

  mkdir -p "$(dirname "$dst_path")"
  cp "$src_path" "$dst_path"
  echo "✅ Backup created at '$dst_path'."
}

restore_system_settings() {
  echo "🗂  Restoring system settings from backup…"
  local backup_root
  backup_root="${PROJECT_ROOT}/backup"
  local backup_path
  backup_path="${backup_root}/src/pypnm/settings/system.json"
  local target
  target="${PROJECT_ROOT}/src/pypnm/settings/system.json"

  if [[ ! -f "$backup_path" ]]; then
    echo "⚠️  Backup system settings not found at '$backup_path'; cannot restore."
    return
  fi

  mkdir -p "$(dirname "$target")"
  cp "$backup_path" "$target"
  echo "✅ System settings restored from backup to '$target'."
}

enable_demo_mode() {
  echo "🎛  Enabling demo mode configuration…"
  local demo_src
  demo_src="${PROJECT_ROOT}/demo/settings/system.json"
  local target
  target="${PROJECT_ROOT}/src/pypnm/settings/system.json"

  if [[ ! -f "$demo_src" ]]; then
    echo "⚠️  Demo settings file not found at '$demo_src'; skipping demo mode."
    return
  fi

  if [[ -f "$target" ]]; then
    echo "ℹ️  Overwriting existing system settings at '$target' with demo template."
  else
    echo "ℹ️  Creating system settings at '$target' from demo template."
  fi

  mkdir -p "$(dirname "$target")"
  cp "$demo_src" "$target"
  echo "✅ Demo mode system settings applied (directories now point to demo/)."
}

echo "🔍 Detecting package manager..."
PM="none"; PM_UPDATE=""; PM_INSTALL=""
if command -v apt-get >/dev/null 2>&1; then
  PM="apt-get"; PM_UPDATE="sudo apt-get update"; PM_INSTALL="sudo apt-get install -y"
  echo "ℹ️  Debian/Ubuntu (apt-get)"
elif command -v dnf >/dev/null 2>&1; then
  PM="dnf"; PM_UPDATE="sudo dnf makecache"; PM_INSTALL="sudo dnf install -y"
  echo "ℹ️  Fedora/RHEL (dnf)"
elif command -v yum >/dev/null 2>&1; then
  PM="yum"; PM_UPDATE="sudo yum makecache"; PM_INSTALL="sudo yum install -y"
  echo "ℹ️  RHEL/CentOS (yum)"
elif command -v zypper >/dev/null 2>&1; then
  PM="zypper"; PM_UPDATE="sudo zypper refresh"; PM_INSTALL="sudo zypper install -y"
  echo "ℹ️  SUSE/openSUSE (zypper)"
elif command -v apk >/dev/null 2>&1; then
  PM="apk"; PM_UPDATE=""; PM_INSTALL="sudo apk add --no-cache"
  echo "ℹ️  Alpine (apk)"
elif command -v brew >/dev/null 2>&1; then
  PM="brew"; PM_UPDATE="brew update"; PM_INSTALL="brew install"
  echo "ℹ️  macOS (brew)"
else
  echo "⚠️  Unsupported OS: please manually install 'ssh', 'sshpass', and Python venv support."
fi

if [[ "$PM" != "none" && -n "${PM_UPDATE:-}" ]]; then
  echo "🔄 Updating package cache..."
  $PM_UPDATE || true
fi

echo "✅ Installing OS prerequisites..."
if ! command -v ssh >/dev/null 2>&1; then
  if [[ "$PM" == "none" ]]; then
    echo "⚠️  No package manager; cannot auto-install 'ssh'."
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
  if [[ "$PM" == "none" ]]; then
    echo "⚠️  No package manager; cannot auto-install 'sshpass'."
  else
    echo "🔧 Installing sshpass..."
    $PM_INSTALL sshpass || true
  fi
fi

echo "🧮 Ensuring SciPy/NumPy build prerequisites (where applicable)..."
case "$PM" in
  apt-get)
    $PM_INSTALL build-essential gfortran libopenblas-dev liblapack-dev || true
    ;;
  dnf|yum)
    $PM_INSTALL gcc gcc-c++ make blas-devel lapack-devel || true
    ;;
  zypper)
    $PM_INSTALL gcc gcc-c++ make libopenblas-devel lapack-devel || true
    ;;
  apk)
    $PM_INSTALL build-base gfortran openblas-dev lapack-dev || true
    ;;
  brew)
    # Homebrew wheels usually bundle BLAS/LAPACK; nothing extra required in most cases.
    :
    ;;
  *)
    echo "⚠️  Skipping SciPy/NumPy build prerequisites for unknown or manual PM."
    ;;
esac

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")"
PYTHON_CMD="python${PYTHON_VERSION}"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
  else
    echo "❌ Python 3.x not found in PATH."
    exit 1
  fi
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
pip install -e "$PROJECT_ROOT"[dev,docs]

echo "📦 Installing required tooling: pytest, mkdocs, mkdocs-material, cryptography…"
pip install "pytest>=7" "mkdocs>=1.6" "mkdocs-material>=9.5" "cryptography>=41"

echo "🔎 Verifying MkDocs install…"
mkdocs --version

echo "🔧 Configuring PYTHONPATH…"
"$PROJECT_ROOT/scripts/install_py_path.sh" "$PROJECT_ROOT" || true

echo "🔐 Ensuring PyPNM secret key exists (~/.ssh/pypnm_secrets.key)…"
if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]]; then
  echo "ℹ️  Skipping secret key creation (CI environment)."
  echo "    Create it locally with:"
  echo "      ./scripts/init_secrets_key.sh"
else
  if [[ -x "${PROJECT_ROOT}/scripts/init_secrets_key.sh" ]]; then
    "${PROJECT_ROOT}/scripts/init_secrets_key.sh" --quiet || true
  else
    echo "ℹ️  scripts/init_secrets_key.sh is missing or not executable; skipping."
  fi
fi

echo "🧪 Running unit tests…"
cd "$PROJECT_ROOT"
pytest -v

if [[ "$PRODUCTION_MODE" == "1" ]]; then
  restore_system_settings
elif [[ "$DEMO_MODE" == "1" ]]; then
  backup_system_settings
  enable_demo_mode
else
  backup_system_settings
fi

###############################################################################
# Optional: PNM File Retrieval Setup (CI-Safe)
#
# Behavior:
#   - If --pnm-file-retrieval-setup was passed:
#       • Attempt to run tools/pnm_file_retrieval_setup.py automatically
#         when in an interactive, non-CI environment.
#       • If in CI or non-TTY, print a message and skip.
#
#   - If the flag was NOT passed:
#       • Do NOT prompt interactively.
#       • Just print a short message about the manual helper.
###############################################################################
run_pnm_setup_if_possible() {
  if [[ ! -t 0 || -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]]; then
    echo "ℹ️  Skipping PNM file retrieval setup (non-interactive or CI environment)."
    echo "    You can run it later with:"
    echo "      ./tools/pnm_file_retrieval_setup.py"
    return
  fi

  if [[ -x "./tools/pnm_file_retrieval_setup.py" ]]; then
    echo
    echo "Launching PNM file retrieval setup..."
    ./tools/pnm_file_retrieval_setup.py
  else
    echo "tools/pnm_file_retrieval_setup.py is missing or not executable."
    echo "You can run it manually later once it is available:"
    echo "  ./tools/pnm_file_retrieval_setup.py"
  fi
}

run_pnm_alias_installer_if_available() {
  if [[ -x "${PROJECT_ROOT}/scripts/install_aliases.sh" ]]; then
    echo "🔗 Installing PyPNM shell aliases (e.g., config-menu)…"
    "${PROJECT_ROOT}/scripts/install_aliases.sh" || true
  fi
}

if [[ "$PNM_FILE_RETRIEVAL_SETUP" == "1" ]]; then
  echo
  echo "PNM File Retrieval Configuration (requested via --pnm-file-retrieval-setup)"
  run_pnm_setup_if_possible
else
  echo
  echo "ℹ️  PNM file retrieval setup was not requested."
  echo "    You can configure it later with:"
  echo "      ./tools/pnm_file_retrieval_setup.py"
fi

run_pnm_alias_installer_if_available

echo "✅ Bootstrap complete."
if [[ "$DEMO_MODE" == "1" ]]; then
  echo "👉 Demo mode is enabled: system settings now reference the demo/ directories."
fi
if [[ "$PRODUCTION_MODE" == "1" ]]; then
  echo "👉 Production mode is restored: system settings have been reverted from backup."
fi
echo "👉 Next steps:"
echo "   1) source '$VENV_DIR/bin/activate'"
echo "   2) (optional) ./tools/pnm_file_retrieval_setup.py"
echo "   3) mkdocs serve"
