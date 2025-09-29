
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional

from pydantic import BaseModel, Field
from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_connect_request import BaseDeviceConnectRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_response import BaseDeviceResponse
from pypnm.docsis.data_type.sysDescr import SystemDescriptorModel

class CaptureParameters(BaseModel):
    """
    Parameters controlling a multi-sample RxMER capture operation.
    """
    measurement_duration: int = Field(
        ...,
        ge=1,
        description="Total duration (in seconds) over which to collect RxMER samples."
    )
    sample_interval: int = Field(
        ...,
        ge=1,
        description="Time interval (in seconds) between successive RxMER captures."
    )

class MultiCaptureParametersRequest(BaseModel):
    parameters: CaptureParameters

class MultiCaptureRequest(BaseDeviceConnectRequest):
    capture:MultiCaptureParametersRequest

class MultiCaptureParametersResponse(BaseDeviceResponse):    
    """
    Details about a multi-capture operation’s current state.
    """
    operation_id: str = Field(
        ...,
        description="Unique identifier for this mult-capture operation."
    )
    state: str = Field(
        ...,
        description="Current state of the operation (e.g., 'running', 'completed', 'stopped')."
    )
    collected: int = Field(
        ...,
        description="Number of samples collected so far."
    )
    time_remaining: int = Field(
        ...,
        description="Measure time remaining in seconds."
    )
    message: Optional[str] = Field(
        default="",
        description="Optional human-readable message or error detail."
    )