# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import io
import logging
import os
from typing import Union
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


from pypnm.api.routes.advance.analysis.signal_analysis.multi_chan_est_singnal_analysis import (
    MultiChanEstimationAnalysisType, MultiChanEstimationSignalAnalysis)
from pypnm.api.routes.advance.common.abstract.service import AbstractService
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.advance.common.operation_manager import OperationManager
from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.advance.common.pnm_collection import PnmCollection
from pypnm.api.routes.advance.multi_ds_chan_est.schemas import (
    MultiChanEstimationAnalysisRequest, MultiChanEstimationAnalysisResponse, 
    MultiChanEstimationRequest, MultiChanEstimationResponseStatus, 
    MultiChanEstimationStartResponse, MultiChanEstimationStatusResponse)
from pypnm.api.routes.advance.multi_ds_chan_est.service import MultiChannelEstimationService
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.config_manager import ConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class MultiDsChanEstRouter(AbstractService):
    """
    Router for handling Multi-DS-Channel-Estimation operations:
      - start a periodic ChannelEstimation capture
      - query status (# samples, state)
      - fetch all collected samples
      - stop the capture early

    Inherits:
        AbstractService: provides load_service and get_service helpers.
    """
    def __init__(self) -> None:
        super().__init__()
        self.router = APIRouter(
            prefix="/advance/multiChannelEstimation",
            tags=["PNM Operations - Multi-DS-Channel-Estimation"],)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._add_routes()

    def _add_routes(self) -> None:
        @self.router.post("/start",
            response_model=Union[MultiChanEstimationStartResponse, SnmpResponse],
            summary="Start a multi-sample ChannelEstimation capture",)
        async def start_multi_ChanEstimation(request: MultiChanEstimationRequest) -> Union[MultiChanEstimationStartResponse, SnmpResponse]:
            """
            Kick off a background task that instructs the CM to TFTP-upload ChannelEstimation
            captures at regular intervals. Returns both a group_id and operation_id.
            """
            duration = request.capture.parameters.measurement_duration
            interval = request.capture.parameters.sample_interval

            self.logger.info(
                f"Starting multi-ChannelEstimation capture for MAC={request.mac_address} "
                f"(duration={duration}s, interval={interval}s)")

            cm = CableModem(
                mac_address=MacAddress(request.mac_address),
                inet=Inet(request.ip_address),
            )

            status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )   

            group_id, operation_id = await self.loadService(
                MultiChannelEstimationService,
                cm,
                duration=duration,
                interval=interval,
            )

            return MultiChanEstimationStartResponse(
                mac_address=request.mac_address,
                status=OperationState.RUNNING,
                message=None,
                group_id=group_id,
                operation_id=operation_id,
            )

        @self.router.get("/status/{operation_id}",
            response_model=MultiChanEstimationStatusResponse,
            summary="Get status of a multi-sample ChannelEstimation capture",)
        def get_status(operation_id: str) -> MultiChanEstimationStatusResponse:
            """
            Get the current state and sample count for a given ChannelEstimation operation.

            Raises:
                HTTPException: 404 if operation_id is not found.
            """
            try:
                service:MultiChannelEstimationService = self.getService(operation_id) # type: ignore
                
            except KeyError:
                raise HTTPException(status_code=404, detail="Operation not found")

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
                    message=None,
                ),
            )

        @self.router.get("/results/{operation_id}",
            summary="Download a ZIP archive of all ChannelEstimation capture files",
            responses={
                200: {
                    "content": {"application/zip": {}},
                    "description": "ZIP archive of capture files",
                }
            },
        )
        def download_results_zip(operation_id: str) -> StreamingResponse:
            """
            Stream a ZIP file containing all captured ChannelEstimation files for this operation.
            Raises 404 if operation not found.
            """
            svc:MultiChannelEstimationService = self.getService(operation_id) # type: ignore
            samples = svc.results(operation_id)

            save_dir = ConfigManager().get("PnmFileRetrieval","save_dir")
            mac = str(svc.cm.get_mac_address).replace(":", "")
            
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
                for sample in samples:
                    file_path = os.path.join(save_dir, sample.filename)
                    arcname = os.path.basename(sample.filename)
                    try:
                        zipf.write(file_path, arcname=arcname)
                    except FileNotFoundError:
                        self.logger.warning(f"File not found, skipping: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Skipping {file_path}: {e}")
                        
            buf.seek(0)

            headers = {"Content-Disposition": f"attachment; filename=multiChannelEstimation_{mac}_{operation_id}.zip"}
            return StreamingResponse(buf, media_type="application/zip", headers=headers)

        @self.router.delete("/stop/{operation_id}",
            response_model=MultiChanEstimationStatusResponse,
            summary="Stop a running multi-sample ChannelEstimation capture early",)
        def stop_capture(operation_id: str) -> MultiChanEstimationStatusResponse:
            """
            Signal capture to stop after the current iteration.

            Raises:
                HTTPException: 404 if operation_id is not found.
            """
            try:
                service:MultiChannelEstimationService = self.getService(operation_id) # type: ignore
            except KeyError:
                raise HTTPException(status_code=404, detail="Operation not found")

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
                    message=None,
                ),
            )

        @self.router.post("/analysis",
            response_model=MultiChanEstimationAnalysisResponse,
            summary="Perform signal analysis on a previously executed Multi-ChannelEstimation",
            description="""
        **Analysis Type:**
        
        MIN_AVG_MAX                 = 0
        GROUP_DELAY                 = 1
        LTE_DETECTION_PHASE_SLOPE   = 2
        ECHO_DETECTION_PHASE_SLOPE  = 3
        ECHO_DETECTION_IFFT         = 4
        """     
        )
        def analysis(request: MultiChanEstimationAnalysisRequest) -> MultiChanEstimationAnalysisResponse:
            # 1) Resolve the capture_group_id
            try:
                capture_group_id:str = OperationManager.get_capture_group(request.operation_id)
            except KeyError:
                return MultiChanEstimationAnalysisResponse(
                    mac_address=request.mac_address,
                    status=ServiceStatusCode.CAPTURE_GROUP_NOT_FOUND,
                    message=f"No capture group found for operation {request.operation_id}",
                    data={}
                )

            # 2) Load and index the raw PNM files
            aggregator = CaptureDataAggregator(capture_group_id)
            pcollect: PnmCollection = aggregator.getPnmCollection()
            if not pcollect:
                return MultiChanEstimationAnalysisResponse(
                    mac_address=request.mac_address,
                    status=ServiceStatusCode.FAILURE,
                    message=f"Unable to collect PNM files for group {capture_group_id}",
                    data={}
                )

            # 3) Dispatch based on requested analysis_type
            atype = MultiChanEstimationAnalysisType(request.analysis.analysis_type)
            
            if atype == MultiChanEstimationAnalysisType.MIN_AVG_MAX:
                engine = MultiChanEstimationSignalAnalysis(pcollect, MultiChanEstimationAnalysisType.MIN_AVG_MAX)
                analysis_rst_dict = engine.to_dict()
                
            elif atype == MultiChanEstimationAnalysisType.GROUP_DELAY:
                engine = MultiChanEstimationSignalAnalysis(pcollect, MultiChanEstimationAnalysisType.GROUP_DELAY)
                analysis_rst_dict = engine.to_dict()
                            
            elif atype == MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
                engine = MultiChanEstimationSignalAnalysis(pcollect, MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE)
                analysis_rst_dict = engine.to_dict()
                print(analysis_rst_dict)
                
            elif atype == MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
                engine = MultiChanEstimationSignalAnalysis(pcollect, MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE)
                analysis_rst_dict = engine.to_dict()                

            elif atype == MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
                engine = MultiChanEstimationSignalAnalysis(pcollect, MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT)
                analysis_rst_dict = engine.to_dict()   
            
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {atype}")

            # 4) Map analysis output to response fields
            data = analysis_rst_dict.get("data", [])
            error = analysis_rst_dict.get("error")
            status = ServiceStatusCode.SUCCESS if not error else ServiceStatusCode.FAILURE
            message = error or f"Analysis {MultiChanEstimationAnalysisType(atype).name} completed for group {capture_group_id}"

            return MultiChanEstimationAnalysisResponse(
                mac_address=request.mac_address,
                status=status,
                message=message,
                data=data
            )

# For dynamic auto-registration
router = MultiDsChanEstRouter().router
