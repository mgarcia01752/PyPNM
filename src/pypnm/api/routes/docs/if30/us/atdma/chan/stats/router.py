# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmChannelEntryResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if30.us.atdma.chan.stats.service import UsScQamChannelService

class UsScQamChannelRouter:
    """
    Router class to handle DOCSIS 3.0 Upstream ATDMA SC-QAM Channel Statistics endpoints.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if30/us/scqam/chan",
            tags=["DOCSIS 3.0 Upstream ATDMA Channel Stats"]
        )
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=List[PnmChannelEntryResponse])
        async def get_us_scqam_upstream_channels(request: SnmpRequest):
            """
            POST /docs/if30/us/scqam/chan/stats

            Retrieves DOCSIS 3.0 upstream ATDMA SC-QAM channel statistics from a cable modem.

            Parameters:
            - `request.mac_address` (str): MAC address of the cable modem.
            - `request.ip_address` (str): IP address of the cable modem.

            Returns:
            - List[PnmChannelEntryResponse]: List of upstream channel statistics.
            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return PnmChannelEntryResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )                  
            
            service = UsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            data = await service.get_upstream_entries()
            return JSONResponse(content=data)
        
        @self.router.post("/preEqualization", response_model=List[PnmChannelEntryResponse])
        async def get_us_scqam_pre_equalizations(request: SnmpRequest):
            """
            POST /docs/if30/us/scqam/chan/stats

            Retrieves DOCSIS 3.0 upstream ATDMA SC-QAM channel statistics from a cable modem.

            Parameters:
            - `request.mac_address` (str): MAC address of the cable modem.
            - `request.ip_address` (str): IP address of the cable modem.

            Returns:
            - List[PnmChannelEntryResponse]: List of upstream channel statistics.
            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return PnmChannelEntryResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )                  
            service = UsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            data = await service.get_upstream_pre_equalizations()
            return JSONResponse(content=data)        

# ✅ Required for dynamic auto-registration
router = UsScQamChannelRouter().router
