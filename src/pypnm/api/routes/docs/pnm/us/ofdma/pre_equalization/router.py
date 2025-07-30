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

[API Guide - OFDMA Pre-Equalization Measurement](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/pre-equalization.md#get-measurement)
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

[API Guide - OFDMA Pre-Equalization Coefficients Analysis](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/pre-equalization.md#get-analysis)
"""

        measurement_statistics_description = """
**Analyze OFDMA Pre-Equalization Coefficients (DOCSIS 3.1)**

This endpoint retrieves summary metrics for upstream pre-equalization, including amplitude ripple,
group delay ripple, slope, mean values, and file references per OFDMA upstream channel.

[API Guide - OFDMA Pre-Equalization Coefficients Measurement](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/us/ofdma/pre-equalization.md#get-measurement-statistics)
"""

        super().__init__(
            prefix="/docs/pnm/us/ofdma",
            tags=["PNM Operations - Upstream OFDMA Pre-Equalization"],
            base_endpoint="/preEqualization",
            set_measurement_description = measurement_description,
            set_analysis_description = analysis_description,
            set_measurement_statistics_description=measurement_statistics_description)
        self.logger = logging.getLogger("UsOfdmaPreEqualization")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:

        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Starting Upstream OFDMA Pre-Equalization measurement for MAC: {mac}, IP: {ip}")

        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdma_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg)       
        
        service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return PnmMeasurementResponse(mac_address=mac,
                                          message="Unable to complete Upstream OFDMA Pre-Equalization measurement.",
                                          status=msg_rsp.status, measurement={})

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
    
        return PnmMeasurementResponse(mac_address=mac,
                                      status=msg_rsp.status, 
                                      measurement=msg_rsp.payload) # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, SnmpResponse]:
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Starting Upstream OFDMA Pre-Equalization analysis for MAC: {mac}, IP: {ip}, Analysis Type: {request.analysis.type}")

        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdma_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg)       
        
        service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
                
        return PnmAnalysisResponse(mac_address=mac, 
                                   status=ServiceStatusCode.SUCCESS,
                                   data=analysis.get_results()) 

    async def get_measurement_statistics_logic(self, request: PnmRequest) -> Union[SnmpResponse]:       # type: ignore
        """
        Retrieves upstream OFDMA Pre-Equalization measurement statistics for a DOCSIS 3.1 cable modem.

        This includes summary values such as:
        - Amplitude ripple (RMS and peak-to-peak)
        - Group delay ripple and slope
        - Mean amplitude and group delay
        - Pre-equalization adjustment status
        - Associated capture and update filenames
        - SNMP measurement status codes
        """
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Fetching Upstream OFDMA Pre-Equalization Measurement Statistics for MAC: {mac}, IP: {ip}")

        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdma_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status,message=msg)

        service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
        service_measure_stat = await service.get_pnm_measurement_statistics()

        return SnmpResponse(
            mac_address=str(mac),
            status=ServiceStatusCode.SUCCESS,
            message="Measurement Statistics for OFDMA Pre-Equalization",
            results=service_measure_stat)
   
# Required for dynamic auto-registration
router = UsOfdmaPreEqualizationRouter().router

