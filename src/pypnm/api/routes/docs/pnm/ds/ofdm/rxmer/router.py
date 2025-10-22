# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, cast

from fastapi import APIRouter

from pypnm.api.routes.basic.rxmer_analysis_rpt import RxMerAnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmAnalysisResponse,)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import (
    SnmpResponse,)
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import (
    CableModemServicePreCheck,)
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.rxmer.service import CmDsOfdmRxMerService
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import InetAddressStr, MacAddressStr

class RxMerRouter:
    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        self.base_endpoint = "/rxMer"
        self.router = APIRouter(
            prefix=prefix, tags=["PNM Operations - Downstream OFDM RxMER"])
        self.logger = logging.getLogger(f'RxMerRouter.{self.base_endpoint.strip("/")}')
        self.__routes()

    def __routes(self) -> None:
        @self.router.post(
            f"{self.base_endpoint}/getCapture",
            summary="Get RxMER PNM Capture File",
            responses=FAST_API_RESPONSE,)
        async def get_capture(request: PnmAnalysisRequest):
            """
            Capture Downstream OFDM RxMER Per-Subcarrier Values.

            Returns either:
              * JSON (PnmAnalysisResponse) when request.output.type == JSON
              * File download (archive) when request.output.type == ARCHIVE
              * SnmpResponse on precheck/measurement failure
            """
            mac: MacAddressStr = request.cable_modem.mac_address
            ip: InetAddressStr = request.cable_modem.ip_address
            tftpv4: Inet = Inet(cast(InetAddressStr, request.cable_modem.pnm_parameters.tftp.ipv4))
            tftpv6: Inet = Inet(cast(InetAddressStr, request.cable_modem.pnm_parameters.tftp.ipv6))

            self.logger.info(f"Starting RxMER measurement for MAC: {mac}, IP: {ip}")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm, validate_ofdm_exist=True).run_precheck()
            
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=mac, status=status, message=msg)

            service: CmDsOfdmRxMerService = CmDsOfdmRxMerService(cm, (tftpv4,tftpv6))
            msg_rsp: MessageResponse = await service.set_and_go()

            if msg_rsp.status != ServiceStatusCode.SUCCESS:
                err = "Unable to complete RxMER measurement."
                return SnmpResponse(mac_address=mac, message=err, status=msg_rsp.status)

            cps = CommonProcessService(msg_rsp)
            msg_rsp = cps.process()

            analysis = Analysis(AnalysisType.BASIC, msg_rsp)

            if request.output.type == FileType.JSON.value:
                payload: Dict[str, Any] = cast(Dict[str, Any], analysis.get_results())
                payload.update(msg_rsp.payload_to_dict())
                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.SUCCESS,
                    data        =   payload,)

            elif request.output.type == FileType.ARCHIVE.value:
                analysis_rpt = RxMerAnalysisReport(analysis)
                rpt: Path = cast(Path, analysis_rpt.build_report())
                return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)

            else:
                return PnmAnalysisResponse(
                    mac_address =   mac,
                    status      =   ServiceStatusCode.INVALID_OUTPUT_TYPE,
                    data        =   {},)


# Required for dynamic auto-registration
router = RxMerRouter().router
