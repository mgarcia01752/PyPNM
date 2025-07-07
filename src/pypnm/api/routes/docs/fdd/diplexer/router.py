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
from pypnm.api.routes.docs.fdd.diplexer.service import FddDiplexerBandEdgeCapabilityService


class FddDiplexerBandEdgeCapability:
    """
    FastAPI router class for exposing DOCSIS 4.0 FDD diplexer band edge capability via a REST endpoint.

    This endpoint allows clients to retrieve the upstream and downstream diplexer edge capabilities
    from a cable modem, typically used to validate DOCSIS 4.0 spectrum configuration support.

    Route:
        POST /docs/fdd/diplexer/bandEdgeCapability
    """

    def __init__(self):
        """
        Initialize the router, logger, and register API routes under the /docs/fdd/diplexer prefix.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/fdd/diplexer",
            tags=["DOCSIS 4.0 FDD Diplexer Band Edge Capability"]
        )
        self._add_routes()

    def _add_routes(self):
        """
        Defines the POST /bandEdgeCapability endpoint and attaches it to the router.
        """

        @self.router.post(
            "/bandEdgeCapability",
            response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_scqam_channels(request: PnmRequest):
            """
            Retrieve FDD diplexer band edge capability entries from the cable modem.

            Performs:
            - Precheck validation (MAC/IP reachability and SNMP readiness)
            - Capability data retrieval
            - Return as a list of channel entry-style dictionaries

            Returns:
                JSONResponse: Either populated capability data or an error response with status.
            """
            # Ensure modem is reachable and SNMP is operational
            status, msg = await CableModemServicePreCheck(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            ).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )

            # Fetch capability data from the cable modem
            service = FddDiplexerBandEdgeCapabilityService(
                mac_address=request.mac_address,
                ip_address=request.ip_address
            )
            data = await service.getFddDiplexerBandEdgeCapability()

            return JSONResponse(content=data)


# ✅ Required for dynamic auto-registration
router = FddDiplexerBandEdgeCapability().router
