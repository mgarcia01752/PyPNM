# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import List, Union, cast
from fastapi import APIRouter, HTTPException
from pypnm.api.routes.basic.fec_summary_analysis_rpt import FecSummaryAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.histogram.router import PnmAnalysisResponse
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.schemas import (
    PnmFecSummaryAnalysisRequest, PnmFecSummaryRequest, PnmFecSummaryResponse)
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.service import CmDsOfdmFecSummaryService
from pypnm.api.routes.docs.pnm.files.service import FileType, PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import FecSummaryType
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class FecSummaryRouter:
    """
    Concrete implementation of PnmFastApiRouter for handling Fec Summary-related requests.
    """
    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags:List[str] = ["PNM Operations - Downstream OFDM FEC Summary"]
        base_endpoint = "/fecSummary"

        self.base_endpoint = base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"FecSummaryRouter.{self.base_endpoint}")

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", 
                          response_model=Union[PnmFecSummaryResponse, SnmpResponse])
        async def get_measurement(request: PnmFecSummaryRequest):
            """
            **OFDM FEC Summary Statistics for Downstream Channels**

            This endpoint fetches FEC summary counters for each active OFDM downstream profile,
            including corrected and uncorrectable codewords over a defined interval.

            [API Guide - OFDM FEC Summary Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/fec-summary.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving FEC Summary for MAC: {mac}, IP: {ip}, FEC Summary Type: {request.fec_summary_type}")            
            try:

                cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

                status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg)               
            
                fec_type = FecSummaryType.from_value(int(request.fec_summary_type))
                service = CmDsOfdmFecSummaryService(cable_modem=cm, fec_summary_type=fec_type)
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(f"[getMeasurement] FEC Summary failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="FEC summary SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                return PnmFecSummaryResponse(
                    mac_address=mac,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict())

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {mac}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", 
                          response_model=Union[PnmFecSummaryResponse, SnmpResponse])
        async def get_analysis(request: PnmFecSummaryAnalysisRequest):
            """
            **OFDM FEC Summary Statistics for Downstream Channels**

            This endpoint fetches FEC summary counters for each active OFDM downstream profile,
            including corrected and uncorrectable codewords over a defined interval.

            [API Guide - OFDM FEC Summary Statistics](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/fec-summary.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving Downstream OFDM FEC Summary for MAC: {mac}, IP: {ip}")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
            
            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)  

            fec_type = FecSummaryType.from_value(int(request.fec_summary_type))
            service = CmDsOfdmFecSummaryService(cable_modem=cm, fec_summary_type=fec_type)
            msg_rsp: MessageResponse = await service.set_and_go()

            if msg_rsp.status != ServiceStatusCode.SUCCESS:
                self.logger.error(f"[getMeasurement]  failed with status: {msg_rsp.status.name}")
                raise HTTPException(status_code=500, detail="Downstream Histogram SNMP execution failed")

            cps = CommonProcessService(msg_rsp)
            msg_rsp = cps.process()
            analysis = Analysis(AnalysisType.BASIC, msg_rsp)
            
            if request.output.type == FileType.JSON.value:
                return PnmAnalysisResponse(mac_address=mac, 
                                           status=ServiceStatusCode.SUCCESS, 
                                           data=analysis.get_results())

            elif request.output.type == FileType.ARCHIVE.value:
                
                analysis_rpt = FecSummaryAnalysisReport(analysis)
                rpt:Path = cast(Path, analysis_rpt.build_report())

                return PnmFileService().get_file(FileType.ARCHIVE,rpt.name)

            else:
                return PnmAnalysisResponse(
                    mac_address=mac,
                    status=ServiceStatusCode.INVALID_OUTPUT_TYPE, 
                    data={})

# Required for dynamic auto-registration
router = FecSummaryRouter().router
