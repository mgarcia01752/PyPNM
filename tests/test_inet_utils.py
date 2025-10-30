# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import ipaddress
import pytest

from pypnm.lib.inet_utils import InetUtils


def test_ipv4_to_hex_basic() -> None:
    assert InetUtils.ipv4_to_hex("192.168.0.1") == "0xC0 0xA8 0x00 0x01"
    assert InetUtils.ipv4_to_hex("10.0.0.255") == "0x0A 0x00 0x00 0xFF"


def test_inet_to_binary_ipv4_ipv6_and_invalid() -> None:
    b4 = InetUtils.inet_to_binary("127.0.0.1")
    assert isinstance(b4, (bytes, bytearray)) and len(b4) == 4
    assert b4 == ipaddress.IPv4Address("127.0.0.1").packed

    b6 = InetUtils.inet_to_binary("2001:db8::1")
    assert isinstance(b6, (bytes, bytearray)) and len(b6) == 16
    assert b6 == ipaddress.IPv6Address("2001:db8::1").packed

    assert InetUtils.inet_to_binary("not-an-ip") is None


def test_binary_to_inet_roundtrip_ipv4_ipv6() -> None:
    ipv4 = "8.8.4.4"
    b4 = ipaddress.IPv4Address(ipv4).packed
    assert InetUtils.binary_to_inet(b4) == ipv4

    ipv6 = "2001:4860:4860::8888"
    b6 = ipaddress.IPv6Address(ipv6).packed
    assert InetUtils.binary_to_inet(b6) == ipv6

    # invalid length -> None
    assert InetUtils.binary_to_inet(b"\x01\x02\x03") is None


def test_are_inets_same_version() -> None:
    assert InetUtils.are_inets_same_version("1.2.3.4", "8.8.8.8") is True
    assert InetUtils.are_inets_same_version("1.2.3.4", "2001:db8::1") is False
    # any invalid → False
    assert InetUtils.are_inets_same_version("invalid", "8.8.8.8") is False
    assert InetUtils.are_inets_same_version("2001:db8::1", "also-bad") is False


def test_get_inet_version_ok_and_error() -> None:
    assert InetUtils.get_inet_version("255.255.255.255") == "IPv4"
    assert InetUtils.get_inet_version("::1") == "IPv6"
    with pytest.raises(ValueError):
        InetUtils.get_inet_version("nope")


def test_hex_to_inet_ipv4_ipv6_and_errors() -> None:
    # IPv4 hex (8 chars)
    assert InetUtils.hex_to_inet("c0a80001") == "192.168.0.1"
    # spaces tolerated
    assert InetUtils.hex_to_inet(" c0 a8 00 01 ") == "192.168.0.1"

    # IPv6 hex (32 chars)
    v6 = "20010db8000000000000000000000001"
    assert InetUtils.hex_to_inet(v6) == "2001:db8::1"

    # invalid lengths
    with pytest.raises(ValueError):
        InetUtils.hex_to_inet("")
    with pytest.raises(ValueError):
        InetUtils.hex_to_inet("abcd")  # too short

    # bad hex content
    with pytest.raises(ValueError):
        InetUtils.hex_to_inet("zzzzzzzz")
