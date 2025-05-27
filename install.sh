#!/usr/bin/env bash
set -euo pipefail

echo "🛠  Running setup-and-test…"
./scripts/setup-and-test.sh

echo
echo "🔧 Configuring PYTHONPATH…"
./scripts/install_py_path.sh "$(pwd)"

echo
echo "🎉 All done! To get started:"
echo "  source .env/bin/activate"
echo "  source ~/.bashrc  # or ~/.zshrc"
