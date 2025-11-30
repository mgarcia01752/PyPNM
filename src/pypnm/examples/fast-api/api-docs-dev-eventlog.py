#!/usr/bin/env python3

from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
import argparse
import json
import sys

try:
    import requests

except ImportError:
    print("❌ The 'requests' library is not installed. Please install it before running this script.")
    sys.exit(1)

def test_endpoint(mac: str, ip: str, url: str):
    """
    Sends a POST request to the /docs/dev/eventLog endpoint using Python requests.
    """
    payload = {
        "mac_address": mac,
        "ip_address": ip
    }

    print(f"\n📡 Sending POST to {url} with payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n✅ Response:")
        print(json.dumps(response.json(), indent=2))
    except requests.RequestException as e:
        print("\n❌ Request failed:")
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Test the /docs/dev/eventLog endpoint.")
    parser.add_argument("--mac", "-m", required=True, help="MAC address of the cable modem")
    parser.add_argument("--inet", "-i", required=True, help="IP address of the cable modem")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/docs/dev/eventLog",
        help="Target URL for the endpoint (default: http://localhost:8000/docs/dev/eventLog)"
    )

    args = parser.parse_args()
    test_endpoint(args.mac, args.inet, args.url)
