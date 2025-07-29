# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if31.docsis.service import DocsisBaseCapabilityService

class BaseCapabilityRouter:
    """
    DOCSIS 3.1 Base Capability API Router

    Provides an endpoint to retrieve the DOCSIS version capability of a cable modem.
    """

    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/docs/if31/docsis",
            tags=["DOCSIS 3.1 DOCSIS Base Capability"])
        self.logger = logging.getLogger(self.__class__.__name__)
        self._register_routes()

    def _register_routes(self) -> None:
        
        @self.router.post("/baseCapability", response_model=SnmpResponse)
        async def base_capability(request: SnmpRequest) -> SnmpResponse:
            """
            **DOCSIS 3.1 Base Capability**

            Retrieves the supported DOCSIS version from the cable modem
            using the `docsIf31DocsisBaseCapability` OID. This value
            indicates the maximum DOCSIS version supported by the device.

            This attribute supersedes `docsIfDocsisBaseCapability` as defined in RFC 4546.

            📘 [API Guide - DOCSIS 3.1 Base Capability](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/docsis-base-configuration.md)
            """

            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving DOCSIS 3.1 Base Capability for MAC: {mac}, IP: {ip}")

            try:
                # Verify modem is reachable
                status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip).run_precheck()

                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.cable_modem.mac_address),
                        status=status,message=msg)

                result = await DocsisBaseCapabilityService.fetch_docsis_base_capabilty(mac_address=mac, ip_address=ip)

                return SnmpResponse(
                    mac_address=str(mac),
                    status=ServiceStatusCode.SUCCESS,
                    message="DOCSIS Base Capability retrieved successfully.",
                    results=result.model_dump())

            except HTTPException:
                raise

            except Exception as exc:
                self.logger.exception("Failed to fetch DOCSIS base capability")
                raise HTTPException(
                    status_code=500,
                    detail="Internal error retrieving DOCSIS base capability")

# Required for dynamic FastAPI router registration
router = BaseCapabilityRouter().router
