#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import argparse
import asyncio
import logging
from api.routes.common.extended.common_messaging_service import MessageResponse
from api.routes.common.extended.common_process_service import CommonProcessService
from api.routes.common.service.status_codes import ServiceStatusCode
from api.routes.docs.pnm.ds.ofdm.chan_est_coeff.service import CmDsOfdmChanEstCoefService
from docsis.cable_modem import CableModem
from lib.file_processor import FileProcessor
from lib.inet import Inet
from lib.mac_address import MacAddress
from lib.utils import TimeUnit, Utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    parser = argparse.ArgumentParser(description="RxMER Set & Go Service")
    parser.add_argument("--mac", "-m", required=True, help="MAC address of cable modem")
    parser.add_argument("--inet", "-i", required=True, help="IP address of cable modem")
    parser.add_argument("--tftp-ipv4", "-t4", required=True, help="IPv4 TFTP server")
    parser.add_argument("--community-write", "-cw", default="private", help="SNMP write community string (default: private)")    

    args = parser.parse_args()

    # Initialize CableModem object
    cm = CableModem(mac_address=MacAddress(args.mac), inet=Inet(args.inet), write_community=str(args.community_write))

    # Check if the cable modem is reachable
    if not cm.is_ping_reachable():
        logging.error(f"{cm.get_inet_address} not reachable, exiting...")
        exit(1)

    logging.info(f"Connected to: {await cm.getSysDescr()}")
    
    service = CmDsOfdmChanEstCoefService(cm)
    msg_rsp:MessageResponse = await service.set_and_go()

    if msg_rsp.status != ServiceStatusCode.SUCCESS:
        print(f'ERROR: {msg_rsp.status.name}')
        exit(1)

    cps = CommonProcessService(msg_rsp)
    msg_rsp:MessageResponse = cps.process()
    
    for payload in msg_rsp.payload: # type: ignore
        FileProcessor(f"output/chan-est-{str(Utils.time_stamp(TimeUnit.MILLISECONDS))}.json").write_file(payload)


if __name__ == "__main__":
    asyncio.run(main())
