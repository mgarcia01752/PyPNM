#!/usr/bin/env bash
set -euo pipefail

# Optional first argument to override the venv directory (default: .env)
VENV_DIR="${1:-.env}"
PYPROJECT="pyproject.toml"

echo "🛠  Starting PyPNM setup & test…"
echo

# 1) Create a fresh venv
echo "🔧 Creating virtual environment in '$VENV_DIR'…"
python3 -m venv "$VENV_DIR"

# 2) Activate it
echo "🚀 Activating '$VENV_DIR'…"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# 3) Upgrade pip
echo "⬆️  Upgrading pip…"
pip install --upgrade pip

# 4) Install helper tools
echo "📦 Installing pip-chill, toml, and build…"
pip install pip-chill toml build

# 5) Update pyproject.toml dependencies
if [[ -f "update_deps.py" && -f "$PYPROJECT" ]]; then
  echo "✏️  Updating '$PYPROJECT' dependencies via update_deps.py…"
  python update_deps.py --toml "$PYPROJECT"
else
  echo "⚠️  Skipping dependency update (missing update_deps.py or $PYPROJECT)."
fi

# 6) Build the wheel & sdist
echo "🔨 Building distribution…"
python -m build

# 7) Install the freshly built wheel
echo "📥 Installing the new wheel…"
pip install dist/*.whl

# 8) Smoke-test import
echo "✅ Testing import of pypnm…"
python - <<'PYCODE'
import pypnm
print(f"Imported pypnm version: {pypnm.__version__}")
PYCODE

echo
echo "🎉 Done! Your clean install of PyPNM is working."
echo "   To re-enter the venv later:  source $VENV_DIR/bin/activate"

