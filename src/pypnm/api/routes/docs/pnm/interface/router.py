
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Union, Dict

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import (SnmpRequest, SnmpResponse,)
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import (CableModemServicePreCheck,)
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.interface.service import InterfaceStatsService

class InterfaceStatsRouter:
    """
    FastAPI router for retrieving DOCSIS interface statistics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/pnm/interface",
            tags=["Interface Statistics"])
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[SnmpResponse])
        async def get_interface_stats(request: SnmpRequest) -> SnmpResponse:
            """
            Retrieve DOCSIS interface statistics grouped by interface type.

            [API Guide - Retrieve DOCSIS Interface Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/pnm/interface/stats.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving interface statistics for MAC: {mac}, IP: {ip}")

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse( mac_address=str(mac), status=status, message=msg)

            service = InterfaceStatsService(mac_address=mac, ip_address=ip)
            data: Dict[str, List[Dict]] = await service.get_interface_stat_entries()

            return JSONResponse(content=data) # type: ignore

# Required for dynamic auto-registration
router = InterfaceStatsRouter().router
