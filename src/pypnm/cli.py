
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import argparse
import os
import uvicorn

def main():
    parser = argparse.ArgumentParser(
        description="Launch the PyPNM FastAPI service with optional HTTPS support.")

    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind (default: 8000)")
    parser.add_argument("--ssl", action="store_true", help="Enable HTTPS (requires cert and key)")
    parser.add_argument("--cert", default="./certs/cert.pem", help="Path to SSL certificate")
    parser.add_argument("--key", default="./certs/key.pem", help="Path to SSL private key")

    args = parser.parse_args()

    if args.ssl:
        print(f"🔒 Launching FastAPI with HTTPS on https://{args.host}:{args.port}")
    else:
        print(f"🌐 Launching FastAPI with HTTP on http://{args.host}:{args.port}")

    # Optional: extend PYTHONPATH dynamically if needed
    os.environ["PYTHONPATH"] = os.getcwd() + "/src:" + os.environ.get("PYTHONPATH", "")

    # Start Uvicorn with dynamic settings
    uvicorn_args = {
        "app": "pypnm.api.main:app",
        "host": args.host,
        "port": args.port,
        "reload": True,
        "timeout_keep_alive": 120,
    }

    if args.ssl:
        uvicorn_args.update({
            "ssl_certfile": args.cert,
            "ssl_keyfile": args.key,
        })

    uvicorn.run(**uvicorn_args)
