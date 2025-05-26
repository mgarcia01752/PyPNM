# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from api.routes.advance.common.schema.common_captuer_schema import (
    MultiCaptureParametersResponse, MultiCaptureRequest)
from api.routes.common.classes.common_endpoint_classes.common_req_resp import (
    CommonAnalysisResponse, CommonMultiAnalysisRequest, CommonResponse)

class MultiChanEstimationParameters(BaseModel):
    """
    Parameters controlling a multi-sample ChannelEstimation capture operation.
    """
    measurement_duration: int = Field(
        ...,
        ge=1,
        description="Total duration (in seconds) over which to collect ChannelEstimation samples."
    )
    sample_interval: int = Field(
        ...,
        ge=1,
        description="Time interval (in seconds) between successive ChannelEstimation captures."
    )

class MultiChanEstimationRequest(MultiCaptureRequest):
    """
    """

class MultiChanEstimationResponseStatus(MultiCaptureParametersResponse):
    """
    Details about a Multi-ChannelEstimation capture operation’s current state.
    """

class MultiChanEstimationResponse(CommonResponse):
    """
    Standard wrapper for Multi-ChannelEstimation operation responses.

    Inherits:
      - `mac_address` (str)
      - `status`   (success|error)
      - `message`  (overall error or info)

    Adds:
      - `operation` for the nested operation-status details.
    """
    operation: MultiChanEstimationResponseStatus = Field(
        ...,
        description="Nested object describing the multi-ChannelEstimation operation status."
    )


class MultiChanEstimationResultsResponse(CommonResponse):
    """
    Returns the final list of capture samples for a completed or in-progress operation.
    """
    samples: List[Dict] = Field(
        ...,
        description="Timestamped transaction info for each ChannelEstimation capture iteration."
    )

class MultiChanEstimationStartResponse(CommonResponse):
    """
    Response returned when a multi-ChannelEstimation capture is kicked off.

    Inherits:
      - mac_address  (echoed back)
      - status       ("success" or "error")
      - message      (optional error/info)

    Adds:
      - operation_id: Unique identifier for the background capture session.
    """
    group_id: str = Field(..., description="Capture group ID for this session")
    operation_id: str = Field(..., description="Operation ID to query status/results")


class MultiChanEstimationStatusResponse(CommonResponse):
    """
    Response schema for checking the status of a Multi-ChannelEstimation capture operation.

    Inherits:
        mac_address (str): 
            The target cable modem’s MAC address, echoed from the request.
        status (Literal["success", "error"]):
            Overall HTTP-level outcome of this call.
        message (Optional[str]):
            Optional informational or error message at the call level.

    Adds:
        operation (MultiChannelEstimationResponseStatus):
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
    operation: MultiChanEstimationResponseStatus = Field(
        ...,
        description=(
            "Detailed operation-level state and sample count:\n"
            "- `operation_id`: capture run ID\n"
            "- `state`: RUNNING|STOPPED|COMPLETED|UNKNOWN\n"
            "- `collected`: number of samples so far\n"
            "- `message`: optional per-operation message"
        )
    )


class MultiChanEstimationAnalysisRequest(CommonMultiAnalysisRequest):
    operation_id: str = Field(..., description="Operation ID to query status/results")

class MultiChanEstimationAnalysisResponse(CommonAnalysisResponse):
    """
    Response schema for Multi-ChannelEstimation signal analysis, keyed by channel ID.
    """
    data: Dict[int, Dict[str, Any]] = Field(
        ...,
        description=(
            "Mapping from channel_id to its analysis results "
            "(frequency, min, avg, max lists)."
        )
    )

