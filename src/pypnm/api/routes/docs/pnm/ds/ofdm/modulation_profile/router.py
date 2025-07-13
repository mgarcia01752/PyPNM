# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union

from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.modulation_profile.service import CmDsOfdmModProfileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class ModulationProfileRouter(PnmFastApiRouter):
    """
    Concrete implementation of PnmFastApiRouter for handling Modulation Profile-related requests.
    """
    def __init__(self):
        
        measurement_description = """
**Retrieve DOCSIS 3.1 Downstream OFDM Modulation Profile**

Captures the raw modulation profile from a DOCSIS 3.1 cable modem’s downstream OFDM channel.
Includes metadata about profile ID, subcarrier spacing, and modulation schemes (e.g., QAM-16 to QAM-4096)
assigned to subcarrier groups.

⚠️ Note: This output reflects a direct conversion from the modem’s internal profile encoding.
Additional decoding is required for full per-subcarrier modulation mapping or bit-loading visualizations.

📄 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/modulation-profile.md#get-measurement)
"""
  
        analysis_description = """
**Analyze Downstream OFDM Modulation Profile**

Performs post-processing of the downstream OFDM modulation profile,
providing a per-subcarrier breakdown of modulation types and frequency layout.

Includes:
- Subcarrier modulation type (e.g., QAM-256, QAM-4096)
- Subcarrier frequency map
- Shannon limit estimates based on modulation order

📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/modulation-profile.md#get-analysis)
"""
        measurement_statistics_description = """"""
    
        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM Modulation Profile"],
            base_endpoint="/modulationProfile",
            set_measurement_description = measurement_description,
            set_analysis_description = analysis_description,
            set_measurement_statistics_description=measurement_statistics_description)
        self.logger = logging.getLogger("ModulationProfileRouter")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:

        self.logger.info(f"Retrieving Modulation Profile measurement for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )         
  
        service: CmDsOfdmModProfileService = CmDsOfdmModProfileService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return PnmMeasurementResponse(mac_address=request.mac_address,
                                          message="Unable to complete Modulation Profile measurement.",
                                          status=msg_rsp.status, measurement={})

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
    
        return PnmMeasurementResponse(mac_address=request.mac_address,
                                      status=msg_rsp.status, 
                                      measurement=msg_rsp.payload) # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, SnmpResponse]:
        """
        Retrieve and analyze the downstream OFDM modulation profile from the cable modem.

        This analysis includes:
        - Per-subcarrier modulation type (e.g., QAM-16, QAM-4096)
        - Frequency mapping
        - Shannon limit estimation per subcarrier

        Supports output types:
        - 0: JSON with modulation and Shannon analysis
        - 1: XLSX formatted report for offline visualization

        📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/modulation-profile.md#get-analysis)

        """
        self.logger.info(f"Generating Modulation Profile plot type: {request.analysis.type} for MAC {request.mac_address}")
        
        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )         

        service: CmDsOfdmModProfileService = CmDsOfdmModProfileService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
                
        return PnmAnalysisResponse(mac_address=request.mac_address,
                                      status=ServiceStatusCode.SUCCESS,
                                      data=analysis.get_results()) 

    async def get_measurement_statistics_logic(self, request: PnmRequest) -> Union[SnmpResponse]:
        """
        """
        self.logger.info(f"Fetching OFDMA Pre-Equalization Measurement Statistics for MAC: {request.mac_address}")

        cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))
        
        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                        validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status, message=msg)  

        return SnmpResponse(
            mac_address=str(request.mac_address),
            status=ServiceStatusCode.SUCCESS,
            message="Measurement Statistics for OFDMA Pre-Equalization",
            results={})

# Required for dynamic auto-registration
router = ModulationProfileRouter().router
