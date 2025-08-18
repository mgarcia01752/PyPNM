#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Cleans logs, Python caches, build artifacts, PNM data, and output files.

set -euo pipefail
IFS=$'\n\t'

# -----------------------------------------------------------------------------
# Usage info
# -----------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] [ROOT_DIR]

Options:
  --all         Clean logs, Python cache, build artifacts, PNM data, output
  --logs        Clean only logs/
  --python      Clean only Python caches (__pycache__, *.pyc, .pytest_cache)
  --build       Clean build/, dist/, *.egg-info
  --pnm         Clean data/pnm/ and data/db/
  --output      Clean output/
  -h, --help    Show this help and exit

ROOT_DIR defaults to the current directory if not provided.
EOF
  exit 1
}

# -----------------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------------
ROOT_DIR="."
declare -a ACTIONS=()

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
while (( $# )); do
  case "$1" in
    --all|--logs|--python|--build|--pnm|--output)
      ACTIONS+=("$1")
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      # assume anything else is the root directory
      ROOT_DIR="$1"
      shift
      ;;
  esac
done

if [[ ${#ACTIONS[@]} -eq 0 ]]; then
  usage
fi

# Canonicalize ROOT_DIR
ROOT_DIR=$(realpath "$ROOT_DIR")
echo "🔍 Cleaning in root directory: $ROOT_DIR"

# -----------------------------------------------------------------------------
# Helper: safe remove (handles multiple args)
# -----------------------------------------------------------------------------
safe_rm() {
  local path
  for path in "$@"; do
    if [[ -e $path ]]; then
      rm -rf "$path"
      echo "🗑️  Removed: $path"
    fi
  done
}

# -----------------------------------------------------------------------------
# Individual “clean” functions
# -----------------------------------------------------------------------------
clean_logs() {
  echo "🧹 Cleaning logs..."
  safe_rm "$ROOT_DIR/logs/"*
}

clean_python() {
  echo "🐍 Cleaning Python caches..."
  find "$ROOT_DIR" -type d -name '__pycache__' -print -exec rm -rf {} +
  find "$ROOT_DIR" -type f -name '*.pyc'     -print -delete
  safe_rm "$ROOT_DIR/.pytest_cache"
}

clean_build() {
  echo "🏗️  Cleaning build artifacts..."
  safe_rm "$ROOT_DIR/build"
  safe_rm "$ROOT_DIR/dist"
  safe_rm "$ROOT_DIR"/*.egg-info
}

clean_pnm() {
  echo "📦 Cleaning PNM data..."
  safe_rm "$ROOT_DIR/.data/pnm/"*
  safe_rm "$ROOT_DIR/.data/db/"*
}

clean_excel() {
  echo "📦 Cleaning excel data..."
  safe_rm "$ROOT_DIR/.data/xlsx/"*
  safe_rm "$ROOT_DIR/.data/csv/"*
}

clean_png() {
  echo "📦 Cleaning matplot.png ..."
  safe_rm "$ROOT_DIR/.data/png/"*
}


safe_rm "$ROOT_DIR/.data/db/"*

clean_output() {
  echo "📤 Cleaning output files..."
  safe_rm "$ROOT_DIR/output/"*
}

# -----------------------------------------------------------------------------
# Dispatch actions
# -----------------------------------------------------------------------------
for action in "${ACTIONS[@]}"; do
  case "$action" in

    --all)
      echo "🚀 Performing full cleanup..."
      clean_logs
      clean_python
      clean_build
      clean_pnm
      clean_excel
      clean_output
      clean_png
      ;;

    --logs)
      clean_logs
      ;;

    --python)
      clean_python
      ;;

    --build)
      clean_build
      ;;

    --pnm)
      clean_pnm
      ;;

    --excel)
      clean_excel
      ;;

    --output)
      clean_output
      ;;
  esac
done

echo "✅ Cleanup complete."
