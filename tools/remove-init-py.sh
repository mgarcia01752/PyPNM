#!/usr/bin/env bash

# Usage:
#   ./remove_init.sh [optional_start_path]
# Default is current directory if no path is provided

START_PATH=${1:-.}

echo "Searching for __init__.py files under: $START_PATH"

find "$START_PATH" -type f -name '__init__.py' -print -exec rm -v {} \;

echo "Done."
