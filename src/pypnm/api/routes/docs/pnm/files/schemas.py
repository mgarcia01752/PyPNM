from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from typing import Dict, Optional, List

from pypnm.api.routes.common.classes.file_capture.types import TransactionId, TransactionRecordModel
from pypnm.lib.types import MacAddressStr, PathLike


class FileQueryRequest(BaseModel):
    '''Base Model'''
    mac_address: MacAddressStr = Field(..., description="MAC address of the cable modem")


class FileQueryResponse(BaseModel):
    files: Dict[str, List[TransactionRecordModel]] = Field(description="Mapping of MAC address to list of PNM file entries",)


class UploadFileRequest(FileQueryRequest):
    filename: PathLike          = Field(..., description="Name of the file to push into the temporary upload area")
    data: Optional[bytes]       = Field(None, description="Raw PNM binary payload to persist for later analysis")


class UploadFileResponse(FileQueryRequest):
    filename: PathLike              = Field(..., description="Name of the file that was registered")
    transaction_id: TransactionId   = Field(..., description="Unique transaction identifier for the uploaded file")


class FileAnalysisRequest(FileQueryRequest):
    transaction_id: TransactionId = Field(..., description="transaction id from file search")
    analysis_type: Optional[str]  = Field(default="auto", description="Type of analysis: spectrum, rxmer, etc.")


class AnalysisResponse(BaseModel):
    analysis_type: str
    plot_url: str  # Or raw data if not generating a URL
    summary: Optional[str] = None
