
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from http import HTTPStatus
import logging
from typing import List, Union
from enum import Enum

from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.system.schemas import SysDescrResponse, SysRequest, SysUpTimeResponse
from pypnm.api.routes.system.service import SystemSnmpService

class SystemRouter:
    """
    FastAPI router for system-level SNMP endpoints:
      - POST /system/sysDescr : Retrieve device sysDescr
      - POST /system/upTime  : Retrieve device sysUpTime
    """
    def __init__(
        self,
        prefix: str = "/system",
        tags: List[Union[str, Enum]] = ["DOCSIS System"]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(__name__)
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post("/sysDescr",response_model=Union[SysDescrResponse, SnmpResponse])
        async def get_sysdescr(request: SysRequest) -> Union[SysDescrResponse, SnmpResponse]:
            """
            **Retrieve DOCSIS System Description**

            This endpoint performs an SNMP query to fetch the system description (`sysDescr`) string
            from a DOCSIS modem, then parses it to extract hardware, software, bootloader, vendor, and model details.

            [API Guide - DOCSIS System Description](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/system-description.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving sysDescr for MAC: {mac}, IP: {ip}")

            try:
                status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg,)                     
                
                return await SystemSnmpService.get_sysdescr(request)
            
            except Exception as exc:
                self.logger.error(f"sysDescr error for {request.cable_modem.mac_address}@{request.cable_modem.ip_address}: {exc}")
                # You can return more detailed errors based on exception type if you like
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve sysDescr")

        @self.router.post("/upTime", response_model=Union[SysUpTimeResponse, SnmpResponse])
        async def get_uptime(request: SysRequest) -> Union[SysUpTimeResponse, SnmpResponse] :
            """
            **Fetch DOCSIS Device System Uptime**

            Retrieves the SNMP system uptime from a DOCSIS cable modem, expressed as a human-readable
            duration (`hh:mm:ss.microseconds`). Useful for identifying recent reboots or uptime trends.

            [API Guide - Device System Uptime](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/up-time.md)

            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving sysUpTime for MAC: {mac}, IP: {ip}")

            try:
                status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg)                          
                
                return await SystemSnmpService.get_sys_up_time(request) 
            
            except Exception as exc:
                self.logger.error(f"sysUpTime error for {mac}@{ip}: {exc}")
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to retrieve sysUpTime")

router = SystemRouter().router
