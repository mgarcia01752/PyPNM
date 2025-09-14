
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from pypnm.api.routes.advance.common.schema.common_captuer_schema import MultiCaptureRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.common_req_resp import (
    CommonAnalysisResponse, CommonAnalysisType, CommonMultiAnalysisRequest, CommonResponse)

from enum import IntEnum

class MeasureModes(IntEnum):
    CONTINUOUS          = 0   
    OFDM_PERFORMANCE_1  = 1
    
class MeasureParameters(BaseModel):
    mode:MeasureModes

class MultiRxMerRequest(MultiCaptureRequest):
    measure:MeasureParameters

class MultiRxMerResponseStatus(BaseModel):
    """
    Details about a Multi-RxMER capture operation’s current state.
    """
    operation_id: str = Field(
        ...,
        description="Unique identifier for this multi-RxMER operation."
    )
    state: str = Field(
        ...,
        description="Current state of the operation (e.g., 'running', 'completed', 'stopped')."
    )
    collected: int = Field(
        ...,
        description="Number of RxMER samples collected so far."
    )
    time_remaining: int = Field(
        ...,
        description="Measure time remaining in seconds."
    )
    message: Optional[str] = Field(
        None,
        description="Optional human-readable message or error detail."
    )

class MultiRxMerResponse(CommonResponse):
    """
    Standard wrapper for Multi-RxMER operation responses.

    Inherits:
      - `mac_address` (str)
      - `status`   (success|error)
      - `message`  (overall error or info)

    Adds:
      - `operation` for the nested operation-status details.
    """
    operation: MultiRxMerResponseStatus = Field(
        ...,
        description="Nested object describing the multi-RxMER operation status."
    )

class MultiRxMerResultsResponse(CommonResponse):
    """
    Returns the final list of capture samples for a completed or in-progress operation.
    """
    samples: List[Dict] = Field(
        ...,
        description="Timestamped transaction info for each RxMER capture iteration."
    )

class MultiRxMerStartResponse(CommonResponse):
    """
    Response returned when a multi-RxMER capture is kicked off.

    Inherits:
      - mac_address  (echoed back)
      - status       ("success" or "error")
      - message      (optional error/info)

    Adds:
      - operation_id: Unique identifier for the background capture session.
    """
    group_id: str = Field(..., description="Capture group ID for this session")
    operation_id: str = Field(..., description="Operation ID to query status/results")

class MultiRxMerStatusResponse(CommonResponse):
    """
    Response schema for checking the status of a Multi-RxMER capture operation.

    Inherits:
        mac_address (str): 
            The target cable modem’s MAC address, echoed from the request.
        status (Literal["success", "error"]):
            Overall HTTP-level outcome of this call.
        message (Optional[str]):
            Optional informational or error message at the call level.

    Adds:
        operation (MultiRxMerResponseStatus):
            Detailed operation-level result, including:
            
            - operation_id (str):
                The 16-hex ID for this capture session.
            - state (OperationState):
                Current capture state: RUNNING, STOPPED, COMPLETED, or UNKNOWN.
            - collected (int):
                Number of `CaptureSample`s successfully gathered so far.
            - message (Optional[str]):
                Optional operation-specific message or warning.

    Example:
    ```json
    {
        "mac_address": "00:11:22:33:44:55",
        "status": "success",
        "message": null,
        "operation": {
            "operation_id": "abcd1234efgh5678",
            "state": "RUNNING",
            "collected": 5,
            "message": null
        }
    }
    ```
    """
    operation: MultiRxMerResponseStatus = Field(
        ...,
        description=(
            "Detailed operation-level state and sample count:\n"
            "- `operation_id`: capture run ID\n"
            "- `state`: RUNNING|STOPPED|COMPLETED|UNKNOWN\n"
            "- `collected`: number of samples so far\n"
            "- `message`: optional per-operation message"
        )
    )

class MultiRxMerAnalysisRequest(BaseModel):
    analysis: CommonAnalysisType    = Field(..., description="Operation ID to query status/results")
    operation_id: str               = Field(..., description="Operation ID to query status/results")

class MultiRxMerAnalysisResponse(CommonAnalysisResponse):
    """
    Response schema for Multi-RxMER signal analysis, keyed by channel ID.
    """
    data: Dict[int, Dict[str, Any]] = Field(
        ...,
        description=(
            "Mapping from channel_id to its analysis results "
            "(frequency, min, avg, max lists)."
        )
    )

