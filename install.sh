#!/usr/bin/env bash
# install_py_path.sh — Append PYTHONPATH exports to your shell startup file.
# Usage: ./install_py_path.sh [PROJECT_ROOT]
# Defaults to the directory containing this script.

set -euo pipefail

# Resolve project root
if [[ -n "${1-}" ]]; then
  PROJECT_ROOT="$1"
else
  # directory of this script
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# Lines to add
EXPORT_LINE='export PYTHONPATH="${PYTHONPATH}:'"$PROJECT_ROOT"'/src:'"$PROJECT_ROOT"'/startup"'

# Determine shell and rc file
SHELL_NAME="$(basename "${SHELL:-}")"
case "$SHELL_NAME" in
  bash) RC_FILE="$HOME/.bashrc" ;;
  zsh)  RC_FILE="$HOME/.zshrc" ;;
  fish) RC_FILE="$HOME/.config/fish/config.fish" ;;
  *)    RC_FILE="$HOME/.profile" ;;
esac

echo "Installing PYTHONPATH exports into $RC_FILE …"

# Ensure the rc directory exists (for fish)
mkdir -p "$(dirname "$RC_FILE")"

# Check and append if missing
if ! grep -F "${PROJECT_ROOT}/src" "$RC_FILE" >/dev/null 2>&1; then
  {
    echo ""
    echo "# >>> Added by install_py_path.sh >>>"
    echo "$EXPORT_LINE"
    echo "# <<< End install_py_path.sh <<<"
  } >> "$RC_FILE"
  echo "✅ Added PYTHONPATH export to $RC_FILE"
else
  echo "⚠️  PYTHONPATH line already present in $RC_FILE; nothing to do."
fi

echo
echo "Next steps:"
echo "  • Restart your terminal, or run:"
echo "      source $RC_FILE"
echo "  • Verify with:"
echo "      echo \$PYTHONPATH"
