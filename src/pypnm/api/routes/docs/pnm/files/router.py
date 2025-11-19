
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse, JSONResponse

from pypnm.api.routes.docs.pnm.files.schemas import (
    FileAnalysisRequest, FileQueryResponse, FileQueryRequest, PushFileRequest, PushFileResponse, AnalysisResponse)
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.mac_address import MacAddress, MacAddressFormat

class PnmFileManager:
    """
    REST API router for managing PNM test files.

    Endpoints:
    - Search files by MAC or criteria
    - Push/upload new test file
    - Analyze an uploaded or retrieved file
    """

    def __init__(self):
        self.router = APIRouter(prefix="/docs/pnm/files",tags=["PNM File Manager"])
        self._add_routes()

    def _add_routes(self):

        default_mac_address = MacAddress(SystemConfigSettings.default_mac_address).to_mac_format(fmt=MacAddressFormat.COLON).lower()
        
        @self.router.get("/searchFiles/{mac_address}", 
                         response_model=FileQueryResponse, 
                         summary="Search for PNM Files via mac address",
                         responses=FAST_API_RESPONSE,)
        def search_files(mac_address: str = Path(..., description=f"MAC address of the cable modem, default: **{default_mac_address}**")):
            """
            **Search Uploaded PNM Files by MAC Address**

            Returns all registered telemetry capture files associated with a given DOCSIS cable modem.

            Each file represents a measurement such as RxMER, constellation, pre-equalization taps, or spectrum scan, and can be downloaded or analyzed via other endpoints.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/file_manager/file-manager.md#-search-uploaded-files)
            """
            request = FileQueryRequest(mac_address=mac_address)
            result = PnmFileService().search_files(request)
            return JSONResponse(content=result.model_dump())

        @self.router.get("/download/{transaction_id}", 
                         response_class=FileResponse, 
                         summary="Download a PNM file by transaction ID")
        def download_file(transaction_id: str = Path(..., description="Transaction ID of the file")):
            """
            **Download PNM Measurement File by Transaction ID**

            Retrieves the raw binary file generated during a telemetry capture session.
            Used for offline inspection, reprocessing, or historical archiving.

            > ⚠️ Note:  
            > If using SwaggerUI, the file may either download automatically or require clicking the download link in your browser.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/file_manager/file-manager.md#-download-file-by-transaction)
            """
            return PnmFileService().get_file_by_transaction_id(transaction_id)

        @self.router.post("/upload", response_model=PushFileResponse, summary="Upload a PNM File")
        def push_file(request: PushFileRequest):
            """
            """
            result = PnmFileService().push_file(request)
            return JSONResponse(content=result.model_dump())

        @self.router.post("/getAnalysis", response_model=AnalysisResponse, summary="Analyze a PNM File")
        def get_analysis(request: FileAnalysisRequest):
            """
            **Trigger Automated Analysis of a PNM File**

            Launches an analysis routine based on the specified file and test type.
            Automatically selects the correct processor depending on file contents.

            Supports analysis types such as:
            - RxMER per subcarrier
            - Channel estimation
            - Pre-equalization taps
            - Spectrum snapshots

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/file_manager/file-manager.md#-trigger-file-analysis)
            """
            result = PnmFileService().get_analysis(request)
            return JSONResponse(content=result.model_dump())


# Required for auto-discovery via dynamic router loading
router = PnmFileManager().router
