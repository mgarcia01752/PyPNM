# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Union, Dict

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (PnmRequest,)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import (SnmpResponse,)
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
            tags=["Interface Statistics"]
        )
        self._add_routes()

    def _add_routes(self):
        @self.router.post("/stats", response_model=Union[SnmpResponse])
        async def get_interface_stats(request: PnmRequest):
            """
            📶 Retrieve DOCSIS interface statistics grouped by interface type.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/pnm/interface/stats.md)
            """
            status, msg = await CableModemServicePreCheck(
                mac_address=request.mac_address,
                ip_address=request.ip_address).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg)

            service = InterfaceStatsService(
                mac_address=request.mac_address,
                ip_address=request.ip_address)
            data: Dict[str, List[Dict]] = await service.get_interface_stat_entries()

            return JSONResponse(content=data)

# ✅ Required for dynamic auto-registration
router = InterfaceStatsRouter().router
