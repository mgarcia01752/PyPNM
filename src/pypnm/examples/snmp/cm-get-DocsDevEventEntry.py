#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import argparse
import asyncio
import logging

from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    parser = argparse.ArgumentParser(description="Get DocsDevEventEntry")
    parser.add_argument("--mac", "-m", required=True, help="MAC address of cable modem")
    parser.add_argument("--inet", "-i", required=True, help="IP address of cable modem")
    parser.add_argument("--community-write", "-cw", default="private", help="SNMP write community string (default: private)")
    args = parser.parse_args()

    cm = CableModem(mac_address=MacAddress(args.mac), inet=Inet(args.inet), write_community=str(args.community_write))

    if not cm.is_ping_reachable():
        logging.error(f"{cm.get_inet_address} not reachable, exiting...")
        exit(1)
          
    logging.info(f"Connected to: {await cm.getSysDescr()}")
    
    event_list = await cm.getDocsDevEventEntry()
    
    for event in event_list:
        print(f'{event.to_dict()}') # type: ignore

if __name__ == "__main__":
    asyncio.run(main())
