# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import io
import json
import logging
import os
from typing import Union
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from pypnm.api.routes.advance.analysis.signal_analysis.multi_rxmer_signal_analysis import (
    MultiRxMerAnalysisType, MultiRxMerSignalAnalysis)
from pypnm.api.routes.advance.common.abstract.service import AbstractService
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.advance.common.operation_manager import OperationManager
from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.advance.common.pnm_collection import PnmCollection

from pypnm.api.routes.advance.multi_rxmer.schemas import (MeaureModes, MultiRxMerAnalysisRequest, 
                                                          MultiRxMerAnalysisResponse, MultiRxMerRequest, 
                                                          MultiRxMerResponseStatus, MultiRxMerStartResponse, 
                                                          MultiRxMerStatusResponse)
from pypnm.api.routes.advance.multi_rxmer.service import MultiRxMer_Ofdm_Performance_1_Service, MultiRxMerService
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.config_manager import ConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.utils import Utils

class MultiRxMerRouter(AbstractService):
    """
    Router for handling Multi-RxMER operations:
      - start a periodic RxMER capture
      - query status (# samples, state)
      - fetch all collected samples
      - stop the capture early

    Inherits:
        AbstractService: provides load_service and get_service helpers.
    """
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/advance/multiRxMer",
            tags=["PNM Operations - Multi-Downstream OFDM RxMER"],)
        self._add_routes()

    def _add_routes(self) -> None:
        @self.router.post("/start",
            response_model=Union[MultiRxMerStartResponse, SnmpResponse],
            summary="Start a multi-sample RxMER capture",)
        async def start_multi_rxmer(request: MultiRxMerRequest) -> Union[MultiRxMerStartResponse, SnmpResponse]:
            """
            Kick off a background task that instructs the CM to TFTP-upload RxMER
            captures at regular intervals. Returns both a group_id and operation_id.
            """
            duration = request.capture.parameters.measurement_duration
            interval = request.capture.parameters.sample_interval
            
            measure_modes = request.measure.mode
            msg:str = ""
            
            self.logger.info(
                f"Starting Multi-RxMER capture for MAC={request.mac_address} "
                f"(duration={duration}s, interval={interval}s)")

            cable_modem = CableModem(
                mac_address=MacAddress(request.mac_address),
                inet=Inet(request.ip_address),
            )

            status, msg = CableModemServicePreCheck(cable_modem=cable_modem).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status,
                    message=msg
                )   

            if measure_modes == MeaureModes.CONTINUOUS:
                msg=f'Starting Multi-RxMER capture for MAC={request.mac_address}'
                self.logger.info(f'{msg}')
                group_id, operation_id = await self.loadService(
                    MultiRxMerService,
                    cable_modem,
                    duration=duration,
                    interval=interval,
                )
                
                
            elif measure_modes == MeaureModes.OFDM_PERFORMANCE_1:
                msg=f'Starting Multi-RxMER-OFDM-Performance-1 capture for MAC={request.mac_address}'
                self.logger.info(f'{msg}')
                group_id, operation_id = await self.loadService(
                    MultiRxMer_Ofdm_Performance_1_Service,
                    cable_modem,
                    duration=duration,
                    interval=interval,
                )
                
                
            else:
                self.logger.error(f'Invalid Measure Mode Selected: ({measure_modes})')
                return MultiRxMerStartResponse(
                    mac_address=request.mac_address,
                    status=ServiceStatusCode.MEASURE_MODE_INVALID,
                    message=f"{ServiceStatusCode.MEASURE_MODE_INVALID.name}",
                    group_id="",
                    operation_id="",
                )
                                
            return MultiRxMerStartResponse(
                mac_address=request.mac_address,
                status=OperationState.RUNNING,
                message=msg,
                group_id=group_id,
                operation_id=operation_id,
            )

        @self.router.get("/status/{operation_id}",
            response_model=MultiRxMerStartResponse,
            summary="Get status of a multi-sample RxMER capture",)
        def get_status(operation_id: str) -> MultiRxMerStatusResponse:
            """
            Get the current state and sample count for a given RxMER operation.

            Raises:
                HTTPException: 404 if operation_id is not found.
            """
            try:
                service:MultiRxMerService = self.getService(operation_id) # type: ignore
                
            except KeyError:
                raise HTTPException(status_code=404, detail="Operation not found")

            status = service.status(operation_id)

            return MultiRxMerStatusResponse(
                mac_address=str(service.cm.get_mac_address),
                status="success",
                message=None,
                operation=MultiRxMerResponseStatus(
                    operation_id=operation_id,
                    state=status["state"],
                    collected=status["collected"],
                    time_remaining=status["time_remaining"],
                    message=None,
                ),
            )

        @self.router.get("/results/{operation_id}",
            summary="Download a ZIP archive of all RxMER capture files",
            responses={
                200: {
                    "content": {"application/zip": {}},
                    "description": "ZIP archive of capture files",
                }
            },
        )
        def download_results_zip(operation_id: str) -> StreamingResponse:
            """
            Stream a ZIP file containing all captured RxMER files for this operation.
            Raises 404 if operation not found.
            """
            svc:MultiRxMerService = self.getService(operation_id) # type: ignore
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

            headers = {"Content-Disposition": f"attachment; filename=multiRxMer_{mac}_{operation_id}.zip"}
            return StreamingResponse(buf, media_type="application/zip", headers=headers)

        @self.router.delete("/stop/{operation_id}",
            response_model=MultiRxMerStatusResponse,
            summary="Stop a running Multi-RxMER capture early",)
        def stop_capture(operation_id: str) -> MultiRxMerStatusResponse:
            """
            Signal capture to stop after the current iteration.

            Raises:
                HTTPException: 404 if operation_id is not found.
            """
            try:
                service:MultiRxMerService = self.getService(operation_id) # type: ignore
            except KeyError:
                raise HTTPException(status_code=404, detail="Operation not found")

            service.stop(operation_id)
            status = service.status(operation_id)

            return MultiRxMerStatusResponse(
                mac_address=str(service.cm.get_mac_address),
                status=OperationState.STOPPED,
                message=None,
                operation=MultiRxMerResponseStatus(
                    operation_id=operation_id,
                    state=status["state"],
                    collected=status["collected"],
                    time_remaining=status["time_remaining"],
                    message=None,
                ),
            )

        @self.router.post("/analysis",
            response_model=MultiRxMerAnalysisResponse,
            summary="Perform signal analysis on a previously executed Multi-RxMER",
            description="""
        **Analysis Type:**

        MIN_AVG_MAX  = 0
        OFDM_PROFILE_PERFORMANCE = 1  
        RXMER_HEAT_MAP = 2
        """
        )
        def analysis(request: MultiRxMerAnalysisRequest) -> MultiRxMerAnalysisResponse:
            # 1) Resolve the capture_group_id
            try:
                capture_group_id = OperationManager.get_capture_group(request.operation_id)
            except KeyError:
                return MultiRxMerAnalysisResponse(
                    mac_address=request.mac_address,
                    status=ServiceStatusCode.CAPTURE_GROUP_NOT_FOUND,
                    message=f"No capture group found for operation {request.operation_id}",
                    data={}
                )

            # 2) Load and index the raw PNM files
            aggregator = CaptureDataAggregator(capture_group_id)
            pcollect: PnmCollection = aggregator.getPnmCollection()
            if not pcollect:
                return MultiRxMerAnalysisResponse(
                    mac_address=request.mac_address,
                    status=ServiceStatusCode.FAILURE,
                    message=f"Unable to collect PNM files for group {capture_group_id}",
                    data={}
                )

            # 3) Dispatch based on requested analysis_type
            atype = MultiRxMerAnalysisType(request.analysis.analysis_type)
            
            if atype == MultiRxMerAnalysisType.MIN_AVG_MAX:
                engine = MultiRxMerSignalAnalysis(pcollect, MultiRxMerAnalysisType.MIN_AVG_MAX)
                analysis_rst_dict = engine.to_dict()
                
            elif atype == MultiRxMerAnalysisType.OFDM_PROFILE_PERFORMANCE_1:
                '''
                    Operation of this test:
                    -----------------------
                    * Collect a seriers of RxMER
                    * Collect at least 1 Modualtion Profile=
                    * Collect a Fec Summary at:
                        - 1 FecSummary every 10 Min
                        - At end of the test
                        
                    OFDM_PROFILE_MEASUREMENT_1
                    --------------------------    
                    * Calculate the Avg RxMER of the series
                    * Calculate Shannon for each subcarrier
                    * Compare each modualtion profile against the RxMER Average
                    * Calculate the percentage of subcarries that are outside a given profile
                    * Provide total FEC Stats for each profile over the time of the capture.
                '''
                engine = MultiRxMerSignalAnalysis(pcollect, MultiRxMerAnalysisType.OFDM_PROFILE_PERFORMANCE_1)
                analysis_rst_dict = engine.to_dict()                
            
            elif atype == MultiRxMerAnalysisType.RXMER_HEAT_MAP:
                engine = MultiRxMerSignalAnalysis(pcollect, MultiRxMerAnalysisType.RXMER_HEAT_MAP)
                analysis_rst_dict = engine.to_dict()
            
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {atype}")

            # 4) Map analysis output to response fields
            data = analysis_rst_dict.get("data", [])
            error = analysis_rst_dict.get("error")
            status = ServiceStatusCode.SUCCESS if not error else ServiceStatusCode.FAILURE
            message = error or f"Analysis {MultiRxMerAnalysisType(atype).name} completed for group {capture_group_id}"

            FileProcessor(f'ofdm-prof-1-{Utils.time_stamp()}.json').write_file(json.dumps(data))
            
            return MultiRxMerAnalysisResponse(
                mac_address=request.mac_address,
                status=status,
                message=message,
                data=data
            )

# For dynamic auto-registration
router = MultiRxMerRouter().router
