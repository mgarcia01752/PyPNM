# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union

from api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmMeasurementResponse,
    PnmAnalysisRequest,
    PnmAnalysisResponse,
    PnmRequest,
)
from api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from api.routes.common.extended.common_messaging_service import MessageResponse
from api.routes.common.extended.common_process_service import CommonProcessService
from api.routes.common.service.status_codes import ServiceStatusCode
from api.routes.docs.pnm.ds.ofdm.chan_est_coeff.service import CmDsOfdmChanEstCoefService
from docsis.cable_modem import CableModem
from lib.inet import Inet
from lib.mac_address import MacAddress

class ChannelEstimationCoefficentRouter(PnmFastApiRouter):
    """
    Concrete implementation of PnmFastApiRouter for handling Channel-Estimation-Coefficent related requests.
    """
    def __init__(self):
        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM Channel Estimation"],
            base_endpoint="/channelEstCoeff")
        self.logger = logging.getLogger("ChannelEstCoeff")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
        """
        Implement Channel-Estimation-Coefficent measurement retrieval logic.
        """    
        self.logger.info(f"Retrieving Channel-Estimation-Coefficent measurement for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )    
        
        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return PnmMeasurementResponse(mac_address=request.mac_address,
                                          message="Unable to complete Channel-Estimation-Coefficent measurement.",
                                          status=msg_rsp.status, measurement={})

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
    
        return PnmMeasurementResponse(mac_address=request.mac_address,
                                      status=msg_rsp.status, 
                                      measurement=msg_rsp.payload) # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> PnmAnalysisResponse:
        """
        Implement RxMER plotting data retrieval.
        """
        self.logger.info(f"Generating Channel-Estimation-Coefficent Analysis Type: {request.analysis.analysis_type} for MAC {request.mac_address}")
        
        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))
        
        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
                
        return PnmAnalysisResponse(mac_address=request.mac_address,
                                      status=ServiceStatusCode.SUCCESS,
                                      data=analysis.get_results()) 


# ✅ Required for dynamic auto-registration
router = ChannelEstimationCoefficentRouter().router
