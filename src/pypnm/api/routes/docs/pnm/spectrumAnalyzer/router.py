from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Any, Dict, List, Tuple, cast

from fastapi import APIRouter

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisRptMatplotConfig
from pypnm.api.routes.basic.ofdm_spec_analyzer_rpt import OfdmSpecAnalyzerAnalysisReport
from pypnm.api.routes.basic.spec_analyzer_analysis_rpt import SpectrumAnalyzerReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.analysis.model.process import AnalysisProcessParameters
from pypnm.api.routes.common.classes.analysis.multi_analysis import MultiAnalysis
from pypnm.api.routes.common.classes.common_endpoint_classes.common.enum import OutputType
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import (
    OfdmSpecAnaAnalysisRequest,
    OfdmSpecAnaAnalysisResponse,
    SingleCaptureSpectrumAnalyzer,
)
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.service import CmSpectrumAnalysisService, DsOfdmChannelSpectrumAnalyzer
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.pnm.DocsIf3CmSpectrumAnalysisEntry import DocsIf3CmSpectrumAnalysisEntry
from pypnm.lib.dict_utils import DictUtils
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import ChannelId, InetAddressStr, MacAddressStr, Path


class SpectrumAnalyzerRouter:
    def __init__(self):
        prefix = "/docs/pnm/ds"
        self.base_endpoint = "/spectrumAnalyzer"
        self.router = APIRouter(prefix=prefix, tags=["PNM Operations - Spectrum Analyzer"])
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.__routes()

    def __routes(self) -> None:
        @self.router.post(
            f"{self.base_endpoint}/getCapture",
            summary="Get Spectrum Analyzer Capture",
            responses=FAST_API_RESPONSE,
        )
        async def get_capture(request: SingleCaptureSpectrumAnalyzer):
            """
            Perform Spectrum Analyzer Capture And Return Analysis Results.

            This endpoint triggers a spectrum capture on the requested cable modem using the
            provided capture parameters. The measurement response is then processed through
            the common analysis pipeline and returned as either:

            - A JSON analysis payload containing decoded amplitude data and summary metrics.
            - An archive file containing plots and related report artifacts (ZIP).

            The cable modem must be PNM-ready and the capture parameters must respect the
            diplexer configuration and platform constraints (DOCSIS 3.x and DOCSIS 4.0 FDD).

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/single/spectrum-analyzer.md)
            """
            mac: MacAddressStr = request.cable_modem.mac_address
            ip: InetAddressStr = request.cable_modem.ip_address

            self.logger.info(
                f"Starting Spectrum Analyzer capture for MAC: {mac}, IP: {ip}, "
                f"Output Type: {request.analysis.output.type}"
            )

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm,
                validate_pnm_ready_status=True,
            ).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=mac, status=status, message=msg)

            service = CmSpectrumAnalysisService(
                cable_modem        = cm,
                capture_parameters = request.capture_parameters,
            )

            msg_rsp: MessageResponse = await service.set_and_go()

            if msg_rsp.status != ServiceStatusCode.SUCCESS:
                err = "Unable to complete Spectrum Analyzer capture."
                self.logger.error(f"{err} Status: {msg_rsp.status.name}")
                return SnmpResponse(mac_address=mac, status=msg_rsp.status, message=err)

            measurement_stats: List[DocsIf3CmSpectrumAnalysisEntry] = cast(
                List[DocsIf3CmSpectrumAnalysisEntry],
                await service.getPnmMeasurementStatistics(),
            )

            cps = CommonProcessService(msg_rsp)
            msg_rsp = cps.process()

            analysis = Analysis(
                AnalysisType.BASIC,
                msg_rsp,
                skip_automatic_process=True,
            )

            analysis.process(cast(AnalysisProcessParameters, request.analysis.spectrum_analysis))

            if request.analysis.output.type == OutputType.JSON:
                payload: Dict[str, Any] = cast(Dict[str, Any], analysis.get_results())
                DictUtils.pop_keys_recursive(payload, ["pnm_header", "mac_address", "channel_id"])

                primative = msg_rsp.payload_to_dict("primative")
                DictUtils.pop_keys_recursive(
                    primative,
                    ["device_details", "channel_id", "amplitude_bin_segments_float"],
                )
                payload.update(primative)
                payload.update(
                    DictUtils.models_to_nested_dict(
                        measurement_stats,
                        "measurement_stats",
                    )
                )

                return PnmAnalysisResponse(
                    mac_address = mac,
                    status      = ServiceStatusCode.SUCCESS,
                    data        = payload,
                )

            if request.analysis.output.type == OutputType.ARCHIVE:
                theme       = request.analysis.plot.ui.theme
                plot_config = AnalysisRptMatplotConfig(theme=theme)
                analysis_rpt = SpectrumAnalyzerReport(analysis, plot_config)
                rpt: Path = cast(Path, analysis_rpt.build_report())
                return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)

            return PnmAnalysisResponse(
                mac_address = mac,
                status      = ServiceStatusCode.INVALID_OUTPUT_TYPE,
                data        = {},
            )

        @self.router.post(
            f"{self.base_endpoint}/getCapture/ofdm",
            summary="Get OFDM Spectrum Analyzer Capture",
            responses=FAST_API_RESPONSE,
        )
        async def get_ofdm_ds_channels_analysis(request: OfdmSpecAnaAnalysisRequest):
            """
            Perform OFDM Downstream Spectrum Capture Across All DS OFDM Channels.

            This endpoint triggers spectrum capture operations on each DOCSIS 3.1 OFDM
            downstream channel of the requested cable modem. Each per-channel response is
            processed through the common analysis pipeline, aggregated into a multi-analysis
            structure, and then returned as either JSON or an archive.

            The cable modem must support OFDM downstream channels and be PNM-ready, and
            the spectrum capture parameters must be valid for the underlying platform and
            diplexer configuration.

            [API Guide]()

            """
            mac: MacAddressStr = request.cable_modem.mac_address
            ip: InetAddressStr = request.cable_modem.ip_address

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
            multi_analysis = MultiAnalysis()

            self.logger.info("DOCSIS 3.1 OFDM downstream spectrum capture for MAC %s, IP %s",mac, ip,)

            status, msg = await CableModemServicePreCheck(cable_modem=cm,
                                                          validate_ofdm_exist=True,
                                                          validate_pnm_ready_status=True,).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return OfdmSpecAnaAnalysisResponse(
                    mac_address = mac,
                    status      = status,
                    message     = msg,
                    data        = {},
                )

            service = DsOfdmChannelSpectrumAnalyzer(
                cm, number_of_averages=request.capture_parameters.number_of_averages,)

            msg_responses: List[Tuple[ChannelId, MessageResponse]] = await service.start()

            measurement_stats: List[DocsIf3CmSpectrumAnalysisEntry] = cast(
                List[DocsIf3CmSpectrumAnalysisEntry],
                await service.getPnmMeasurementStatistics(),)

            primative:Dict[str,Dict[Any,Any]] = {'primative':{}}
            for idx, (chan_id, msg_rsp) in enumerate(msg_responses):
                cps_msg_rsp = CommonProcessService(msg_rsp).process()
                
                analysis = Analysis(AnalysisType.BASIC, cps_msg_rsp, skip_automatic_process=True,)
                analysis.process(cast(AnalysisProcessParameters, request.analysis.spectrum_analysis))
                multi_analysis.add(chan_id, analysis)
                
                primative_entry = cps_msg_rsp.payload_to_dict(idx)
                primative['primative'].update(primative_entry)

            analyzer_rpt = OfdmSpecAnalyzerAnalysisReport(multi_analysis)
            analyzer_rpt.build_report()

            if request.analysis.output.type == OutputType.JSON:
                analyzer_rpt_dict = analyzer_rpt.to_dict()
                analyzer_rpt_dict.update(primative)
                analyzer_rpt_dict.update(DictUtils.models_to_nested_dict(measurement_stats, "measurement_stats",))

                return OfdmSpecAnaAnalysisResponse(
                    mac_address = mac,
                    status      = ServiceStatusCode.SUCCESS,
                    data        = analyzer_rpt_dict,)

            if request.analysis.output.type == OutputType.ARCHIVE:
                return PnmFileService().get_file(FileType.ARCHIVE, analyzer_rpt.get_archive(),)

            return OfdmSpecAnaAnalysisResponse(
                mac_address = mac,
                status      = ServiceStatusCode.INVALID_OUTPUT_TYPE,
                message     = f"Unsupported output type: {request.analysis.output.type}",
                data        = {},)

# Required for dynamic auto-registration
router = SpectrumAnalyzerRouter().router
