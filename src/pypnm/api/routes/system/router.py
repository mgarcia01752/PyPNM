# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List, Union
from enum import Enum

from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.system.schemas import SysDescrResponse, SysUpTimeResponse
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
        async def get_sysdescr(request: SnmpRequest) -> Union[SysDescrResponse, SnmpResponse]:
            """
            **Retrieve DOCSIS System Description**

            This endpoint performs an SNMP query to fetch the system description (`sysDescr`) string
            from a DOCSIS modem, then parses it to extract hardware, software, bootloader, vendor, and model details.

            📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/system-description.md)

            ---
            - Uses standard SNMP OID: `1.3.6.1.2.1.1.1.0`
            - Field parsing is vendor-specific (e.g., Hitron, Technicolor, ARRIS)
            - Returns structured metadata fields and `is_empty` flag if parsing fails
            """
            try:
                status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                        ip_address=request.ip_address).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg,)                     
                
                return await SystemSnmpService.get_sysdescr(request)
            
            except Exception as exc:
                self.logger.error(f"sysDescr error for {request.mac_address}@{request.ip_address}: {exc}")
                # You can return more detailed errors based on exception type if you like
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve sysDescr")

        @self.router.post("/upTime", response_model=Union[SysUpTimeResponse, SnmpResponse])
        async def get_uptime(request: SnmpRequest) -> Union[SysUpTimeResponse, SnmpResponse] :
            """
            Handle POST /system/upTime
            """
            try:
                status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                        ip_address=request.ip_address).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg)                          
                
                return await SystemSnmpService.get_sys_up_time(request) 
            
            except Exception as exc:
                self.logger.error(f"sysUpTime error for {request.mac_address}@{request.ip_address}: {exc}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve sysUpTime"
                )

router = SystemRouter().router
