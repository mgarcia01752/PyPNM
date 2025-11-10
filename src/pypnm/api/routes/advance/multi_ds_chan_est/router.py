# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import io
import os
import zipfile
import logging
from typing import Union, Dict, Callable
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from pypnm.api.routes.advance.analysis.signal_analysis.multi_chan_est_singnal_analysis import (
    MultiChanEstimationAnalysisType, MultiChanEstimationSignalAnalysis)
from pypnm.api.routes.advance.common.abstract.service import AbstractService
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.advance.common.operation_manager import OperationManager
from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.advance.multi_ds_chan_est.schemas import (
    MultiChanEstimationAnalysisRequest, MultiChanEstimationAnalysisResponse,
    MultiChanEstimationRequest, MultiChanEstimationResponseStatus,
    MultiChanEstimationStartResponse, MultiChanEstimationStatusResponse,
    AnalysisDataModel)
from pypnm.api.routes.advance.multi_ds_chan_est.service import MultiChannelEstimationService
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.file_capture.types import GroupId
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class MultiDsChanEstRouter(AbstractService):
    """Router for handling Multi-DS-Channel-Estimation operations."""

    def __init__(self) -> None:
        super().__init__()
        self.router = APIRouter(prefix="/advance/multiChannelEstimation",
                                tags=["PNM Operations - Multi-DS-Channel-Estimation"])
        self.logger = logging.getLogger(self.__class__.__name__)
        self._add_routes()

    # ──────────────────────────────────────────────────────────
    # Routes
    # ──────────────────────────────────────────────────────────
    def _add_routes(self) -> None:

        # ──────────────────────────────────────────────────────
        @self.router.post("/start",
            response_model=Union[MultiChanEstimationStartResponse, SnmpResponse],
            summary="Start a multi-sample ChannelEstimation capture")
        async def start_multi_chan_estimation(request: MultiChanEstimationRequest) -> Union[MultiChanEstimationStartResponse, SnmpResponse]:
            duration, interval = request.capture.parameters.measurement_duration, request.capture.parameters.sample_interval
            mac, ip_address = request.cable_modem.mac_address, request.cable_modem.ip_address
            self.logger.info(f"[start] Multi-ChanEst for MAC={mac}, duration={duration}s interval={interval}s")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip_address))
            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(f"[start] Precheck failed for MAC={mac}: {msg}")
                return SnmpResponse(mac_address=mac, status=status, message=msg)

            group_id, operation_id = await self.loadService(MultiChannelEstimationService, cm,
                                                            duration=duration, interval=interval)
            return MultiChanEstimationStartResponse(mac_address=mac, status=OperationState.RUNNING,
                                                    message=None, group_id=group_id, operation_id=operation_id)

        # ──────────────────────────────────────────────────────
        @self.router.get("/status/{operation_id}",
            response_model=MultiChanEstimationStatusResponse,
            summary="Get status of a multi-sample ChannelEstimation capture")
        def get_status(operation_id: str) -> MultiChanEstimationStatusResponse:
            try: service: MultiChannelEstimationService = self.getService(operation_id)  # type: ignore
            except KeyError: raise HTTPException(status_code=404, detail="Operation not found")

            status = service.status(operation_id)
            return MultiChanEstimationStatusResponse(
                mac_address=str(service.cm.get_mac_address),
                status="success",
                message=None,
                operation=MultiChanEstimationResponseStatus(
                    operation_id=operation_id,
                    state=status["state"],
                    collected=status["collected"],
                    time_remaining=status["time_remaining"],
                    message=None))

        # ──────────────────────────────────────────────────────
        @self.router.get("/results/{operation_id}",
            summary="Download a ZIP archive of all ChannelEstimation capture files",
            responses={200: {"content": {"application/zip": {}},
                             "description": "ZIP archive of capture files"}})
        def download_results_zip(operation_id: str) -> StreamingResponse:
            svc: MultiChannelEstimationService = self.getService(operation_id)  # type: ignore
            samples = svc.results(operation_id)
            save_dir, mac = SystemConfigSettings.save_dir, str(svc.cm.get_mac_address).replace(":", "")
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for s in samples:
                    path = os.path.join(save_dir, s.filename)
                    try: zf.write(path, arcname=os.path.basename(s.filename))
                    except FileNotFoundError: self.logger.warning(f"[zip] Missing: {path}")
                    except Exception as e: self.logger.warning(f"[zip] Skip {path}: {e}")
            buf.seek(0)
            headers = {"Content-Disposition": f"attachment; filename=multiChannelEstimation_{mac}_{operation_id}.zip"}
            return StreamingResponse(buf, media_type="application/zip", headers=headers)

        # ──────────────────────────────────────────────────────
        @self.router.delete("/stop/{operation_id}",
            response_model=MultiChanEstimationStatusResponse,
            summary="Stop a running multi-sample ChannelEstimation capture early")
        def stop_capture(operation_id: str) -> MultiChanEstimationStatusResponse:
            try: service: MultiChannelEstimationService = self.getService(operation_id)  # type: ignore
            except KeyError: raise HTTPException(status_code=404, detail="Operation not found")

            service.stop(operation_id)
            status = service.status(operation_id)
            return MultiChanEstimationStatusResponse(
                mac_address=str(service.cm.get_mac_address),
                status=OperationState.STOPPED,
                message=None,
                operation=MultiChanEstimationResponseStatus(
                    operation_id=operation_id,
                    state=status["state"],
                    collected=status["collected"],
                    time_remaining=status["time_remaining"],
                    message=None))

        # ──────────────────────────────────────────────────────
        @self.router.post("/analysis",
            response_model=MultiChanEstimationAnalysisResponse,
            summary="Perform signal analysis on a previously executed Multi-ChannelEstimation")
        # ──────────────────────────────────────────────────────
        @self.router.post("/analysis",
            response_model=MultiChanEstimationAnalysisResponse,
            summary="Perform signal analysis on a previously executed Multi-ChannelEstimation")
        def analysis(request: MultiChanEstimationAnalysisRequest) -> Union[MultiChanEstimationAnalysisResponse, FileResponse]:
            """
            Perform post-capture analysis on Multi-ChannelEstimation measurement data.

            Supports:
            - MIN_AVG_MAX
            - GROUP_DELAY
            - LTE_DETECTION_PHASE_SLOPE
            - ECHO_DETECTION_PHASE_SLOPE
            - ECHO_DETECTION_IFFT
            """
            try:
                capture_group_id: GroupId = OperationManager.get_capture_group(request.operation_id)
                self.logger.info(f"[analysis] operation_id={request.operation_id} capture_group={capture_group_id}")
            except KeyError:
                msg = f"No capture group found for operation {request.operation_id}"
                self.logger.error(msg)
                return MultiChanEstimationAnalysisResponse(
                    mac_address=MacAddress.null(),
                    status=ServiceStatusCode.CAPTURE_GROUP_NOT_FOUND,
                    message=msg,
                    data=AnalysisDataModel(analysis_type="UNKNOWN", results=[]))

            # Prepare data aggregator
            cda = CaptureDataAggregator(capture_group_id)

            # Parse analysis type
            try:
                atype = MultiChanEstimationAnalysisType(request.analysis.type)
            except ValueError:
                msg = f"Invalid analysis type: {request.analysis.type}"
                self.logger.error(msg)
                return MultiChanEstimationAnalysisResponse(
                    mac_address=MacAddress.null(),
                    status=ServiceStatusCode.DS_OFDM_CHAN_EST_INVALID_ANALYSIS_TYPE,
                    message=msg,
                    data=AnalysisDataModel(analysis_type="UNKNOWN", results=[]))

            # Dispatch map for type → analysis engine
            analysis_map: Dict[MultiChanEstimationAnalysisType, Callable[[CaptureDataAggregator], MultiChanEstimationSignalAnalysis]] = {
                MultiChanEstimationAnalysisType.MIN_AVG_MAX: lambda agg: MultiChanEstimationSignalAnalysis(agg, MultiChanEstimationAnalysisType.MIN_AVG_MAX),
                MultiChanEstimationAnalysisType.GROUP_DELAY: lambda agg: MultiChanEstimationSignalAnalysis(agg, MultiChanEstimationAnalysisType.GROUP_DELAY),
                MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE: lambda agg: MultiChanEstimationSignalAnalysis(agg, MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE),
                MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE: lambda agg: MultiChanEstimationSignalAnalysis(agg, MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE),
                MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT: lambda agg: MultiChanEstimationSignalAnalysis(agg, MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT),
            }

            if atype not in analysis_map:
                msg = f"Unsupported analysis type: {atype}"
                self.logger.error(msg)
                return MultiChanEstimationAnalysisResponse(
                    mac_address     =   MacAddress.null(),
                    status          =   ServiceStatusCode.DS_OFDM_CHAN_EST_INVALID_ANALYSIS_TYPE,
                    message         =   msg,
                    data            =   AnalysisDataModel(analysis_type="UNKNOWN", results=[]))

            # Determine output type
            output_type = FileType(request.output.type)
            engine = analysis_map[atype](cda)
            analysis_result = engine.to_model()

            # Handle output formats
            if output_type == FileType.JSON:
                err = analysis_result.error
                status = ServiceStatusCode.SUCCESS if not err else ServiceStatusCode.FAILURE
                message = err or f"Analysis {analysis_result.analysis_type} completed for group {capture_group_id}"
                data_model = AnalysisDataModel(
                    analysis_type=analysis_result.analysis_type,
                    results=[r.model_dump() for r in analysis_result.results])

                mac = str(engine.getMacAddresses()[0])
                self.logger.info(f"[analysis] type={atype.name} mac={mac} status={status.name} group={capture_group_id}")

                return MultiChanEstimationAnalysisResponse(
                    mac_address =   mac,
                    status      =   status,
                    message     =   message,
                    data        =   data_model)

            elif output_type == FileType.ARCHIVE:
                try:
                    engine.create_csv()
                    engine.create_matplot()
                    rpt = engine.build_report()
                    self.logger.info(f"[analysis] Built archive report for group {capture_group_id}")
                    return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)
                
                except Exception as e:
                    msg = f"Archive build failed: {e}"
                    self.logger.error(msg)
                    return MultiChanEstimationAnalysisResponse(
                        mac_address =   MacAddress.null(),
                        status      =   ServiceStatusCode.FAILURE,
                        message     =   msg,
                        data        =   AnalysisDataModel(analysis_type=atype.name, results=[]))

            # Unsupported output type
            msg = f"Unsupported output type: {output_type}"
            self.logger.error(msg)
            return MultiChanEstimationAnalysisResponse(
                mac_address=MacAddress.null(),
                status=ServiceStatusCode.INVALID_OUTPUT_TYPE,
                message=msg,
                data=AnalysisDataModel(analysis_type=atype.name, results=[]))

# Auto-register
router = MultiDsChanEstRouter().router
