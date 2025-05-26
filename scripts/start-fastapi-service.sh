#!/usr/bin/env bash

# --------------------------------------------------------------------------------------
# 🛡️  FastAPI Webservice Launcher with HTTPS Support
#
# This script launches the FastAPI webservice using Uvicorn.
# It supports both HTTP and HTTPS based on command-line arguments.
#
# ✅ Prerequisites:
#   - Python installed with `uvicorn` and `fastapi`
#   - Optional: SSL certificate and key files (PEM format) for HTTPS
#
# 🔐 To create a self-signed SSL certificate for development:
#   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
#     -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"
#
# 📌 Default values:
#   --host        127.0.0.1
#   --port        8000
#   --ssl         false
#   --cert        ./certs/cert.pem
#   --key         ./certs/key.pem
#
# 🚀 Usage Examples:
#   ./start-fastapi-service.sh
#   ./start-fastapi-service.sh --host 0.0.0.0 --port 443 --ssl true
# --------------------------------------------------------------------------------------

set -e

# Default values
HOST="127.0.0.1"
PORT="8000"
USE_SSL="false"
CERT_FILE="./certs/cert.pem"
KEY_FILE="./certs/key.pem"

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --host) HOST="$2"; shift ;;
    --port) PORT="$2"; shift ;;
    --ssl) USE_SSL="$2"; shift ;;
    --cert) CERT_FILE="$2"; shift ;;
    --key) KEY_FILE="$2"; shift ;;
    *) echo "❌ Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# Extend PYTHONPATH for module resolution
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/startup"

# Launch FastAPI
if [[ "$USE_SSL" == "true" ]]; then
  echo "🔒 Launching FastAPI with HTTPS on https://${HOST}:${PORT}"
  uvicorn src.api.main:app \
    --reload \
    --timeout-keep-alive 120 \
    --host "$HOST" \
    --port "$PORT" \
    --ssl-certfile "$CERT_FILE" \
    --ssl-keyfile "$KEY_FILE"
else
  echo "🌐 Launching FastAPI with HTTP on http://${HOST}:${PORT}"
  uvicorn src.api.main:app \
    --reload \
    --timeout-keep-alive 120 \
    --host "$HOST" \
    --port "$PORT"
fi
