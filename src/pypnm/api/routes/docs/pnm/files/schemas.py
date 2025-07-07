# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from pypnm.api.routes.common.classes.common_endpoint_classes.common_req_resp import CommonFileRequest

class FileQueryRequest(CommonFileRequest):
    '''Base Model'''

class FileEntry(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier for this file transaction")
    filename: str = Field(..., description="Name of the file")
    pnm_test_type: str = Field(..., description="Type of PNM test performed")
    timestamp: str = Field(..., description="Human-readable timestamp")
    sys_descr: Optional[dict] = Field(None, description="System description details")

class FileQueryResponse(BaseModel):
    files: Dict[str, List[FileEntry]] = Field(
        ..., description="Mapping of MAC address to list of PNM file entries"
    )

class PushFileRequest(FileQueryRequest):
    filename: str = Field(..., description="Name of the file to push")
    data: Optional[str] = Field(None, description="Optional base64-encoded or raw file data")

class PushFileResponse(FileQueryRequest):
    filename: str = Field(..., description="Name of the file to push")
    transaction_id: str

class FileAnalysisRequest(FileQueryRequest):
    transaction_id: str = Field(..., description="transaction id from file search")
    analysis_type: Optional[str] = Field(default="auto", description="Type of analysis: spectrum, rxmer, etc.")

class AnalysisResponse(BaseModel):
    analysis_type: str
    plot_url: str  # Or raw data if not generating a URL
    summary: Optional[str] = None
