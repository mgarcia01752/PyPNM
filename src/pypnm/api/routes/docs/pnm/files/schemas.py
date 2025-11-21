from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


from pypnm.api.routes.common.classes.common_endpoint_classes.common_req_resp import CommonFileSearchRequest
from pypnm.api.routes.common.classes.file_capture.types import TransactionId
from pypnm.lib.types import FileName, TimeStamp


class FileQueryRequest(CommonFileSearchRequest):
    """Base request model for querying PNM files (inherits MAC/IP/etc. from CommonFileRequest)."""
    pass


class FileEntry(BaseModel):
    transaction_id: TransactionId           = Field(..., description="Unique identifier for this file transaction")
    filename: FileName                      = Field(..., description="Name of the file")
    pnm_test_type: str                      = Field(..., description="Type of PNM test performed")
    timestamp: TimeStamp                    = Field(..., description="Capture or transaction timestamp")
    system_description: Optional[dict]      = Field(None, description="Optional system description metadata")


class FileQueryResponse(BaseModel):
    files: Dict[str, List[FileEntry]]       = Field(..., description="Mapping of MAC address to list of PNM file entries")


class PushFileRequest(FileQueryRequest):
    filename: FileName                      = Field(..., description="Name of the file to push")
    data: Optional[str]                     = Field(None, description="Optional base64-encoded or raw file data")


class PushFileResponse(FileQueryRequest):
    filename: FileName                      = Field(..., description="Name of the file that was pushed")
    transaction_id: TransactionId           = Field(..., description="Unique identifier for the created file transaction")


class FileAnalysisRequest(FileQueryRequest):
    transaction_id: TransactionId           = Field(..., description="Transaction ID returned from file search")
    analysis_type: Optional[str]            = Field(default="auto", description="Type of analysis to perform (e.g., 'spectrum', 'rxmer', or 'auto').")


class AnalysisResponse(BaseModel):
    analysis_type: str                      = Field(..., description="Resolved analysis type that was performed")
    plot_url: str                           = Field(..., description="URL to rendered plot or visualization resource")
    summary: Optional[str]                  = Field(None, description="Optional human-readable analysis summary")
