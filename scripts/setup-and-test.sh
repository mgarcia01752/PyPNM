#!/usr/bin/env bash
set -euo pipefail

# setup-and-test.sh — Verify your PyPNM install quickly.

VENV_DIR="${1:-.env}"

echo "🛠  Verifying PyPNM in venv '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "⬆️  Ensuring pip, setuptools, wheel are up-to-date…"
pip install --upgrade pip setuptools wheel

echo "📥 Installing PyPNM package (editable)…"
pip install -e .[dev]

echo "✅ Smoke-test import and version:"
python - <<'PYCODE'
import pypnm
print(f"✅ Imported PyPNM v{pypnm.__version__}")
PYCODE

echo "🎉 Setup & test successful!"
