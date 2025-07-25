# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union

from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.chan_est_coeff.service import CmDsOfdmChanEstCoefService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class ChannelEstimationCoefficentRouter(PnmFastApiRouter):
    """
    Concrete implementation of PnmFastApiRouter for handling Channel-Estimation-Coefficent related requests.
    """
    def __init__(self):
        
        measurement_description = """
**Capture Downstream OFDM Channel Estimation Coefficients**

This API retrieves complex per-subcarrier channel estimation taps from a DOCSIS 3.1 cable modem.
These coefficients represent the channel’s frequency response and are vital for diagnostics and impulse
response analysis.

Includes:
- Real/Imaginary values for each subcarrier
- Channel ID and frequency metadata
- Raw coefficient buffer size and count

📘 [API Guide – Get Measurement](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-measurement)
"""

        analysis_description = """
**Analyze Downstream OFDM Channel Estimation Data**

Performs signal-domain analysis of DOCSIS 3.1 channel estimation coefficients. Output includes:
- Frequency-mapped magnitude and group delay
- Complex tap representation
- Statistical breakdown (mean, skewness, crest factor, etc.)

⚠️ Due to payload size, it is recommended to use Postman or CURL instead of Swagger UI.

📘 [API Guide – Get Analysis](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-analysis)
"""

        measurement_statistics_description = """
**Summarize Downstream OFDM Channel Estimation Coefficient Statistics**

This endpoint returns high-level channel estimation metrics per downstream OFDM channel, including:
- Amplitude ripple (RMS, peak-to-peak)
- Group delay ripple (RMS, peak-to-peak)
- Amplitude slope, group delay slope, and mean values
- Measurement status and associated binary filename

📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-measurement-statistics)
"""

        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM Channel Estimation"],
            base_endpoint="/channelEstCoeff",
            set_measurement_description = measurement_description,
            set_analysis_description = analysis_description,
            set_measurement_statistics_description=measurement_statistics_description)
        self.logger = logging.getLogger("ChannelEstimationCoefficentRouter")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
        """
        Implement Channel-Estimation-Coefficent measurement retrieval logic.
        """    
        self.logger.info(f"Retrieving Channel-Estimation-Coefficent measurement for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status, message=msg)    
        
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
        self.logger.info(f"Generating Channel-Estimation-Coefficent Analysis Type: {request.analysis.type} for MAC {request.mac_address}")
        
        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status, message=msg) 
        
        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
                
        return PnmAnalysisResponse(mac_address=request.mac_address,
                                      status=ServiceStatusCode.SUCCESS,
                                      data=analysis.get_results()) 

    async def get_measurement_statistics_logic(self, request: PnmRequest) -> Union[SnmpResponse]:
        """
        Retrieves OFDM Channel Estimation Coefficient measurement statistics for a DOCSIS 3.1 cable modem.

        This includes values such as amplitude ripple (RMS & peak-to-peak), group delay ripple,
        group delay slope, and related channel estimation metrics across all downstream OFDM channels.
        """
        self.logger.info(f"Fetching OFDM Channel Estimation Coefficient Statistics for MAC: {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status, message=msg) 

        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        service_measure_stat = await service.get_pnm_measurement_statistics()

        return SnmpResponse(
            mac_address=str(request.mac_address),
            status=ServiceStatusCode.SUCCESS,
            message="Measurement Statistics for OFDM Channel Estimation Coefficients",
            results=service_measure_stat)

# ✅ Required for dynamic auto-registration
router = ChannelEstimationCoefficentRouter().router
