# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List, Union
from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisResponse, PnmResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import (
    CmSpecAnaAnalysisRequest, CmSpecAnaAnalysisResponse, CmSpectrumAnalyzerRequest)
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.service import CmSpectrumAnalysisService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class SpectrumAnalyzerRouter:
    """
    Concrete implementation of PnmFastApiRouter for handling Spectrum Analyzer-related requests.
    """
    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags:List[str] = ["PNM Operations - Spectrum Analyzer"]
        base_endpoint = "/spectrumAnalyzer"

        self.base_endpoint = base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"SpectrumAnalyzerRouter.{self.base_endpoint}")

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", 
                          response_model=Union[CmSpecAnaAnalysisResponse, SnmpResponse])
        async def get_measurement(request: CmSpectrumAnalyzerRequest):
            """
            **Perform Downstream OFDM Spectrum Capture**

            This endpoint performs a full-bandwidth spectrum capture from a DOCSIS cable modem.
            It returns both the decoded amplitude bin segments as floating-point values and the
            raw spectrum data in hexadecimal format for advanced signal anomaly analysis.

            ⚠️ **Note**: Ensure the configured start and end frequencies do not cross the diplexer boundary.
            Spectrum capture settings must respect diplexer constraints for DOCSIS 3.x and DOCSIS 4.0 (FDD).

            📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/spectrum-analyzer.md)
            """
            try:
                cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))
                
                status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg)                   
                
                service = CmSpectrumAnalysisService(cable_modem=cm, spec_analyzer_para=request.parameters)
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(f"[getMeasurement] Spectrum Analyzer failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="Spectrum Analyzer SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                return CmSpecAnaAnalysisResponse(
                    mac_address=request.mac_address,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict())

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", 
                          response_model=Union[PnmAnalysisResponse, SnmpResponse], 
                          response_model_exclude_unset=True)
        async def get_analysis(request: CmSpecAnaAnalysisRequest):
            try:
                
                status, msg = await CableModemServicePreCheck(mac_address=request.mac_address,
                                                                ip_address=request.ip_address).run_precheck()
                
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg)
                         
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getPlot] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Plot retrieval failed: {str(e)}")
            
# Required for dynamic auto-registration
router = SpectrumAnalyzerRouter().router
