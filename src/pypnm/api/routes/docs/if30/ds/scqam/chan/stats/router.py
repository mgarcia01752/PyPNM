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
            tags=["DOCSIS 3.0 Downstream SC-QAM Channel Stats"])
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_scqam_ds_channels(request: PnmRequest):
            """
            **DOCSIS 3.0 Downstream SC-QAM Channel Stats**

            Retrieves downstream SC-QAM channel configuration and signal quality metrics
            for a DOCSIS 3.0 modem, including modulation type, frequency, RxMER, power,
            and error counters.

            This endpoint is used for monitoring downstream health and identifying RF impairments
            such high uncorrectable error rates.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/scqam/stats.md)

            """
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                          ip_address=request.ip_address).run_precheck()
            
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg)              
            
            service = DsScQamChannelService(
                mac_address=request.mac_address,
                ip_address=request.ip_address)
            
            data = await service.get_scqam_chan_entries()
            return JSONResponse(content=data)

# ✅ Required for dynamic auto-registration
router = DsScQamChannelRouter().router
