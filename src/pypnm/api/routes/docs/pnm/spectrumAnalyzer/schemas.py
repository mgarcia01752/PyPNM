
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import (
    SpectrumRetrievalType, WindowFunction)
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisRequest, PnmDataResponse, PnmRequest)

class SpecAnMovingAvgParameters(BaseModel):
    window_size:int                                     = Field(..., description="")

class SpecAnCapturePara(BaseModel):
    inactivity_timeout       : int                      = Field(default=100, description="Timeout in seconds for inactivity during spectrum analysis.")
    first_segment_center_freq: int                      = Field(default=108_000_000, description="First segment center frequency in Hz.")
    last_segment_center_freq : int                      = Field(default=1_002_000_000, description="Last segment center frequency in Hz.")
    segment_freq_span        : int                      = Field(default=1_000_000, description="Frequency span of each segment in Hz.")
    num_bins_per_segment     : int                      = Field(default=256, description="Number of FFT bins per segment.")
    noise_bw                 : int                      = Field(default=150, description="Equivalent noise bandwidth in kHz.")
    window_function          : WindowFunction           = Field(default=WindowFunction.HANN, description="FFT window function to apply. See WindowFunction enum for options.")
    num_averages             : int                      = Field(default=1, description="Number of averages per segment.")
    spectrum_retrieval_type  : SpectrumRetrievalType    = Field(default=SpectrumRetrievalType.FILE, description="Method of spectrum data retrieval.")

class SpecAnCaptureParaAnalysis(SpecAnCapturePara):
    moving_average: SpecAnMovingAvgParameters           = Field(..., description="") 

# -------------- REQUEST ------------------
class CmSpecAnaAnalysisRequest(PnmAnalysisRequest):
    capture_parameters: SpecAnCaptureParaAnalysis       = Field(..., description="Spectrum analysis specification parameters.")

class CmSpectrumAnalyzerRequest(PnmRequest):
    parameters: SpecAnCapturePara                       = Field(..., description="Spectrum analyzer capture parameters.")

# -------------- RESPONSE------------------

class CmSpecAnaAnalysisResponse(PnmDataResponse):
    """Generic response container for most PNM operations."""
