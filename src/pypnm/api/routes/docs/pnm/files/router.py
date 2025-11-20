from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from fastapi import APIRouter, Path, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from pypnm.api.routes.common.classes.file_capture.types import TransactionId
from pypnm.api.routes.docs.pnm.files.schemas import (
    FileAnalysisRequest, FileQueryResponse, FileQueryRequest, 
    UploadFileRequest, UploadFileResponse, AnalysisResponse)
from pypnm.api.routes.docs.pnm.files.service import PnmFileService
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.fastapi_constants import FAST_API_RESPONSE
from pypnm.lib.mac_address import MacAddress, MacAddressFormat
from pypnm.lib.types import FileNameStr, MacAddressStr, PathLike


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
        def search_files(mac_address: MacAddressStr = Path(..., description=f"MAC address of the cable modem, default: **{default_mac_address}**")):
            """
            **Search Uploaded PNM Files by MAC Address**

            Returns all registered telemetry capture files associated with a given DOCSIS cable modem.

            Each file represents a measurement such as RxMER, constellation, pre-equalization taps, or spectrum scan, and can be downloaded or analyzed via other endpoints.

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/file_manager/file-manager.md#-search-uploaded-files)
            """
            request = FileQueryRequest(mac_address=mac_address)
            result  = PnmFileService().search_files(request)
            return JSONResponse(content=result.model_dump())

        @self.router.get("/download/transactionID/{transaction_id}", 
                         response_class=FileResponse, 
                         summary="Download a PNM file by transaction ID",
                         responses=FAST_API_RESPONSE,)
        def download_file_via_transaction_id(transaction_id: TransactionId = Path(description="Transaction ID of the file")):
            """
            **Download PNM Measurement File by Transaction ID**

            Download a previously uploaded PNM measurement file using its unique transaction ID.

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/file_manager/file-manager.md#-download-file-by-transaction)
            """
            return PnmFileService().get_file_by_transaction_id(transaction_id)

        @self.router.get("/download/macAddress/{mac_address}", 
                         response_class=FileResponse, 
                         summary="Download a PNM file by transaction ID",
                         responses=FAST_API_RESPONSE,)
        def download_file_via_mac_address(mac_address: MacAddressStr = Path(..., description="MAC address of the cable modem")):
            """
            **Download PNM Measurement File by MacAddress**

            Download a previously uploaded PNM measurement files using its associated MAC address.

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/file_manager/file-manager.md#-download-file-by-transaction)
            """
            return PnmFileService().get_file_by_macaddress(mac_address)

        @self.router.get("/download/file/{filename}", 
                         response_class=FileResponse, 
                         summary="Download a PNM file by filename",
                         responses=FAST_API_RESPONSE,)
        def download_file_via_filename(filename: PathLike = Path(..., description="Filename of the PNM file")):
            """
            **Download PNM Measurement File by Filename**

            Download a previously uploaded PNM measurement files using its associated filename.

            [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/docs/api/fast-api/file_manager/file-manager.md#-download-file-by-transaction)
            """
            return PnmFileService().get_file_by_filename(filename)

        @self.router.post("/upload", 
                          response_model=UploadFileResponse, 
                          summary="Upload A PNM File",
                          responses=FAST_API_RESPONSE,)
        async def upload_file(file: UploadFile = File(..., description="PNM binary file to upload"),
                              filename: FileNameStr = Form(..., description="Filename to assign to the uploaded PNM binary")):
            """
            **Upload A Raw PNM Measurement File**

            Accepts a user-provided PNM binary payload plus a target filename,
            stores the file in a temporary upload directory, inspects its
            header to determine the PNM test type, and registers a new
            transaction in the PyPNM file database.

            Returns:
            - `PushFileResponse` containing the filename and newly assigned
              transaction ID.

            Usage (SwaggerUI):
            - Select a file in the `file` field.
            - Provide a desired `filename`.
            - Execute the request to register the upload.
            """
            content = await file.read()

            request = UploadFileRequest(
                filename = filename,
                data     = content,
            )

            result = PnmFileService().upload_file(request)
            return JSONResponse(content=result.model_dump())

        @self.router.post("/getAnalysis", 
                          response_model=UploadFileResponse,  
                          summary="Analyze a PNM File",
                          responses=FAST_API_RESPONSE,)
        def get_analysis(file: UploadFile = File(..., description="PNM binary file to upload"),
                         filename: FileNameStr = Form(..., description="Filename to assign to the uploaded PNM binary")):
            """
            **Trigger Automated Analysis of a PNM File**

            Launches an analysis routine based on the specified file and test type.
            Performs a basic analysis and returns structured results.

            Supports analysis types such as:
            - RxMER per subcarrier
            - Channel estimation
            - Pre-equalization taps
            - Spectrum snapshots

            Returns:
            - Analysis results in JSON format
            - Key performance metrics
            - CSV data for further processing
            - Matplotlib plots 

            🔗 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/file_manager/file-manager.md#-trigger-file-analysis)
            """
            result = PnmFileService().get_analysis(request)
            return JSONResponse(content=result.model_dump())


# Required for auto-discovery via dynamic router loading
router = PnmFileManager().router
