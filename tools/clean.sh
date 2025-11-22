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
  --logs        Truncate logs/pypnm.log (preserve file and permissions)
  --python      Clean only Python caches (__pycache__, *.pyc, .pytest_cache)
  --build       Clean build/, dist/, *.egg-info
  --pnm         Clean data/pnm/ and data/db/
  --archive     Clean .data/archive/
  --excel       Clean .data/xlsx/ and .data/csv/
  --plot-data   Clean .data/png/, .data/csv/ and .data/archive/
  --msg-rsp     Clean .data/msg_rsp (Message Response)
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
    --all|--logs|--python|--build|--pnm|--output|--plot-data|--msg-rsp|--archive|--excel)
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
  echo "🧹 Cleaning logs (truncate, preserve files)..."

  local log_file="$ROOT_DIR/logs/pypnm.log"

  if [[ -f "$log_file" ]]; then
    : > "$log_file"   # truncate to zero bytes, keep permissions and inode
    echo "🧾 Truncated: $log_file"
  else
    echo "ℹ️  No log file found at: $log_file"
  fi
}

clean_archives() {
  echo "🧹 Cleaning archives..."
  safe_rm "$ROOT_DIR/.data/archive/"*
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
  echo "📊 Cleaning Excel/CSV data..."
  safe_rm "$ROOT_DIR/.data/xlsx/"*
  safe_rm "$ROOT_DIR/.data/csv/"*
}

clean_png() {
  echo "🖼️  Cleaning PNG data..."
  safe_rm "$ROOT_DIR/.data/png/"*
}

clean_output() {
  echo "📤 Cleaning output files..."
  safe_rm "$ROOT_DIR/output/"*
}

clean_plot_data() {
  echo "📈 Cleaning plot data and archive files..."
  safe_rm "$ROOT_DIR/.data/png/"*
  safe_rm "$ROOT_DIR/.data/csv/"*
  safe_rm "$ROOT_DIR/.data/archive/"*
}

clean_msg_rsp() {
  echo "📨 Cleaning message-response data..."
  safe_rm "$ROOT_DIR/.data/msg_rsp/"*
}

# -----------------------------------------------------------------------------
# Dispatch actions
# -----------------------------------------------------------------------------
for action in "${ACTIONS[@]}"; do
  case "$action" in

    --all)
      echo "🚀 Performing full cleanup..."
      clean_logs
      clean_archives
      clean_python
      clean_build
      clean_pnm
      clean_excel
      clean_output
      clean_png
      clean_plot_data
      clean_msg_rsp
      ;;

    --archive)
      clean_archives
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

    --plot-data)
      clean_plot_data
      ;;

    --msg-rsp)
      clean_msg_rsp
      ;;

    --output)
      clean_output
      ;;
  esac
done

echo "✅ Cleanup complete."
