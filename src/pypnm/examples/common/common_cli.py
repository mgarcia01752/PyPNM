#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import json
import sys
from typing import TypedDict

try:
    import requests
except ImportError:
    print("The 'requests' library is not installed. Please install it before running these examples.")
    sys.exit(2)


EXIT_SUCCESS: int                      = 0
EXIT_IMPORT_ERROR: int                 = 2
EXIT_REQUEST_ERROR: int                = 3

DEFAULT_SNMP_COMMUNITY: str            = "private"
DEFAULT_BASE_URL: str                  = "http://127.0.0.1:8000"
DEFAULT_SAMPLE_TIME_ELAPSED_SEC: int   = 5
DEFAULT_HTTP_TIMEOUT_SEC: float        = 120.0


class SnmpV2CPayload(TypedDict):
    community: str


class SnmpPayload(TypedDict):
    snmpV2C: SnmpV2CPayload


class CableModemPayload(TypedDict):
    mac_address: str
    ip_address: str
    snmp: SnmpPayload


class CableModemRequestPayload(TypedDict):
    cable_modem: CableModemPayload


class CaptureParametersPayload(TypedDict):
    sample_time_elapsed: int


class CableModemCaptureRequestPayload(TypedDict):
    cable_modem: CableModemPayload
    capture_parameters: CaptureParametersPayload


def build_cable_modem_payload(mac: str, ip: str, community: str) -> CableModemRequestPayload:
    """
    Build The Common cable_modem Request Payload.

    This helper constructs the JSON structure shared by multiple example
    scripts. The returned payload contains the cable_modem object with the
    MAC address, IP address, and SNMP v2c community configuration.
    """
    return {
        "cable_modem": {
            "mac_address": mac,
            "ip_address": ip,
            "snmp": {
                "snmpV2C": {
                    "community": community,
                },
            },
        },
    }


def build_cable_modem_capture_payload(
    mac: str,
    ip: str,
    community: str,
    sample_time_elapsed: int,
) -> CableModemCaptureRequestPayload:
    """
    Build A cable_modem Request Payload With Capture Parameters.

    This helper extends the common cable_modem payload with a capture_parameters
    section used by measurement endpoints such as downstream SC-QAM codeword
    error rate. The sample_time_elapsed value defines the capture duration in
    seconds.
    """
    base_payload: CableModemRequestPayload = build_cable_modem_payload(mac, ip, community)
    return {
        "cable_modem": base_payload["cable_modem"],
        "capture_parameters": {
            "sample_time_elapsed": sample_time_elapsed,
        },
    }


def send_cable_modem_request(endpoint_path: str, base_url: str, mac: str, ip: str, community: str) -> int:
    """
    Send A POST Request To A PyPNM Endpoint Using The cable_modem Payload.

    The endpoint_path argument supplies the REST path, such as
    "/docs/dev/eventLog". The base_url argument defines the server root, for
    example "http://127.0.0.1:8000". A POST request is issued with the
    cable_modem payload, and the JSON response is printed when available. The
    return value is an exit status where zero indicates success and a non-zero
    value indicates a transport or HTTP error.
    """
    url: str = _join_url(base_url, endpoint_path)
    payload: CableModemRequestPayload = build_cable_modem_payload(mac, ip, community)

    print()
    print(f"Sending POST to {url} with payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload, timeout=DEFAULT_HTTP_TIMEOUT_SEC)
        response.raise_for_status()
    except requests.RequestException as exc:
        print()
        print("Request failed:")
        print(str(exc))
        return EXIT_REQUEST_ERROR

    print()
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)

    return EXIT_SUCCESS


def send_cable_modem_capture_request(
    endpoint_path: str,
    base_url: str,
    mac: str,
    ip: str,
    community: str,
    sample_time_elapsed: int,
) -> int:
    """
    Send A POST Request With cable_modem And capture_parameters Payload.

    This helper is intended for measurement endpoints that require both the
    cable_modem configuration and capture_parameters, such as downstream
    SC-QAM codeword error rate. The sample_time_elapsed argument specifies the
    capture duration in seconds. A POST request is issued and the JSON
    response is printed when available. The return value is an exit status
    where zero indicates success and a non-zero value indicates a transport
    or HTTP error.
    """
    url: str = _join_url(base_url, endpoint_path)
    payload: CableModemCaptureRequestPayload = build_cable_modem_capture_payload(
        mac=mac,
        ip=ip,
        community=community,
        sample_time_elapsed=sample_time_elapsed,
    )

    print()
    print(f"Sending POST to {url} with payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload, timeout=DEFAULT_HTTP_TIMEOUT_SEC)
        response.raise_for_status()
    except requests.RequestException as exc:
        print()
        print("Request failed:")
        print(str(exc))
        return EXIT_REQUEST_ERROR

    print()
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)

    return EXIT_SUCCESS


def _join_url(base_url: str, endpoint_path: str) -> str:
    """
    Join Base URL And Endpoint Path Into A Single URL String.
    """
    base: str = base_url.rstrip("/")
    path: str = endpoint_path.lstrip("/")
    return f"{base}/{path}"
