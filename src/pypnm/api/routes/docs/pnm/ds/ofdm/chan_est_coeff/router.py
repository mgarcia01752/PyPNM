
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import Union, cast

from fastapi.responses import FileResponse

from pypnm.api.routes.basic.channel_estimation_analysis_rpt import ChanEstimationReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.chan_est_coeff.service import CmDsOfdmChanEstCoefService
from pypnm.api.routes.docs.pnm.files.service import FileType, PnmFileService
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

[API Guide - Downstream OFDM Channel Estimation Coefficients](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-measurement)
"""

        analysis_description = """
**Analyze Downstream OFDM Channel Estimation Data**

Performs signal-domain analysis of DOCSIS 3.1 channel estimation coefficients. Output includes:
- Frequency-mapped magnitude and group delay
- Complex tap representation
- Statistical breakdown (mean, skewness, crest factor, etc.)

⚠️ Due to payload size, it is recommended to use Postman or CURL instead of Swagger UI.

[API Guide - Downstream OFDM Channel Estimation Data](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-analysis)
"""

        measurement_statistics_description = """
**Summarize Downstream OFDM Channel Estimation Coefficient Statistics**

This endpoint returns high-level channel estimation metrics per downstream OFDM channel, including:
- Amplitude ripple (RMS, peak-to-peak)
- Group delay ripple (RMS, peak-to-peak)
- Amplitude slope, group delay slope, and mean values
- Measurement status and associated binary filename

[API Guide - OFDM Channel Estimation Coefficient Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/channel-estimation.md#get-measurement-statistics)
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
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Retrieving Channel-Estimation-Coefficent for MAC: {mac}, IP: {ip}")

        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg)    
        
        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return PnmMeasurementResponse(mac_address=mac,
                                          message="Unable to complete Channel-Estimation-Coefficent measurement.",
                                          status=msg_rsp.status, measurement={})

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
    
        return PnmMeasurementResponse(mac_address=mac,status=msg_rsp.status, 
                                      measurement=msg_rsp.payload) # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, FileResponse, SnmpResponse]:

        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Retrieving Channel-Estimation-Coefficent Analysis for MAC: {mac}, IP: {ip}, Analysis Type: {request.analysis.type}")
        
        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg) 
        
        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        msg_rsp:MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp:MessageResponse = cps.process()
        
        analysis = Analysis(AnalysisType.BASIC, msg_rsp)

        if request.output.type == FileType.JSON.value:
            return PnmAnalysisResponse(
                mac_address=mac, 
                status=ServiceStatusCode.SUCCESS, data=analysis.get_results())

        elif request.output.type == FileType.ARCHIVE.value:
            
            analysis_rpt = ChanEstimationReport(analysis)
            rpt:Path = cast(Path, analysis_rpt.build_report())

            return PnmFileService().get_file(FileType.ARCHIVE,rpt.name)

        else:
            return PnmAnalysisResponse(
                mac_address=mac,
                status=ServiceStatusCode.INVALID_OUTPUT_TYPE, data={})

    async def get_measurement_statistics_logic(self, request: SnmpRequest) -> SnmpResponse:
        """
        Retrieves OFDM Channel Estimation Coefficient measurement statistics for a DOCSIS 3.1 cable modem.

        This includes values such as amplitude ripple (RMS & peak-to-peak), group delay ripple,
        group delay slope, and related channel estimation metrics across all downstream OFDM channels.
        """
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Retrieving OFDM Channel Estimation Coefficient Statistics for MAC: {mac}, IP: {ip}")        

        cm: CableModem = CableModem(MacAddress(mac), Inet(ip))

        status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                      validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg) 

        service: CmDsOfdmChanEstCoefService = CmDsOfdmChanEstCoefService(cm)
        service_measure_stat = await service.get_pnm_measurement_statistics()

        return SnmpResponse(
            mac_address=str(mac),
            status=ServiceStatusCode.SUCCESS,
            message="Measurement Statistics for OFDM Channel Estimation Coefficients",
            results=service_measure_stat)

# Required for dynamic auto-registration
router = ChannelEstimationCoefficentRouter().router
