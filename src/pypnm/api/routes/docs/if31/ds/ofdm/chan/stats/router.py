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
from pypnm.api.routes.docs.if31.ds.ofdm.chan.stats.service import DsOfdmChannelService

class DsOfdmChannelStatsRouter:
    """
    Router class for DOCSIS 3.1 Downstream OFDM Channel Physical Layer Statistics API.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if31/ds/ofdm/channel",
            tags=["DOCSIS 3.1 Downstream OFDM Channel Physical Layer Statistics"]
        )
        self._add_routes()

    def _add_routes(self):
        
        @self.router.post("/stats", response_model=List[PnmChannelEntryResponse])
        async def get_ds_ofdm_channels(request: SnmpRequest):
            """
            **Downstream OFDM Modulation Profile Statistics (DOCSIS 3.1)**

            Gathers per-profile traffic and FEC correction metrics from each active downstream OFDM channel.
            Profiles typically include IDs 0-4 and always include profile `255` (NCP).

            **Outputs include:**
            - Total, corrected, and uncorrectable codewords
            - Frame counts (unicast/multicast) and CRC errors
            - Octet counters segmented by profile
            - Support for multiple OFDM channels per modem

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/stats.md)
            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                          ip_address=request.ip_address,
                                                          validate_ofdm_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return PnmChannelEntryResponse(
                    mac_address=str(request.mac_address),
                    status=status, message=msg)     
                         
            service = DsOfdmChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address)
            
            data = await service.get_ofdm_chan_entries()
            return JSONResponse(content=data)
        
# ✅ Required for dynamic auto-registration
router = DsOfdmChannelStatsRouter().router
