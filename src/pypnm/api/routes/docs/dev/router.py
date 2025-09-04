
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_connect_request import BaseDeviceConnectRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.dev.schemas import EventLogResponse
from pypnm.api.routes.docs.dev.service import CmDocsDevService

logger = logging.getLogger(__name__)

class DocsDevRouter:
    """
    Router class for DOCSIS device management operations such as retrieving event logs
    and resetting cable modems.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/docs/dev", tags=["DOCSIS Device"])
        self.logger = logging.getLogger(self.__class__.__name__)
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/eventLog", response_model=EventLogResponse)
        async def get_event_log(request: BaseDeviceConnectRequest):
            """
            **Retrieve DOCSIS Cable Modem Event Log**

            This endpoint fetches the device event log from a DOCSIS cable modem using SNMP. 
            Entries typically include system-level events such as T3/T4 timeouts, partial service alerts, 
            reboots, and other diagnostic messages useful for proactive network maintenance.

            [API Guide - Cable Modem Event Log](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/event-log.md)

            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving event log for MAC: {mac}, IP: {ip}")            
            status, msg = await CableModemServicePreCheck(mac_address=mac,ip_address=ip).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                logger.error(msg)
                return EventLogResponse(mac_address=str(mac), status=status, message=msg, logs=[])                
            
            try:
                service = CmDocsDevService(mac_address=mac,ip_address=ip)
                log_entries = await service.fetch_event_log()
                return EventLogResponse(mac_address=str(service.mac), 
                                        status=ServiceStatusCode.SUCCESS,
                                        logs=log_entries)
                
            except HTTPException:
                raise
            
            except Exception as e:
                logger.exception("Failed to fetch event log, Mac: {mac}, IP: {ip}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/reset", response_model=SnmpResponse)
        async def reset_cable_modem(request: BaseDeviceConnectRequest):
            """
            **Reset a DOCSIS Cable Modem**

            Sends a remote SNMP reset command to the target cable modem, instructing it to reboot.

            This is typically used for maintenance, recovery from fault states, or in automated diagnostics
            workflows to bring the device back to an operational state.

            [API Guide - Reset DOCSIS Cable Modem](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/reset-cm.md)

            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Resetting cable modem for MAC: {mac}, IP: {ip}")           
            status, msg = await CableModemServicePreCheck(mac_address=mac,ip_address=ip).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac),status=status,message=msg)               
            
            try:
                service = CmDocsDevService(mac_address=mac,ip_address=ip)
                result = await service.reset_cable_modem()
                return JSONResponse(content=result.model_dump())
            
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(f"Failed to reset cable modem, Mac: {mac}, IP: {ip}")
                raise HTTPException(status_code=500, detail=str(e))

router = DocsDevRouter().router