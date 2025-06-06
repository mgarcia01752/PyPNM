#!/usr/bin/env bash
# install_py_path.sh — Append PYTHONPATH exports to your shell startup file.
# Usage: ./install_py_path.sh [PROJECT_ROOT]
# Defaults to the directory containing this script.

set -euo pipefail

# 1) Determine project root
if [[ -n "${1-}" ]]; then
  PROJECT_ROOT="$1"
else
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

SRC_PATH="$PROJECT_ROOT/src"

# 2) Prepare snippets for each shell
BASH_EXPORT="export PYTHONPATH=\"\$PYTHONPATH:$SRC_PATH\""
ZSH_EXPORT="$BASH_EXPORT"
FISH_EXPORT="set -gx PYTHONPATH \$PYTHONPATH $SRC_PATH"

# 3) Figure out which RC file to touch
RC_FILE=""
# If fish is the current shell
if [[ "${SHELL##*/}" == "fish" ]]; then
  RC_FILE="$HOME/.config/fish/config.fish"
  EXPORT_LINE="$FISH_EXPORT"
# If zsh
elif [[ -f "$HOME/.zshrc" ]]; then
  RC_FILE="$HOME/.zshrc"
  EXPORT_LINE="$ZSH_EXPORT"
# If bash on Linux
elif [[ -f "$HOME/.bashrc" ]]; then
  RC_FILE="$HOME/.bashrc"
  EXPORT_LINE="$BASH_EXPORT"
# If bash on macOS (or bash_profile exists)
elif [[ -f "$HOME/.bash_profile" ]]; then
  RC_FILE="$HOME/.bash_profile"
  EXPORT_LINE="$BASH_EXPORT"
else
  echo "⚠️  No known shell rc file found (~/.bashrc, ~/.bash_profile, ~/.zshrc, or Fish config)."
  echo "Please add this line to your shell startup manually:"
  echo
  echo "    $BASH_EXPORT"
  exit 1
fi

echo "👉  Appending PYTHONPATH configuration to $RC_FILE"

# 4) Append idempotently
if ! grep -F "$SRC_PATH" "$RC_FILE" &>/dev/null; then
  {
    echo ""
    echo "# >>> Added by install_py_path.sh >>>"
    echo "$EXPORT_LINE"
    echo "# <<< End install_py_path.sh <<<"
  } >> "$RC_FILE"
  echo "✅  Added PYTHONPATH to $RC_FILE"
else
  echo "⚠️  $SRC_PATH already in $RC_FILE; nothing changed."
fi

echo
echo "Next steps:"
echo "  • Reload your shell (e.g. run:  source $RC_FILE)"
echo "  • Verify with:             echo \$PYTHONPATH"
