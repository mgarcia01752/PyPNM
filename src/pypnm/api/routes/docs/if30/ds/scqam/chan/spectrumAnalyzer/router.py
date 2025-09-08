# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Union
from fastapi import APIRouter
from fastapi.responses import FileResponse

from pypnm.api.routes.basic.scqam_spec_analyzer_rpt import ScQamSpecAnalyzerAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.analysis.multi_analysis import MultiAnalysis
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if30.ds.scqam.chan.spectrumAnalyzer.schemas import (
    ScQamSpecAnaAnalysisRequest, ScQamSpecAnaAnalysisResponse)
from pypnm.api.routes.docs.if30.ds.scqam.chan.spectrumAnalyzer.service import DsScQamChannelSpectrumAnalyzer
from pypnm.api.routes.docs.pnm.files.service import FileType, PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class DsScQamChannelSpectrumAnalyzerRouter:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if30/ds/scqam/chan/spectrumAnalyzer",
            tags=["DOCSIS 3.0 Downstream SC-QAM Channel", "Spectrum Analyzer"],
        )
        self._add_routes()

    def _add_routes(self):

        @self.router.post(
            "/analysis",
            response_model=ScQamSpecAnaAnalysisResponse,
            # ✅ Document that this endpoint may also return a ZIP file
            responses={
                200: {
                    "description": "Analysis JSON or ZIP archive.",
                    "content": {
                        "application/json": {},
                        "application/zip": {
                            "schema": {"type": "string", "format": "binary"}
                        }
                    },
                }
            },
        )
        async def get_scqam_ds_channels_analysis(request: ScQamSpecAnaAnalysisRequest,) -> Union[ScQamSpecAnaAnalysisResponse, FileResponse]:
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            cm = CableModem(MacAddress(mac), Inet(ip))
            multi_analysis = MultiAnalysis()

            # Prefer parameterized logging
            self.logger.info(
                "DOCSIS 3.0 SC-QAM downstream spectrum capture for MAC %s, IP %s",
                mac, ip)

            status, msg = await CableModemServicePreCheck(
                                cable_modem=cm,
                                validate_scqam_exist=True,
                                validate_pnm_ready_status=True
                            ).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return ScQamSpecAnaAnalysisResponse(
                    mac_address=mac,
                    status=status,
                    message=msg,
                    data={}
                )

            service = DsScQamChannelSpectrumAnalyzer(cm)
            msg_responses = await service.start()

            for msg_rsp in msg_responses:
                cps_msg_rsp = CommonProcessService(msg_rsp).process()
                analysis = Analysis(AnalysisType.BASIC, cps_msg_rsp)
                multi_analysis.add(analysis)

            analyzer_rpt = ScQamSpecAnalyzerAnalysisReport(multi_analysis)
            analyzer_rpt.build_report()

            if request.output.type == FileType.JSON.value:
                return ScQamSpecAnaAnalysisResponse(
                    mac_address=mac,
                    status=ServiceStatusCode.SUCCESS,
                    data=analyzer_rpt.to_dict())

            if request.output.type == FileType.ARCHIVE.value:
                return PnmFileService().get_file(FileType.ARCHIVE, analyzer_rpt.get_archive())

            # Unsupported output type -> explicit failure
            return ScQamSpecAnaAnalysisResponse(
                mac_address=mac,
                status=ServiceStatusCode.FAILURE,
                message=f"Unsupported output type: {request.output.type}",
                data={}
            )

# Required for dynamic auto-registration
router = DsScQamChannelSpectrumAnalyzerRouter().router
