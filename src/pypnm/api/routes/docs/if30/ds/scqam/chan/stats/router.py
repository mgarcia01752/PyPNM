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
from pypnm.api.routes.docs.if30.ds.scqam.chan.stats.service import DsScQamChannelService

class DsScQamChannelRouter:
    """
    Router class to handle DOCSIS 3.0 Downstream SC-QAM Channel Statistics endpoints.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if30/ds/scqam/chan",
            tags=["DOCSIS 3.0 Downstream SC-QAM Channel Stats"]
        )
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_scqam_channels(request: PnmRequest):
            """
            POST /docs/if30/ds/scqam/chan/stats

            Retrieves DOCSIS 3.0 SC-QAM downstream channel statistics from a cable modem.

            Parameters:
            - `req.mac_address` (str): MAC address of the target modem.
            - `req.ip_address` (str): IP address of the target modem.

            Returns:
            - List[PnmChannelEntryResponse]: List of channel statistics entries.
            """
            status, msg = CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )              
            
            service = DsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            data = await service.get_scqam_chan_entries()
            return JSONResponse(content=data)

# ✅ Required for dynamic auto-registration
router = DsScQamChannelRouter().router
