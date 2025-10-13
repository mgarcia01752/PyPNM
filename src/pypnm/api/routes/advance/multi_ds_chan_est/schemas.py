# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from pypnm.api.routes.advance.common.operation_manager import OperationId
from pypnm.api.routes.advance.common.schema.common_capture_schema import (
    MultiCaptureParametersResponse, MultiCaptureRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.common_req_resp import (
    CommonAnalysisResponse, CommonAnalysisType, CommonOutput, CommonResponse)
from pypnm.api.routes.common.classes.file_capture.types import GroupId

class MultiChanEstimationParameters(BaseModel):
    """Parameters controlling a multi-sample ChannelEstimation capture operation."""
    measurement_duration: int   = Field(..., ge=1, description="Total duration (in seconds) over which to collect ChannelEstimation samples.")
    sample_interval: int        = Field(..., ge=1, description="Time interval (in seconds) between successive ChannelEstimation captures.")

class MultiChanEstimationRequest(MultiCaptureRequest): 
    """Request schema for initiating a Multi-ChannelEstimation operation."""
    pass

class MultiChanEstimationResponseStatus(MultiCaptureParametersResponse): 
    """Status details about a Multi-ChannelEstimation capture operation."""
    pass

class MultiChanEstimationResponse(CommonResponse):
    """Standard wrapper for Multi-ChannelEstimation operation responses."""
    operation: MultiChanEstimationResponseStatus = Field(..., description="Nested object describing the multi-ChannelEstimation operation status.")

class MultiChanEstimationResultsResponse(CommonResponse):
    """Returns the final list of capture samples for a completed or in-progress operation."""
    samples: List[Dict] = Field(..., description="Timestamped transaction info for each ChannelEstimation capture iteration.")

class MultiChanEstimationStartResponse(CommonResponse):
    """Response returned when a multi-ChannelEstimation capture is kicked off."""
    group_id: GroupId           = Field(..., description="Capture group ID for this session")
    operation_id: OperationId   = Field(..., description="Operation ID to query status/results")

class MultiChanEstimationStatusResponse(CommonResponse):
    """Response schema for checking the status of a Multi-ChannelEstimation capture operation."""
    operation: MultiChanEstimationResponseStatus = Field(..., description="Detailed operation-level state and sample count (operation_id, state, collected, time_remaining, message).")

class MultiChanEstimationAnalysisRequest(BaseModel):
    """Request schema for performing signal analysis on a completed Multi-ChannelEstimation capture."""
    analysis: CommonAnalysisType    = Field(..., description="Analysis type to perform.")
    output: CommonOutput            = Field(description="Output type: JSON or file.")
    operation_id: OperationId       = Field(..., description="Operation ID to query status/results.")

class AnalysisDataModel(BaseModel):
    """Typed container for analysis output."""
    analysis_type: str              = Field(..., description="Executed analysis type name.")
    results: List[Dict[str, Any]]   = Field(..., description="List of per-channel analysis results (min/avg/max, group delay, anomalies, etc.).")

class MultiChanEstimationAnalysisResponse(CommonAnalysisResponse):
    """Response schema for Multi-ChannelEstimation signal analysis."""
    data: AnalysisDataModel = Field(..., description="Structured analysis result container including the analysis_type and its corresponding per-channel results.")
