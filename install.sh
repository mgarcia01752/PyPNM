#!/usr/bin/env bash
set -euo pipefail

# Detect Ubuntu version
if [ -r /etc/os-release ]; then
  . /etc/os-release
  DISTRO="$ID"
  VERSION="$VERSION_ID"
else
  echo "Cannot detect OS version. Exiting."
  exit 1
fi

# Only support Ubuntu for this check
if [ "$DISTRO" != "ubuntu" ]; then
  echo "Warning: this installer is optimized for Ubuntu."
fi

# Choose Python package names based on Ubuntu version
case "$VERSION" in
  "22.04")
    PYTHON_PKG=python3.10
    VENV_PKG=python3.10-venv
    ;;
  "24.04")
    PYTHON_PKG=python3.12
    VENV_PKG=python3.12-venv
    ;;
  *)
    # fallback to default distro python3
    PYTHON_PKG=python3
    VENV_PKG=python3-venv
    echo "Detected Ubuntu $VERSION — installing default $PYTHON_PKG."
    ;;
esac

echo "Installing on Ubuntu $VERSION: $PYTHON_PKG (+ venv) and pip…"
sudo apt update
sudo apt install -y \
     curl \
     wget \
     "$PYTHON_PKG" \
     "$VENV_PKG" \
     python3-pip

# -------------------------------
# Download DOCSIS MIBs ending in .txt into a 'mibs' directory
# -------------------------------
echo
echo "Creating 'mibs' directory (if not existing)…"
mkdir -p mibs

echo "Downloading DOCSIS MIB files with a .txt extension into ./mibs…"
wget -r -np -nH --cut-dirs=2 -A "*.txt" -R "index.html*" \
     -P mibs "https://mibs.cablelabs.com/MIBs/DOCSIS/"

echo
echo "✅ DOCSIS .txt MIB files downloaded into the './mibs' directory."

echo
echo "✅ System packages installed."
echo "Setting up Python virtual environment…"
python3 -m venv .venv

# Activate the venv in this script context
# (for user interactive shells they'll need to `source .venv/bin/activate`)
source .venv/bin/activate

echo "Installing PyPNM in editable mode…"
pip install -e .

echo
echo "✅ PyPNM installed!"
echo "To exit the virtual environment, run 'deactivate'."


