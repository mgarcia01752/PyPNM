# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from __future__ import annotations

from pydantic import BaseModel, Field
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmAnalysisResponse
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import SpecAnMovingAvgParameters

class ScQamSpecAna(BaseModel):
    moving_average: SpecAnMovingAvgParameters = Field(..., description="")
    number_of_averges: int                    = Field(default=10, description="Number of samples to calculate the average per-bin")      

class ScQamSpecAnaAnalysisRequest(PnmAnalysisRequest):
    capture_parameters:ScQamSpecAna

class ScQamSpecAnaAnalysisResponse(PnmAnalysisResponse):
    pass