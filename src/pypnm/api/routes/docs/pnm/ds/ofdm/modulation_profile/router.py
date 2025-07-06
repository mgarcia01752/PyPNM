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
        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM Modulation Profile"],
            base_endpoint="/modulationProfile")
        self.logger = logging.getLogger("ModulationProfileRouter")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
        """
        Retrieve DOCSIS 3.1 Downstream OFDM Modulation Profile

        This API captures and returns the modulation profile data for downstream OFDM channels 
        from a DOCSIS 3.1 cable modem. It reports profile metadata including modulation schemes 
        (e.g., QAM-16, QAM-4096) used per subcarrier group, along with carrier frequency layout 
        and subcarrier spacing.

        ⚠️ Note: This is a raw conversion of modulation profile entries. Further processing is 
        required to generate full per-subcarrier bit-loading visualizations or modulation maps.

        - **POST**: `/docs/pnm/ds/ofdm/modulationProfile/getMeasurement`
        - 📄 [Modulation Profile Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/modulation-profile.md)

        Returns:
            - PnmMeasurementResponse: Measurement data containing one or more OFDM channel modulation profiles.
            - SnmpResponse: SNMP error or fallback message.
        """ 
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
        Implement Modulation Profile plotting data retrieval.
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


# Required for dynamic auto-registration
router = ModulationProfileRouter().router
