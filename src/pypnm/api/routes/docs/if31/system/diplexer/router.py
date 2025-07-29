# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union
from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if31.system.diplexer.schemas import DiplexerResponse
from pypnm.api.routes.docs.if31.system.diplexer.service import DiplexerConfigService
from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion


class DiplexerConfigResult:
    
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/docs/if31/system",
                                tags=["DOCSIS 3.1 System"])
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post("/diplexer", response_model=Union[DiplexerResponse, SnmpResponse])
        async def diplexer_config(request: SnmpRequest) -> Union[DiplexerResponse, SnmpResponse]:
            """
            **DOCSIS 3.1 System Diplexer Configuration**

            Queries the modem for upstream/downstream diplexer frequency band configurations
            and hardware capability settings.

            Returns configuration values including:
            - Band edge frequencies
            - Diplexer capability codes
            - Configured and supported downstream frequency ranges

            📘 [API Guide - System Diplexer Configuration](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/diplexer-configuration.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving diplexer configuration for MAC: {mac}, IP: {ip}")

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                                                          validate_ofdm_exist=True).run_precheck()
            try:

                status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                                                              check_docsis_version=[ClabsDocsisVersion.DOCSIS_31]).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac),
                                        status=status,message=msg)  

                config = await DiplexerConfigService.fetch_diplexer_config(mac_address=mac, ip_address=ip)

                response = DiplexerResponse(mac_address=mac,
                                            status=ServiceStatusCode.SUCCESS,
                                            results=config)
                return response

            except HTTPException:
                raise
            
            except Exception as exc:
                self.logger.exception("Failed to fetch diplexer configuration")
                raise HTTPException(
                    status_code=500,
                    detail="Internal error retrieving diplexer configuration"
                )

router = DiplexerConfigResult().router
