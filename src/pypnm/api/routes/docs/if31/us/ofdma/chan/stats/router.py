# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Union

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmChannelEntryResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
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
            tags=["DOCSIS 3.1 Upstream OFDMA Channel Statistics"])
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_us_ofdma_channels(request: SnmpRequest):
            """
            **Upstream OFDMA Channel Statistics**

            Queries a cable modem for active upstream OFDMA channel configuration and health status.
            This includes subcarrier layout, transmission parameters, and timeout counters related to ranging.

            **Outputs include:**
            - Channel ID, subcarrier count, and frequency range
            - Transmit power and pre-equalization enablement
            - Cyclic prefix, roll-off period, and symbols per frame
            - Ranging timeouts and mute status indicators

            [API Guide - Upstream OFDMA Channel Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/stats.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving Upstream OFDMA Channel Statistics for MAC: {mac}, IP: {ip}")

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                                                          validate_ofdma_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)              
            
            service = UsOfdmChannelService(mac_address=mac, ip_address=ip)
            data = await service.get_ofdma_chan_entries()

            return JSONResponse(content=data)
        
# Required for dynamic auto-registration
router = UsOfdmaChannelRouter().router
