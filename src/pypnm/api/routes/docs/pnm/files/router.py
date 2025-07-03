# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
from fastapi import APIRouter, Path
from fastapi.responses import FileResponse, JSONResponse

from pypnm.api.routes.docs.pnm.files.schemas import (
    FileAnalysisRequest,
    FileQueryResponse,
    FileQueryRequest,
    PushFileRequest,
    PushFileResponse,
    AnalysisResponse
)
from pypnm.api.routes.docs.pnm.files.service import PnmFileService

class PnmFileManager:
    """
    REST API router for managing PNM test files.

    Endpoints:
    - Search files by MAC or criteria
    - Push/upload new test file
    - Analyze an uploaded or retrieved file
    """

    def __init__(self):
        self.router = APIRouter(
            prefix="/docs/pnm/files",
            tags=["PNM File Manager"]
        )
        self._add_routes()

    def _add_routes(self):

        @self.router.post("/searchFiles", response_model=FileQueryResponse, summary="Search for PNM Files")
        def search_files(request: FileQueryRequest):
            """
            Searches and returns all available PNM files associated with the specified MAC address.

            This endpoint queries the transaction registry and groups results by MAC address.
            Each result includes filename, PNM test type, timestamp, and transaction ID.

            Returns:
            
                JSONResponse: A structured response with a dictionary mapping MAC addresses
                            to lists of PNM file metadata entries.
            """
            result = PnmFileService().search_files(request)
            return JSONResponse(content=result.model_dump())

        @self.router.get("/download/{transaction_id}", 
                         response_class=FileResponse, summary="Download a PNM file by transaction ID")
        def download_file(transaction_id: str = Path(..., description="Transaction ID of the file")):
            """
            Downloads the original binary file associated with a given transaction ID.
            """
            return PnmFileService().get_file_by_transaction_id(transaction_id)

        @self.router.post("/upload", response_model=PushFileResponse, summary="Upload a PNM File")
        def push_file(request: PushFileRequest):
            """
            Accepts a file from the user and stores it in the PyPNM file system.
            Registers the file for future analysis or lookup.
            """
            result = PnmFileService().push_file(request)
            return JSONResponse(content=result.model_dump())

        @self.router.post("/getAnalysis", response_model=AnalysisResponse, summary="Analyze a PNM File")
        def get_analysis(request: FileAnalysisRequest):
            """
            Analyzes the provided file and returns structured results
            such as plots, summaries, or decoded telemetry.
            """
            result = PnmFileService().get_analysis(request)
            return JSONResponse(content=result.model_dump())


# Required for auto-discovery via dynamic router loading
router = PnmFileManager().router
