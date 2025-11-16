from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Any, Dict, List, cast

from fastapi import APIRouter

from pypnm.api.routes.basic.us_ofdma_pre_eq_analysis_rpt import CmUsOfdmaPreEqReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.common.enum import OutputType
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisResponse, PnmSingleCaptureRequest,)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import (
    SnmpResponse,)
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import (
    CableModemServicePreCheck,)
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.api.routes.docs.pnm.us.ofdma.pre_equalization.service import (
    CmUsOfdmaPreEqService,)
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.pnm.DocsPnmCmUsPreEqEntry import DocsPnmCmUsPreEqEntry
from pypnm.lib.dict_utils import DictUtils
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import InetAddressStr, MacAddressStr, Path


class UsOfdmaPreEqualizationRouter:
    def __init__(self):
        prefix             = "/docs/pnm/us/ofdma"
        self.base_endpoint = "/preEqualization"
        self.router        = APIRouter(
            prefix=prefix, tags=["PNM Operations - Upstream OFDMA Pre-Equalization"])
        self.logger        = logging.getLogger(
            f'UsOfdmaPreEqualizationRouter.{self.base_endpoint.strip("/")}')
        self.__routes()

    def __routes(self) -> None:
        @self.router.post(
            f"{self.base_endpoint}/getCapture",
            summary="Get Upstream OFDMA Pre-Equalization Capture",
            responses=FAST_API_RESPONSE,)
        async def get_capture(request: PnmSingleCaptureRequest):
            """
            Capture Upstream OFDMA Pre-Equalization Coefficients.

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/single/us/ofdma/pre-equalization.md#get-capture)

            """
            mac: MacAddressStr = request.cable_modem.mac_address
            ip: InetAddressStr = request.cable_modem.ip_address

            self.logger.info(
                f"Starting Upstream OFDMA Pre-Equalization measurement for MAC: {mac}, IP: {ip}")

            cm = CableModem(MacAddress(mac), Inet(ip))

            status, msg = await CableModemServicePreCheck(cable_modem=cm, 
                                                          validate_ofdma_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=mac, status=status, message=msg)

            service: CmUsOfdmaPreEqService = CmUsOfdmaPreEqService(cm)
            msg_rsp: MessageResponse = await service.set_and_go()

            if msg_rsp.status != ServiceStatusCode.SUCCESS:
                err = "Unable to complete Upstream OFDMA Pre-Equalization measurement."
                return SnmpResponse(mac_address=mac, message=err, status=msg_rsp.status)

            measurement_stats:List[DocsPnmCmUsPreEqEntry] = \
                cast(List[DocsPnmCmUsPreEqEntry], await service.getPnmMeasurementStatistics())

            cps    = CommonProcessService(msg_rsp)
            msg_rsp = cps.process()

            analysis = Analysis(AnalysisType.BASIC, msg_rsp)

            if request.analysis.output.type == OutputType.JSON:
                payload: Dict[str, Any] = cast(Dict[str, Any], analysis.get_results())

                # Clean up payload by removing unneeded or redundant sections
                DictUtils.pop_keys_recursive(payload, ["pnm_header", "modulations", "snr_db_values"])
                primative = msg_rsp.payload_to_dict('primative')
                DictUtils.pop_keys_recursive(primative, ["device_details", "modulation_statistics"])
                payload.update(primative)
                payload.update(DictUtils.models_to_nested_dict(measurement_stats, 'measurement_stats',))

                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.SUCCESS,
                    data        =   payload,)

            elif request.analysis.output.type == OutputType.ARCHIVE:
                analysis_rpt = CmUsOfdmaPreEqReport(analysis)
                rpt: Path    = cast(Path, analysis_rpt.build_report())
                return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)

            else:
                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.INVALID_OUTPUT_TYPE,
                    data        =   {},)


# Required for dynamic auto-registration
router = UsOfdmaPreEqualizationRouter().router
