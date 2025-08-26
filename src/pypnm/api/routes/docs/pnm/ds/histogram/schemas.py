# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import Field
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmMeasurementResponse, PnmRequest

class PnmHistogramRequest(PnmRequest):
    """Request model used to trigger measurement-related operations on a cable modem."""
    sample_duration:int = Field(
        default=10, description="Histogram Sample Duration in seconds"
    )

class PnmHistogramResponse(PnmMeasurementResponse):
    """Generic response container for most PNM operations."""

class PnmHistogramAnalysisRequest(PnmAnalysisRequest):
    sample_duration:int = Field(
        default=10, description="Histogram Sample Duration in seconds"
    )
