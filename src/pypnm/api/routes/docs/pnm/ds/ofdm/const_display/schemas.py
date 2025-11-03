
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmDataResponse, PnmRequest, PnmAnalysisRequest, PnmSingleCaptureRequest
from pypnm.docsis.data_type.DsCmConstDisplay import CmDsConstellationDisplayConst as ConsDisplaConstant

class ConstellationDisplaySettings(BaseModel):
    modulation_order_offset:int = Field(default=ConsDisplaConstant.MODULATION_OFFSET.value, description="")
    number_sample_symbol:int    = Field(default=ConsDisplaConstant.NUM_SAMPLE_SYMBOL.value, description="")    

class PnmConstellationDisplayAnalysisRequest(PnmSingleCaptureRequest):
    """Generic response container for most PNM operations."""
    capture_settings:ConstellationDisplaySettings

class PnmConstellationDisplayRequest(PnmRequest):
    """Request model used to trigger measurement-related operations on a cable modem."""
    capture_settings:ConstellationDisplaySettings

class PnmConstellationDisplayResponse(PnmDataResponse):
    """Generic response container for most PNM operations."""


