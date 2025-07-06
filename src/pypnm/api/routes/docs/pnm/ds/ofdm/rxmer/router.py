# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import Union

from fastapi import HTTPException
from fastapi.responses import FileResponse

from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.analysis.report.excel.basic.rxmer_excel_basic import RxMerExcelBasic
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
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

📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/rxmer.md)
"""

        analysis_description = """ 
"""
        
        super().__init__(
            prefix="/docs/pnm/ds/ofdm",
            tags=["PNM Operations - Downstream OFDM RxMER"],
            base_endpoint="/rxMer",
            set_measurement_description=measurement_description,
            set_analysis_description=analysis_description)
        self.logger = logging.getLogger("RxMerRouter")

    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
   
        self.logger.info(f"Retrieving RxMER measurement for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )   
        
        service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm)
        msg_rsp: MessageResponse = await service.set_and_go()

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            return SnmpResponse(
                mac_address=request.mac_address,
                message="Unable to complete RxMER measurement.",
                status=msg_rsp.status
            )

        cps = CommonProcessService(msg_rsp)
        msg_rsp: MessageResponse = cps.process()
    
        return PnmMeasurementResponse(
            mac_address=request.mac_address,
            status=msg_rsp.status, 
            measurement=msg_rsp.payload  # type: ignore
        )

    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, FileResponse, SnmpResponse]:
        """
        Implement RxMER plotting data retrieval.
        """
        self.logger.info(f"Generating RxMER plot type: {request.analysis.type} for MAC {request.mac_address}")

        cm: CableModem = CableModem(MacAddress(request.mac_address), Inet(request.ip_address))

        status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            self.logger.error(msg)
            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=status,
                message=msg
            )

        service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm)
        msg_rsp: MessageResponse = await service.set_and_go()

        cps = CommonProcessService(msg_rsp)
        msg_rsp: MessageResponse = cps.process()

        analysis = Analysis(AnalysisType.BASIC, msg_rsp)

        results = analysis.get_results() or {}  # Ensure it's a valid dictionary
        
        if request.output.type == FileType.JSON.value:
            return PnmAnalysisResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.SUCCESS,
                data=results
            )

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

        else:
            return PnmAnalysisResponse(
                mac_address=request.mac_address,
                status=ServiceStatusCode.INVALID_OUTPUT_TYPE,
                data=None
            )

# ✅ Required for dynamic auto-registration
router = RxMerRouter().router
