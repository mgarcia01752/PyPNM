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
            📶 **DOCSIS 3.0 Upstream ATDMA Channel Stats**

            Retrieves DOCSIS 3.0 upstream SC-QAM (ATDMA) channel configuration and operational statistics.

            **The response includes modulation settings:**
            - Frequency parameters
            - Pre-equalization status
            - Transmit power
            - Ranging behavior
            
            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/scqam/chan/stats.md)

            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                          ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return PnmChannelEntryResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg)                  
            
            service = UsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address)
            
            data = await service.get_upstream_entries()
            return JSONResponse(content=data)
        
        @self.router.post("/preEqualization", response_model=List[PnmChannelEntryResponse])
        async def get_us_scqam_pre_equalizations(request: SnmpRequest):
            """
            **DOCSIS 3.0 Upstream Pre-Equalization Coefficients**

            Retrieves forward and reverse pre-equalization tap coefficients from a DOCSIS 3.0 SC-QAM upstream channel.

            **The output includes:**
            - Main tap location
            - Number of forward and reverse taps
            - Complex tap coefficients with real/imag/magnitude/magnitude_dB

            Used to analyze echo cancellation behavior and upstream plant quality.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/scqam/chan/pre-equalization.md)

            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return PnmChannelEntryResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg)
                                  
            service = UsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address)
            
            data = await service.get_upstream_pre_equalizations()
            return JSONResponse(content=data)        

# ✅ Required for dynamic auto-registration
router = UsScQamChannelRouter().router
