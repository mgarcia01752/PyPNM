# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging

from api.routes.system.schemas import SysRequest, SysDescrResponse, SysUpTimeResponse
from api.routes.common.service.status_codes import ServiceStatusCode
from docsis.cable_modem import CableModem
from docsis.data_type.sysDescr import SystemDescriptor
from lib.inet import Inet
from lib.mac_address import MacAddress

logger = logging.getLogger(__name__)


class SystemSnmpService:
    """
    Service class for retrieving SNMP system-level information from a cable modem,
    such as sysDescr and sysUpTime.
    """

    @staticmethod
    async def get_sysdescr(request: SysRequest) -> SysDescrResponse:
        """
        Retrieve the sysDescr (system description) from the cable modem.

        Args:
            request (SysRequest): connection params + SNMP config.

        Returns:
            SysDescrResponse: 
              - on success: status=SUCCESS, sys_descr contains OID→description map
              - on failure: status=FAILURE, message=error text, sys_descr=None
        """
        try:
            logger.info(f"Fetching sysDescr for {request.mac_address}@{request.ip_address}")
            cm = CableModem(
                mac_address=MacAddress(request.mac_address),
                inet=Inet(request.ip_address)
            )
            sys_descr: SystemDescriptor = await cm.getSysDescr()
                        
            return SysDescrResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.SUCCESS,
                results={"sysDescr":sys_descr},
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve sysDescr: {e}", exc_info=True)
            return SysDescrResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.FAILURE,
                message=str(e),
                results={},
            )

    @staticmethod
    async def get_sys_up_time(request: SysRequest) -> SysUpTimeResponse:
        """
        Retrieve the sysUpTime from the cable modem.

        Args:
            request (SysRequest): connection params + SNMP config.

        Returns:
            SysUpTimeResponse:
              - on success: status=SUCCESS, uptime contains human‐readable string
              - on failure: status=FAILURE, message=error text, uptime=""
        """
        try:
            logger.info(f"Fetching sysUpTime for {request.mac_address}@{request.ip_address}")
            cm = CableModem(
                mac_address=MacAddress(request.mac_address),
                inet=Inet(request.ip_address)
            )
            
            raw_uptime: str = await cm.getSysUpTime()
            logger.debug("sysUpTime raw value: %r", raw_uptime)
            return SysUpTimeResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.SUCCESS,
                results={"uptime": raw_uptime},
            )
        
        except Exception as e:
            logger.error(f"Failed to retrieve sysUpTime: {e}", exc_info=True)
            return SysUpTimeResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.FAILURE,
                message=str(e),
                results={"uptime":""},
            )
