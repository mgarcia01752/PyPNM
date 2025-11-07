from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import Any, Dict, List, cast

from fastapi import APIRouter

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisRptMatplotConfig
from pypnm.api.routes.basic.fec_summary_analysis_rpt import FecSummaryAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.common.enum import OutputType
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.schemas import PnmFecSummaryAnalysisRequest
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.service import CmDsOfdmFecSummaryService
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import FecSummaryType
from pypnm.docsis.data_type.pnm.DocsPnmCmDsOfdmFecEntry import DocsPnmCmDsOfdmFecEntry
from pypnm.lib.dict_utils import DictUtils
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import InetAddressStr, MacAddressStr


class FecSummaryRouter:
    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        self.base_endpoint = "/fecSummary"
        self.router = APIRouter(prefix=prefix, tags=["PNM Operations - Downstream OFDM FEC Summary"])
        self.logger = logging.getLogger(f'FecSummaryRouter.{self.base_endpoint.strip("/")}')
        self.__routes()

    def __routes(self) -> None:
        @self.router.post(
            f"{self.base_endpoint}/getCapture",
            summary="Get FEC Summary PNM Capture",
            responses=FAST_API_RESPONSE,)
        async def get_capture(request: PnmFecSummaryAnalysisRequest):
            """
            Capture Downstream OFDM FEC Summary Statistics.

            Retrieves corrected/uncorrectable codeword counters for the selected FEC
            summary interval (e.g., 10-minute or 24-hour) across active OFDM profiles.

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/single/ds/ofdm/fec-summary.md)
            """
            mac: MacAddressStr = request.cable_modem.mac_address
            ip: InetAddressStr = request.cable_modem.ip_address
            self.logger.info(f"Starting FEC Summary capture for MAC: {mac}, IP: {ip}")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm, validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=mac, status=status, message=msg)

            fec_type:FecSummaryType = request.capture_settings.fec_summary_type
            service = CmDsOfdmFecSummaryService(cable_modem=cm, fec_summary_type=fec_type)
            msg_rsp: MessageResponse = await service.set_and_go()

            if msg_rsp.status != ServiceStatusCode.SUCCESS:
                err = "Unable to complete FEC Summary capture."
                return SnmpResponse(mac_address=mac, message=err, status=msg_rsp.status)

            measurement_stats:List[DocsPnmCmDsOfdmFecEntry] = \
                cast(List[DocsPnmCmDsOfdmFecEntry], await service.getPnmMeasurementStatistics())

            cps = CommonProcessService(msg_rsp)
            msg_rsp = cps.process()

            analysis = Analysis(AnalysisType.BASIC, msg_rsp)

            if request.analysis.output.type == OutputType.JSON:
                payload: Dict[str, Any] = cast(Dict[str, Any], analysis.get_results())
                DictUtils.pop_keys_recursive(payload, ["pnm_header", "mac_address"])

                primative = msg_rsp.payload_to_dict('primative')
                DictUtils.pop_keys_recursive(primative, ["device_details"])
                payload.update(msg_rsp.payload_to_dict("primative"))

                payload.update(DictUtils.models_to_nested_dict(measurement_stats, 'measurement_stats',))

                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.SUCCESS,
                    data        =   payload)

            elif request.analysis.output.type == OutputType.ARCHIVE:
                theme = request.analysis.plot.ui.theme
                plot_config = AnalysisRptMatplotConfig(theme = theme) 
                analysis_rpt = FecSummaryAnalysisReport(analysis, plot_config)
                rpt: Path = cast(Path, analysis_rpt.build_report())
                return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)

            else:
                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.INVALID_OUTPUT_TYPE,
                    data        =   {},)


# Required for dynamic auto-registration
router = FecSummaryRouter().router
