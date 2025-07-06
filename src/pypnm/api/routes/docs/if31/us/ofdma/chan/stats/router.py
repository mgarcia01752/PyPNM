# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Union

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmChannelEntryResponse, PnmRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if31.us.ofdma.chan.stats.service import UsOfdmChannelService


class UsOfdmaChannelRouter:
    """
    Router class for DOCSIS 3.1 Upstream OFDMA Channel Statistics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if31/us/ofdma/channel",
            tags=["DOCSIS 3.1 Upstream OFDMA Channel Statistics"]
        )
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_us_ofdma_channels(request: PnmRequest):
            """
            🔍 Upstream OFDMA Pre-Equalization Measurement

            Retrieves complex subcarrier coefficients for a DOCSIS 3.1 cable modem’s upstream OFDMA channel.
            Used in PNM analysis to identify in-channel reflections, group delay, and frequency-domain distortions.

            The result includes:
            - Complex coefficient pairs (Real, Imaginary)
            - Subcarrier spacing and frequency details
            - PNM capture metadata (e.g., timestamp, channel ID)

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/get-measurement-pre-equalization.md)

            ---
            **Request:** `PnmRequest`  
            **Response:** Pre-equalization `values[]` for OFDMA subcarriers + metadata
            """
        
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg,
                )              
            
            service = UsOfdmChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            data = await service.get_ofdma_chan_entries()
            return JSONResponse(content=data)
        
# ✅ Required for dynamic auto-registration
router = UsOfdmaChannelRouter().router
