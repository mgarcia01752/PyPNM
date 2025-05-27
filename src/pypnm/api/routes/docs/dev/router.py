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
        @self.router.post("/eventLog", 
                          response_model=EventLogResponse)
        async def get_event_log(request: BaseDeviceConnectRequest):
            """
            POST /docs/dev/eventLog
            Retrieves DOCSIS event log entries from a cable modem by IP and MAC address.
            """
            status, msg = CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                logger.error(msg)
                return EventLogResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg,
                    logs=[]
                )                
            
            try:
                service = CmDocsDevService(
                    mac_address=request.mac_address,
                    ip_address=request.ip_address)
                
                log_entries = await service.fetch_event_log()
                return EventLogResponse(
                    mac_address=str(service.mac),
                    status=ServiceStatusCode.SUCCESS,
                    logs=log_entries
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to fetch event log")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/reset", response_model=SnmpResponse)
        async def reset_cable_modem(request: BaseDeviceConnectRequest):
            
            status, msg = CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )               
            
            try:
                service = CmDocsDevService(
                    mac_address=request.mac_address,
                    ip_address=request.ip_address
                )
                result = await service.reset_cable_modem()
                return JSONResponse(content=result.model_dump())
            
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to reset cable modem")
                raise HTTPException(status_code=500, detail=str(e))

router = DocsDevRouter().router