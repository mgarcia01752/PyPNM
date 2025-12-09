#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Scan the repository for potential secrets using gitleaks (if available)
# and basic heuristic checks as a fallback.

set -euo pipefail
IFS=$'\n\t'

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Scan the current Git repository for potential secrets.

Options:
  --all-history    Scan full Git history (gitleaks only). Default: working tree.
  --path DIR       Repository root (default: project root inferred from this script).
  -h, --help       Show this help message and exit.

Exit codes:
  0  No issues detected.
  1  Errors running the scanner.
  2  Potential secrets detected.
EOF
}

SCAN_ALL_HISTORY=0
CUSTOM_PATH=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --all-history)
      SCAN_ALL_HISTORY=1
      shift
      ;;
    --path)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --path requires a directory." >&2
        exit 1
      fi
      CUSTOM_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT_DEFAULT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="${CUSTOM_PATH:-${PROJECT_ROOT_DEFAULT}}"

if [ ! -d "${PROJECT_ROOT}/.git" ]; then
  echo "ERROR: ${PROJECT_ROOT} does not look like a Git repository (.git missing)." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

echo "Project root      : ${PROJECT_ROOT}"
echo "Scan full history : ${SCAN_ALL_HISTORY}"

has_gitleaks=0
if command -v gitleaks >/dev/null 2>&1; then
  has_gitleaks=1
fi

if [ "${has_gitleaks}" -eq 1 ]; then
  echo "Using gitleaks for secret scanning..."

  cmd=(gitleaks detect --source "${PROJECT_ROOT}" --no-banner --redact)

  if [ "${SCAN_ALL_HISTORY}" -eq 1 ]; then
    cmd+=(--log-opts=--all)
  fi

  echo "Running: ${cmd[*]}"
  if "${cmd[@]}"; then
    echo "gitleaks reported no secrets."
    exit 0
  else
    status=$?
    if [ "${status}" -eq 1 ]; then
      echo "gitleaks detected potential secrets."
      exit 2
    fi
    echo "ERROR: gitleaks exited with status ${status}."
    exit 1
  fi
fi

echo "WARNING: gitleaks not found; falling back to heuristic scan."
echo "Install gitleaks for stronger checks: https://github.com/gitleaks/gitleaks"

PATTERNS=(
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "BEGIN RSA PRIVATE KEY"
  "BEGIN OPENSSH PRIVATE KEY"
  "BEGIN PRIVATE KEY"
  "ssh-rsa "
  "xoxb-"
  "xoxp-"
  "ghp_"
  "github_pat_"
  "pypi-"
  "access_token"
  "secret_key"
  "PRIVATE KEY"
)

FOUND=0

for pattern in "${PATTERNS[@]}"; do
  if git grep -n --ignore-case --fixed-strings -- "${pattern}" >/dev/null 2>&1; then
    if [ "${FOUND}" -eq 0 ]; then
      echo "Potential secrets found by heuristic scan:"
    fi
    FOUND=2
    git grep -n --ignore-case --fixed-strings -- "${pattern}" || true
  fi
done

if [ "${FOUND}" -eq 0 ]; then
  echo "Heuristic scan did not find obvious secrets."
  exit 0
fi

exit "${FOUND}"
