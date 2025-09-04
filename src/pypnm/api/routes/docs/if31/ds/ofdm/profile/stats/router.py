
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if31.ds.ofdm.profile.stats.schemas import OfdmProfileStatsResponse
from pypnm.api.routes.docs.if31.ds.ofdm.profile.stats.service import OfdmProfileStatsService

class OfdmProfileStatsRouter:
    """
    Router class for DOCSIS 3.1 Downstream OFDM Modulation Profile Statistics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if31/ds/ofdm/profile",
            tags=["DOCSIS 3.1 Downstream OFDM Modulation Profile Stats"])
        
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=OfdmProfileStatsResponse)
        async def get_ofdm_profile_stats(request: SnmpRequest):
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving DOCSIS 3.1 Downstream OFDM profile statistics for MAC: {mac}, IP: {ip}")

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                                                          validate_ofdm_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return OfdmProfileStatsResponse(mac_address=str(mac),
                                                status=status, message=msg)
                                 
            stats_data = await OfdmProfileStatsService.fetch_profile_stats(mac_address=mac, ip_address=ip)
            
            return OfdmProfileStatsResponse(
                mac_address=mac,
                status=ServiceStatusCode.SUCCESS, 
                data=stats_data) # type: ignore
        
# Required for dynamic auto-registration
router = OfdmProfileStatsRouter().router
