# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union

from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmMeasurementResponse, PnmAnalysisRequest, PnmAnalysisResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.us.ofdma.pre_equalization.service import CmUsOfdmaPreEqService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class UsOfdmaPreEqualizationRouter(PnmFastApiRouter):
    """
    Concrete implementation of PnmFastApiRouter for handling Upstream OFDMA Pre-Equalization related requests.
    """
    def __init__(self):
        
        measurement_description = """
**Upstream OFDMA Pre-Equalization Measurement**

Captures raw complex tap coefficients from a DOCSIS 3.1 cable modem’s upstream OFDMA channel.

This measurement provides the foundational data used for Proactive Network Maintenance (PNM),
including detection of group delay, in-channel reflections, and frequency-dependent impairments.

**Included in the response:**
- Real/Imaginary coefficient pairs per subcarrier
- Subcarrier frequency spacing and zero-index frequency
- Full PNM file metadata (timestamp, channel ID, file format)

🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/pre-equalization.md#get-measurement)
"""

        analysis_description = """
**Analyze OFDMA Pre-Equalization Coefficients (DOCSIS 3.1)**

Processes upstream complex coefficients into structured per-subcarrier analysis.
This endpoint enables advanced insight into upstream channel quality using statistical and signal-domain metrics.

**Outputs include:**
- Subcarrier magnitudes (dB)
- Group delay (µs) inferred from phase slopes
- Reconstructed complex values (Real/Imaginary)
- Frequency mapping per subcarrier

🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/pre-equalization.md#get-analysis)
"""
        super().__init__(
            prefix="/docs/pnm/us/ofdma",
            tags=["PNM Operations - Upstream OFDMA Pre-Equalization"],
            base_endpoint="/preEqualization",
            set_measurement_description = measurement_description,
            set_analysis_description = analysis_description)
        self.logger = logging.getLogger("UsOfdmaPreEqualization")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
  
        self.logger.info(f"Retrieving Upstream OFDMA Pre-Equalization measurement for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )       
        
        service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return PnmMeasurementResponse(mac_address=request.mac_address,
                                          message="Unable to complete Upstream OFDMA Pre-Equalization measurement.",
                                          status=msg_rsp.status, measurement={})

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
    
        return PnmMeasurementResponse(mac_address=request.mac_address,
                                      status=msg_rsp.status, 
                                      measurement=msg_rsp.payload) # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, SnmpResponse]:

        self.logger.info(f"Generating Upstream OFDMA Pre-Equalization Analysis Type: {request.analysis.type} for MAC {request.mac_address}")
        
        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )       
        
        service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
                
        return PnmAnalysisResponse(mac_address=request.mac_address,
                                      status=ServiceStatusCode.SUCCESS,
                                      data=analysis.get_results()) 
        
# ✅ Required for dynamic auto-registration
router = UsOfdmaPreEqualizationRouter().router

