#!/usr/bin/env python3
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025
import argparse
import asyncio
import sys
from typing import Optional

from pypnm.config.system_config_settings import SystemConfigSettings as S
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.ping import Ping


def _hdr(msg: str) -> None:
    print(f"\n=== {msg} ===")


def resolve_config(
    ip: str | None, mac: str | None, read_comm: str | None, timeout: int | None
):
    ip_s = ip or S.default_ip_address
    mac_s = mac or S.default_mac_address
    rc = read_comm or S.snmp_read_community
    to = int(timeout if timeout is not None else S.snmp_timeout)
    return ip_s, mac_s, rc, to


async def preflight(ip: str | None, mac: str | None, read_comm: str | None, timeout: int | None) -> int:
    ip_s, mac_s, rc, to = resolve_config(ip, mac, read_comm, timeout)

    _hdr("Preflight Inputs")
    print(f"IP: {ip_s}")
    print(f"MAC: {mac_s}")
    print(f"SNMPv2 Read Community: {rc!r}")
    print(f"Timeout (s): {to}")

    inet = Inet(ip_s)
    mac_obj = MacAddress(mac_s)

    # quick ping
    _hdr("ICMP Reachability")
    reachable = Ping.is_reachable(str(inet), timeout=1, count=1)
    print(f"Ping reachable: {reachable}")
    if not reachable:
        print("WARN: Ping failed — SNMP may still work if ICMP is blocked.")

    # SNMP sysDescr + MAC check
    _hdr("SNMPv2 Checks")
    cm = CableModem(mac_obj, inet, write_community=S.snmp_write_community)

    # CmSnmpOperation inside CableModem should use read community from config for GETs
    try:
        sys_descr = await asyncio.wait_for(cm.getSysDescr(), timeout=to)
    except Exception as e:
        print(f"ERROR: sysDescr fetch failed: {e}")
        return 2

    if not sys_descr:
        print("ERROR: Empty sysDescr response.")
        return 2

    print(f"sysDescr: {sys_descr}")

    try:
        if_phys = await asyncio.wait_for(cm.getIfPhysAddress(), timeout=to)
    except Exception as e:
        print(f"ERROR: ifPhysAddress fetch failed: {e}")
        return 2

    print(f"SNMP ifPhysAddress: {if_phys}")
    mac_ok = mac_obj.is_equal(if_phys)  # type: ignore[arg-type]
    print(f"MAC matches expected: {mac_ok}")

    rc_ok = reachable or True  # allow success even if ICMP blocked
    ok = bool(sys_descr) and (if_phys is not None) and mac_ok

    _hdr("Result")
    print("OK" if ok else "FAIL")
    return 0 if ok and rc_ok else 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Preflight ping + SNMPv2 check for Cable Modem using SystemConfigSettings defaults."
    )
    p.add_argument("--ip", help="Override IP address (default: SystemConfigSettings.default_ip_address)")
    p.add_argument("--mac", help="Override MAC address (default: SystemConfigSettings.default_mac_address)")
    p.add_argument("--read-community", help="Override SNMPv2 read community (default: SystemConfigSettings.snmp_read_community)")
    p.add_argument("--timeout", type=int, help="SNMP timeout seconds (default: SystemConfigSettings.snmp_timeout)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(preflight(args.ip, args.mac, args.read_community, args.timeout))


if __name__ == "__main__":
    sys.exit(main())
