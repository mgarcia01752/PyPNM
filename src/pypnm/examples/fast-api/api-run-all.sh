#!/usr/bin/env bash

# --------------------------------------------------------------------------------------
# 📦 Batch Python Script Executor with CLI Argument Support
#
# This script searches for all `.py` files in the current directory and subdirectories,
# and runs them with configurable CLI arguments for MAC address and CM IP.
#
# 🛠️ Default Values:
#   --mac    0aa.bbcc.ddee
#   --inet   172.20.58.24
#   --tftp   172.20.10.153
#   --mibs   mibs/
#
# 🔄 Usage:
#   ./run_all.sh
#   ./run_all.sh --mac 00aa.bbcc.ddee --inet 192.168.100.1 --tftp 10.0.0.1 --mibs ./custom-mibs
# --------------------------------------------------------------------------------------

set -e

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --mac) CM_MAC="$2"; shift ;;
    --inet) CM_IP="$2"; shift ;;
    --tftp) TFTP="$2"; shift ;;
    --mibs) MIB_DIR="$2"; shift ;;
    *) echo "❌ Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}/src:${PWD}/startup"

# Common CLI argument string
CLI="--mac ${CM_MAC} --inet ${CM_IP} --tftp ${TFTP} --mibs ${MIB_DIR}"

# Execute all Python scripts
for file in $(find . -type f -name "*.py"); do
    echo "🚀 Running $file with CLI args: ${CLI}"
    python3 "$file" ${CLI}
done
