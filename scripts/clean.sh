#!/usr/bin/env bash

# Usage info
usage() {
    echo "Usage: $0 [ACTION]... [ROOT_DIR]"
    echo ""
    echo "Actions:"
    echo "  --all         Clean logs, __pycache__, .pytest_cache, *.pyc, builds"
    echo "  --logs        Only clean logs directory"
    echo "  --python      Only clean Python cache files"
    echo "  --build       Clean dist/, build/, *.egg-info"
    echo "  --pnm         Clean data/tftp and data/db directories"
    echo "  --output      Clean output directory (PNM process files)"
    echo "  help          Show this help message"
    echo ""
    echo "If ROOT_DIR is not specified, it defaults to current directory."
    exit 1
}

# Default root directory
ROOT_DIR="."
ACTIONS=()

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --all|--logs|--python|--build|--pnm|--output)
            ACTIONS+=("$arg")
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            ROOT_DIR="$arg"
            ;;
    esac
done

if [ ${#ACTIONS[@]} -eq 0 ]; then
    usage
fi

echo "Root directory: $ROOT_DIR"

# Execute requested actions
for ACTION in "${ACTIONS[@]}"; do
    case "$ACTION" in
        --all)
            echo "Cleaning all logs, cache, build, PNM, and output files..."
            rm -rf "$ROOT_DIR"/logs/* || true
            rm -rf "$ROOT_DIR"/.pytest_cache
            find "$ROOT_DIR" -type d -name '__pycache__' -exec rm -rf {} + -print
            find "$ROOT_DIR" -type f -name '*.pyc' -delete -print
            rm -rf "$ROOT_DIR"/build "$ROOT_DIR"/dist "$ROOT_DIR"/*.egg-info
            rm -rf "$ROOT_DIR"/data/pnm/* "$ROOT_DIR"/data/db/*
            rm -rf "$ROOT_DIR"/output/*
            ;;
        --logs)
            echo "Cleaning logs..."
            rm -rf "$ROOT_DIR"/logs/* || true
            ;;
        --python)
            echo "Cleaning Python cache files and folders..."
            find "$ROOT_DIR" -type d -name '__pycache__' -exec rm -rf {} + -print
            find "$ROOT_DIR" -type f -name '*.pyc' -delete -print
            rm -rf "$ROOT_DIR"/.pytest_cache
            ;;
        --build)
            echo "Cleaning build artifacts..."
            rm -rf "$ROOT_DIR"/build "$ROOT_DIR"/dist "$ROOT_DIR"/*.egg-info
            ;;
        --pnm)
            echo "Cleaning PNM files..."
            rm -rf "$ROOT_DIR"/data/pnm/* "$ROOT_DIR"/data/db/*
            ;;
        --output)
            echo "Cleaning output PNM process files..."
            rm -rf "$ROOT_DIR"/output/*
            ;;
    esac
done

echo "Cleanup complete."
exit 0
