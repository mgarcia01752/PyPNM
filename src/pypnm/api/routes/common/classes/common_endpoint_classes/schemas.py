# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, Optional
from pydantic import Field, field_validator
from api.routes.common.classes.common_endpoint_classes.common_req_resp import CommonAnalysisRequest, CommonRequest, CommonResponse

class PnmRequest(CommonRequest):
    """Request model used to trigger measurement-related operations on a cable modem."""
    pass

class PnmResponse(CommonResponse):
    """Generic response container for most PNM operations."""
    data: Optional[bytes | str | None] = Field(
        default=None,
        description="Raw or structured data resulting from the operation (e.g., text, JSON, or binary)."
    )

class PnmFileRequest(CommonRequest):
    """Request model used when the operation requires access to a specific PNM file."""
    file_name: str = Field(..., description="Name of the file associated with the MAC address.")
    transaction_id: Optional[str] = Field(
        default=None,
        description="Optional transaction identifier to track file operations or correlate requests."
    )

class PnmChannelEntryResponse(CommonResponse):
    """Response model containing detailed OFDM or OFDMA channel entry data."""
    index: int = Field(default=0, description="Index in the channel table (e.g., OFDM/OFDMA channel number).")
    channel_id: int = Field(default=0, description="Logical channel ID assigned by the CMTS.")
    entry: Dict[str, Any] = Field(default={}, description="Dictionary of all fields for this channel entry.")

class PnmFileResponse(CommonResponse):
    """Response model for file-related operations, such as retrieving or listing PNM files."""
    file_name: str = Field(..., description="Name of the PNM-related file returned by the operation.")
    data: Optional[bytes | str | Any] = Field(
        default=None,
        description="Contents of the file or relevant metadata (could be binary or string)."
    )

class PnmAnalysisResponse(CommonResponse):
    """Response model that contains data structured for plotting PNM metrics."""
    data: Dict[Any, Any] = Field(
        ..., 
        description="Structured data (e.g., series of x/y points or histogram bins) used to generate plots."
    )
    
class PnmAnalysisRequest(CommonAnalysisRequest):
    """Request model that contains data structured for plotting PNM metrics."""

class PnmDataResponse(CommonResponse):
    """Flexible response container for PNM operations returning generic dictionary data."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of key-value data returned from the PNM operation."
    )

class PnmMeasurementResponse(CommonResponse):
    """Response model used for returning measurement values collected from the modem."""
    measurement: Dict[Any, Any] = Field(
        default_factory=dict,
        description="Raw or structured data resulting from the operation (e.g., text, JSON, or binary)."
    )
    
    @field_validator("measurement", mode="before")
    def wrap_measurement_in_key(cls, v):
        """
        Ensures that if the input is not a dictionary, it gets wrapped under a 'data' key.
        """
        if isinstance(v, dict):
            return v
        return {"data": v}
    