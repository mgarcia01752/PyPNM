# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest
from api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from api.routes.common.service.status_codes import ServiceStatusCode
from api.routes.docs.if31.ds.ofdm.profile.stats.schemas import OfdmProfileStatsResponse
from api.routes.docs.if31.ds.ofdm.profile.stats.service import OfdmProfileStatsService



class OfdmProfileStatsRouter:
    """
    Router class for DOCSIS 3.1 Downstream OFDM Modulation Profile Statistics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if31/ds/ofdm/profile",
            tags=["DOCSIS 3.1 Downstream OFDM Modulation Profile Stats"]
        )
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=OfdmProfileStatsResponse)
        async def get_ofdm_profile_stats(request: SnmpRequest):
            """
            Retrieve DOCSIS 3.1 downstream OFDM profile statistics.
            """
            status, msg = CableModemServicePreCheck(mac_address=request.mac_address,
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return OfdmProfileStatsResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )
                                 
            stats_data = await OfdmProfileStatsService.fetch_profile_stats(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            
            return OfdmProfileStatsResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.SUCCESS, 
                data=stats_data)
        
# ✅ Required for dynamic auto-registration
router = OfdmProfileStatsRouter().router
