#!/usr/bin/env python3

from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import argparse
import asyncio
import logging
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import DocsPnmCmCtlStatus
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.utils import Utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    parser = argparse.ArgumentParser(description="Downstream Symbol Capture")
    parser.add_argument("--mac", "-m", required=True, help="Mac address of cable modem")
    parser.add_argument("--inet", "-i", required=True, help="IP address of cable modem")
    parser.add_argument("--tftp-ipv4", "-t4", required=True, help="IPv4 TFTP server")
    parser.add_argument("--tftp-ipv6", "-t6", help="IPv6 TFTP server")
    parser.add_argument("--tftp-dest-dir", "-td", default="", help="TFTP server destination directory")
    parser.add_argument("--community-write", "-cw", default="private", help="SNMP write community string (default: private)")
    args = parser.parse_args()

    cm = CableModem(mac_address=MacAddress(args.mac), inet=Inet(args.inet), write_community=str(args.community_write))

    if not cm.is_ping_reachable():
        logging.error(f"{cm.get_inet_address} not reachable, exiting...")
        exit(1)

    logging.info(f"Connected to: {await cm.getSysDescr()}")
    
    if not await cm.setDocsPnmBulk(tftp_server=args.tftp_ipv4, tftp_path=args.tftp_dest_dir):
        logging.error(f'Unable to set TFTP Server: {args.tftp_ipv4} and/or TFTP Path: {args.tftp_dest_dir}')
        exit(1)
            
    for idx in await cm.getDocsIf31CmDsOfdmChannelIdIndex():
        
        filename = f"ds-symbol-capture_{idx}_{Utils.time_stamp()}.bin"
        print(f"Setting Symbol Capture for OFDM index {idx} with filename {filename}")
        await cm.setDocsPnmCmDsOfdmSymTrig(ofdm_idx=idx, symbol_trig_file_name=filename)
        
        while (True):
            if await cm.getDocsPnmCmCtlStatus() == DocsPnmCmCtlStatus.TEST_IN_PROGRESS:
                logging.info(f'Tesing in progress...')
                continue
            break

if __name__ == "__main__":
    asyncio.run(main())
