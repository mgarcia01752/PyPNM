# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Union
from fastapi import APIRouter
from fastapi.responses import FileResponse

from pypnm.api.routes.basic.ofdm_spec_analyzer_rpt import OfdmSpecAnalyzerAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.analysis.multi_analysis import MultiAnalysis
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if31.ds.ofdm.chan.spectrumAnalyzer.schemas import OfdmSpecAnaAnalysisRequest, OfdmSpecAnaAnalysisResponse
from pypnm.api.routes.docs.if31.ds.ofdm.chan.spectrumAnalyzer.service import DsOfdmChannelSpectrumAnalyzer
from pypnm.api.routes.docs.pnm.files.service import FileType, PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class DsOfdmChannelSpectrumAnalyzerRouter:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if31/ds/ofdm/chan/spectrumAnalyzer",
            tags=["DOCSIS 3.1 Downstream OFDM Channel", "Spectrum Analyzer"],
        )
        self._add_routes()

    def _add_routes(self):

        @self.router.post(
            "/analysis",
            response_model=OfdmSpecAnaAnalysisResponse,
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
        async def get_ofdm_ds_channels_analysis(request: OfdmSpecAnaAnalysisRequest,) -> Union[OfdmSpecAnaAnalysisResponse, FileResponse]:
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            cm = CableModem(MacAddress(mac), Inet(ip))
            multi_analysis = MultiAnalysis()

            # Prefer parameterized logging
            self.logger.info("DOCSIS 3.0 SC-QAM downstream spectrum capture for MAC %s, IP %s",mac, ip)

            status, msg = await CableModemServicePreCheck(
                                cable_modem=cm,
                                validate_ofdm_exist=True,
                                validate_pnm_ready_status=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return OfdmSpecAnaAnalysisResponse(
                    mac_address=mac,
                    status=status,
                    message=msg,
                    data={}
                )

            service = DsOfdmChannelSpectrumAnalyzer(cm)
            msg_responses = await service.start()

            for msg_rsp in msg_responses:
                cps_msg_rsp = CommonProcessService(msg_rsp).process()
                analysis = Analysis(AnalysisType.BASIC, cps_msg_rsp)
                multi_analysis.add(analysis)

            analyzer_rpt = OfdmSpecAnalyzerAnalysisReport(multi_analysis)
            analyzer_rpt.build_report()

            if request.output.type == FileType.JSON.value:
                return OfdmSpecAnaAnalysisResponse(
                    mac_address=mac,
                    status=ServiceStatusCode.SUCCESS,
                    data=analyzer_rpt.to_dict())

            if request.output.type == FileType.ARCHIVE.value:
                return PnmFileService().get_file(FileType.ARCHIVE, analyzer_rpt.get_archive())

            # Unsupported output type -> explicit failure
            return OfdmSpecAnaAnalysisResponse(
                mac_address=mac,
                status=ServiceStatusCode.FAILURE,
                message=f"Unsupported output type: {request.output.type}",
                data={}
            )

# Required for dynamic auto-registration
router = DsOfdmChannelSpectrumAnalyzerRouter().router
