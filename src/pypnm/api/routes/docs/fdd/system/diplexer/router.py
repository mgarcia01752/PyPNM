
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union, Dict, Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.fdd.system.diplexer.service import FddDiplexerConfigService
from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion


class FddDiplexerConfigResult:
    """
    DOCSIS 4.0 FDD System Configuration Router

    Provides an endpoint to retrieve the currently active upstream and downstream
    diplexer band edge configuration from a DOCSIS 4.0 cable modem.
    """

    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/docs/fdd/system",
            tags=["DOCSIS 4.0 FDD System"])
        self.logger = logging.getLogger(self.__class__.__name__)
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post("/diplexer/configuration", response_model=Union[SnmpResponse, Dict[str, Any]])
        async def diplexer_config(request: SnmpRequest) -> Union[SnmpResponse, JSONResponse]:
            """
            **DOCSIS 4.0 FDD Diplexer Configuration**

            This endpoint queries the cable modem for its active diplexer band edge
            settings (Upstream Upper, Downstream Lower, Downstream Upper), as defined by
            TLVs 5.79, 5.80, and 5.81.

            - Validates CM accessibility and SNMP functionality.
            - Returns diplexer frequency configuration in MHz.
            - Returns an error response if the modem is unreachable or SNMP fails.

            [API Guide - FDD Diplexer Configuration](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/fdd/fdd-system-diplexer-configuration.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                check_docsis_version=[ClabsDocsisVersion.DOCSIS_40]).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)

            service = await FddDiplexerConfigService.fetch_fdd_diplexer_config(mac_address=mac, ip_address=ip)
            cfg = service.to_dict()
            return JSONResponse(content=cfg)

# Required for dynamic FastAPI router registration
router = FddDiplexerConfigResult().router
