#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=${PWD}

# ──────────────────────────────────────────────────────────────────────────────
# 1. Detect Ubuntu version (fallback to lsb_release if /etc/os-release missing)
# ──────────────────────────────────────────────────────────────────────────────
if [ -r /etc/os-release ]; then
  . /etc/os-release
  DISTRO="$ID"
  VERSION="$VERSION_ID"
elif command -v lsb_release &>/dev/null; then
  DISTRO="$(lsb_release -si | tr '[:upper:]' '[:lower:]')"
  VERSION="$(lsb_release -sr)"
else
  echo "Cannot detect OS version. Exiting."
  exit 1
fi

# Only support Ubuntu for this check
if [ "$DISTRO" != "ubuntu" ]; then
  echo "Warning: this installer is optimized for Ubuntu. Detected '$DISTRO $VERSION'."
fi

# Choose Python package names based on Ubuntu version
case "$VERSION" in
  22.*)
    PYTHON_PKG=python3.10
    VENV_PKG=python3.10-venv
    ;;
  24.*)
    PYTHON_PKG=python3.12
    VENV_PKG=python3.12-venv
    ;;
  *)
    PYTHON_PKG=python3
    VENV_PKG=python3-venv
    echo "Detected Ubuntu $VERSION — installing default $PYTHON_PKG."
    ;;
esac

echo
echo "🏗️  Installing on Ubuntu $VERSION: $PYTHON_PKG (+ venv) and pip…"
sudo apt update
sudo apt install -y \
     curl \
     wget \
     "$PYTHON_PKG" \
     "$VENV_PKG" \
     python3-pip

echo
echo "✅ System packages installed."

# ──────────────────────────────────────────────────────────────────────────────
# 2. Download DOCSIS MIBs ending in .txt into a 'mibs' directory
# ──────────────────────────────────────────────────────────────────────────────
echo
echo "Creating 'mibs' directory (if not existing)…"
mkdir -p mibs

# Ensure wget is available
if ! command -v wget &>/dev/null; then
  echo "Error: wget is required but not installed. Aborting."
  exit 1
fi

echo "Downloading DOCSIS MIB files with a .txt extension into ./mibs…"
wget -r -np -nH --cut-dirs=2 -A "*.txt" -R "index.html*" \
     -P mibs "https://mibs.cablelabs.com/MIBs/DOCSIS/"

# Check how many .txt files actually arrived
count=$(ls mibs/*.txt 2>/dev/null | wc -l || echo 0)
if [ "$count" -eq 0 ]; then
  echo "⚠️  Warning: No .txt MIB files found in mibs/. Please verify the remote directory."
else
  echo "✅ Downloaded $count .txt MIB file(s)."
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3. Create index.md listing all .txt files
# ──────────────────────────────────────────────────────────────────────────────
echo
if ! cd mibs; then
  echo "Error: Could not enter mibs directory. Exiting."
  exit 1
fi

cat << 'EOF' > index.md
# DOCSIS MIB Files Index

Below is a list of all downloaded `.txt` MIB files currently in this directory:

EOF

for file in *.txt; do
  [ -e "$file" ] || continue
  echo "- [${file}](./${file})" >> index.md
done

# Return to the root directory
cd "${ROOT_DIR}"
echo "✅ Generated 'mibs/index.md' with a list of all .txt files."

# ──────────────────────────────────────────────────────────────────────────────
# 4. Create & activate Python virtual environment, then install PyPNM
# ──────────────────────────────────────────────────────────────────────────────
echo
echo "Setting up Python virtual environment…"
"$PYTHON_PKG" -m venv .env

# Activate the venv in this script context
source .env/bin/activate

echo "Upgrading pip, setuptools, and wheel in venv…"
pip install --upgrade pip setuptools wheel

echo "Installing PyPNM in editable mode…"
pip install -e .

# Quick import check
if python -c "import pypnm" &> /dev/null; then
  echo "✅ PyPNM imported successfully."
else
  echo "❌ Error: PyPNM could not be imported. Check your packaging."
  exit 1
fi

echo
echo "✅ PyPNM installed! To exit the virtual environment, run 'deactivate'."
echo
echo "🎉 Installation complete! 🎉"
