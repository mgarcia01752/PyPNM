# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import SpectrumRetrievalType, WindowFunction
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmRequest

class SpectrumAnalyzerParameters(BaseModel):
    inactivity_timeout: int = Field(
        100, description="Timeout in seconds for inactivity during spectrum analysis.")
    first_segment_center_freq: int = Field(
        108_000_000, description="First segment center frequency in Hz.")
    last_segment_center_freq: int = Field(
        1_002_000_000, description="Last segment center frequency in Hz.")
    segment_freq_span: int = Field(
        1_000_000, description="Frequency span of each segment in Hz.")
    num_bins_per_segment: int = Field(
        256, description="Number of FFT bins per segment.")
    noise_bw: int = Field(
        150, description="Equivalent noise bandwidth in kHz.")
    window_function: WindowFunction = Field(
        WindowFunction.HANN,
        description="FFT window function to apply. See WindowFunction enum for options.")
    num_averages: int = Field(
        1, description="Number of averages per segment.")
    spectrum_retrieval_type: SpectrumRetrievalType = Field(
        SpectrumRetrievalType.FILE,
        description="Method of spectrum data retrieval.")

class CmSpectrumAnalyzerRequest(PnmRequest):
    parameters: SpectrumAnalyzerParameters = Field(
        ..., description="Spectrum analysis specification parameters.")

class CmSpecAnaAnalysisRequest(PnmAnalysisRequest):
    parameters: SpectrumAnalyzerParameters = Field(
        ..., description="Spectrum analysis specification parameters.")
