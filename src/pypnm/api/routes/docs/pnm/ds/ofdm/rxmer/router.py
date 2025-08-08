# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import Union
from fastapi import HTTPException
from fastapi.responses import FileResponse

from pypnm.api.routes.basic.rxmer_analysis_report import RxMerAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.analysis.report.excel.basic.rxmer_excel_basic import RxMerExcelBasic
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.rxmer.service import CmDsOfdmRxMerService
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class RxMerRouter(PnmFastApiRouter):
    """
    Concrete implementation of PnmFastApiRouter for handling RxMER-related requests.
    """
    def __init__(self):
        
        measurement_description = """
**Capture Downstream OFDM RxMER Per-Subcarrier Values**

This endpoint retrieves per-subcarrier RxMER (Receive Modulation Error Ratio) data
from a DOCSIS cable modem. The response includes:

- MER values in dB
- Channel ID and zero subcarrier frequency
- Subcarrier spacing and data length
- Shannon-derived bits per symbol and modulation estimation
- Statistical metrics: mean, standard deviation, skewness, peak-to-peak, etc.

Each entry corresponds to an active OFDM downstream channel found on the device.

[API Guide - Capture Downstream OFDM RxMER Per-Subcarrier Values](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/rxmer.md#get-measurement)
"""

        analysis_description = """
**Analyze Downstream OFDM RxMER Per-Subcarrier Values**

This endpoint performs post-processing on RxMER measurement data retrieved from the cable modem.
It extracts subcarrier-level details such as:
- Per-carrier MER magnitude (in dB)
- Frequency mapping for each subcarrier
- Carrier status classification (Exclusion, Clipped, Normal)
- Shannon-based bits-per-symbol and modulation support

Supports multiple output types (`JSON`, `XLSX`) and future advanced analysis modes.

[API Guide - Analyze Downstream OFDM RxMER Per-Subcarrier Values](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/rxmer.md#get-analysis)
"""

        measurement_statistics_description = """
**Summarize Downstream OFDM RxMER Measurement Statistics**

This endpoint retrieves statistical summaries of RxMER (Receive Modulation Error Ratio) 
measurements for each downstream OFDM channel on a DOCSIS cable modem. It does not 
retrieve raw per-subcarrier values, but instead provides high-level metrics including:

- Mean and standard deviation of RxMER
- Threshold values and exceeded frequency markers
- Measurement status codes
- Associated binary filename used for full RxMER capture

Useful for quick health checks, threshold monitoring, and triggering further diagnostics.

[API Guide - Downstream OFDM RxMER Measurement Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/rxmer.md#get-measurement-statistics)
"""

        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM RxMER"],
            base_endpoint="/rxMer",
            set_measurement_description=measurement_description,
            set_analysis_description=analysis_description,
            set_measurement_statistics_description = measurement_statistics_description)
        self.logger = logging.getLogger("RxMerRouter")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address   
        self.logger.info(f"Starting RxMER measurement for MAC: {mac}, IP: {ip}")

        cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
        
        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg)  
        
        service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm)
        msg_rsp: MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            msg = 'Unable to complete RxMER measurement.'
            return SnmpResponse(mac_address=mac, message=msg, status=msg_rsp.status)

        cps = CommonProcessService(msg_rsp)
        msg_rsp: MessageResponse = cps.process()
    
        return PnmMeasurementResponse(
            mac_address=mac, status=msg_rsp.status, measurement=msg_rsp.payload)  # type: ignore

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, FileResponse, SnmpResponse]:
        
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Generating RxMER Analysis: {request.analysis.type} for MAC: {request.cable_modem.mac_address}")

        cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
        
        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac), status=status, message=msg)  

        service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm)
        msg_rsp: MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp: MessageResponse = cps.process()

        analysis = Analysis(AnalysisType.BASIC, msg_rsp)
        results = analysis.get_results() or {}  # Ensure it's a valid dictionary
        
        if request.output.type == FileType.JSON.value:
            return PnmAnalysisResponse(
                mac_address=mac, status=ServiceStatusCode.SUCCESS, data=results)

        elif request.output.type == FileType.XLSX.value:
            xlsx_dir = SystemConfigSettings.xlsx_dir
            
            # Check if the XLSX directory exists
            if not Path(xlsx_dir).exists():
                self.logger.error(f"XLSX directory not found: {xlsx_dir}")
                raise HTTPException(status_code=500, detail="XLSX directory not found.")
            
            excel = RxMerExcelBasic(analysis, Path(xlsx_dir))
            excel.build()
            self.logger.info(f'Excel Filename: {excel.get_filename()}')

            # Ensure the file was created successfully
            if not Path(xlsx_dir, excel.get_filename()).exists():
                self.logger.error(f"Failed to create Excel file: {excel.get_filename()}")
                raise HTTPException(status_code=500, detail="Failed to create Excel file.")

            return PnmFileService().get_file(FileType.XLSX, excel.get_filename())

        elif request.output.type == FileType.ARCHIVE.value:
            
            analysis_rpt = RxMerAnalysisReport(analysis)

            # fname = ""
            # return PnmFileService().get_file(FileType.ARCHIVE,fname)
            msg = 'Test Response'
            return SnmpResponse(mac_address=str(mac), status=ServiceStatusCode.SUCCESS, message=msg)
        
        else:
            return PnmAnalysisResponse(
                mac_address=request.cable_modem.mac_address,
                status=ServiceStatusCode.INVALID_OUTPUT_TYPE, data=None )

    async def get_measurement_statistics_logic(self, request: SnmpRequest) -> SnmpResponse:
        mac = request.cable_modem.mac_address
        ip = request.cable_modem.ip_address
        self.logger.info(f"Fetching RxMER Measurement Statistics for MAC: {mac}, IP: {ip}")

        cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
        
        status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(mac_address=str(mac),status=status, message=msg)  

        service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm)
        service_measure_stat = await service.get_pnm_measurement_statistics()

        return SnmpResponse(
            mac_address=str(mac),
            status=ServiceStatusCode.SUCCESS,
            message="Measurement Statistics for RxMER",
            results=service_measure_stat)

# Required for dynamic auto-registration
router = RxMerRouter().router
