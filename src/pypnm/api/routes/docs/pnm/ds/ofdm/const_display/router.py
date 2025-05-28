# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List, Union

from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmAnalysisResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.const_display.schemas import PnmConstellationDisplayRequest, PnmConstellationDisplayResponse
from pypnm.api.routes.docs.pnm.ds.ofdm.const_display.service import CmDsOfdmConstDisplayService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class ConstellationDisplayRouter:
    """
    Router implementation for handling DOCSIS 3.1 Downstream OFDM Constellation Display
    Proactive Network Maintenance (PNM) requests.

    This router provides a POST endpoint to trigger SNMP-based measurement collection
    from a target cable modem and return the processed constellation display data.
    """

    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags: List[str] = ["PNM Operations - Downstream OFDM Constellation Display"]
        self.base_endpoint = "/constellationDisplay"

        self.base_endpoint = self.base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags) # type: ignore
        self.logger = logging.getLogger(f"ConstellationDisplayRouter.{self.base_endpoint}")
        self._add_routes()
        
    def _add_routes(self):

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", response_model=Union[PnmConstellationDisplayResponse,SnmpResponse])
        async def get_measurement(request: PnmConstellationDisplayRequest) -> Union[PnmConstellationDisplayResponse, SnmpResponse]:
            """
            Trigger constellation display measurement for a specific cable modem.

            Parameters:
                request (ConstDispRequest): Contains MAC address, IP address, and other test params.

            Returns:
                ConstDispResponse: SNMP test status and decoded constellation display results.

            Raises:
                HTTPException: If SNMP execution or post-processing fails.
            """
            try:
                cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))
                
                status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg
                    )                    
                
                modulation_order_offset = request.modulation_order_offset
                number_sample_symbol = request.number_sample_symbol

                service = CmDsOfdmConstDisplayService(
                    cable_modem=cm,
                    modulation_order_offset=modulation_order_offset,
                    number_sample_symbol=number_sample_symbol,
                )
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(
                        f"[getMeasurement] Constellation Display failed with status: {msg_rsp.status.name}"
                    )
                    raise HTTPException(status_code=500, detail="Constellation Display SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                return PnmConstellationDisplayResponse(
                    mac_address=request.mac_address,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict(),
                )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", response_model=Union[PnmAnalysisResponse, SnmpResponse])
        async def get_analysis(request: PnmAnalysisRequest):
            
            status, msg = await CableModemServicePreCheck(mac_address=request.mac_address, 
                                                    ip_address=request.ip_address).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )               
            
            try:
                pass
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getPlot] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Plot retrieval failed: {str(e)}")

# ✅ Required for dynamic auto-registration
router = ConstellationDisplayRouter().router
