#!/usr/bin/env python3

from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import argparse
import asyncio
import json
import logging
from typing import List
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import DocsPnmCmCtlStatus
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.utils import Generate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    parser = argparse.ArgumentParser(description="Downstream OFDM RxMER")
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

    ofdm_idx_list = await cm.getDocsIf31CmDsOfdmChannelIdIndex()
    
    if not await cm.setDocsPnmBulk(tftp_server=args.tftp_ipv4, tftp_path=args.tftp_dest_dir):
        logging.error(f'Unable to set TFTP Server: {args.tftp_ipv4} and/or TFTP Path: {args.tftp_dest_dir}')
        exit(1)
            
    for idx in ofdm_idx_list:
        
        filename = f"rxmer_{idx}_{Generate.time_stamp()}.bin"
        print(f"Setting RxMER for OFDM index {idx} with filename {filename}")
        await cm.setDocsPnmCmDsOfdmRxMer(ofdm_idx=idx, rxmer_file_name=filename)
        
        while (True):
            if await cm.getDocsPnmCmCtlStatus() == DocsPnmCmCtlStatus.TEST_IN_PROGRESS:
                logging.warning('Testing in progress...')
                continue
            break
    
    results: List[dict] = []

    for entry in await cm.getDocsPnmCmDsOfdmRxMerEntry():
        results.append(entry.model_dump())

    filename = f".data/pnm/DocsPnmCmDsOfdmRxMerEntry-{args.mac}-{Generate.time_stamp()}.json"
    json_data = json.dumps(results, indent=2)

    FileProcessor(filename).write_file(json_data)
    
if __name__ == "__main__":
    asyncio.run(main())
