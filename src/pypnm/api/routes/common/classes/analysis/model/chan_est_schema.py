# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from pydantic import BaseModel, Field
from pypnm.api.routes.common.classes.analysis.model.schema import BaseAnalysisModel
from pypnm.lib.types import ComplexArray, FloatSeries, IntSeries
from pypnm.pnm.lib.signal_statistics import SignalStatisticsModel


class GroupDelayStats(BaseModel):
    group_delay_unit : str         = Field(..., description="Unit of group delay values (e.g., microseconds).")
    magnitude        : FloatSeries = Field(..., description="Per-subcarrier group delay values in specified units.")


class ChanEstCarrierModel(BaseModel):
    carrier_count             : int          = Field(..., description="Total number of active subcarriers included in the estimation.")
    frequency_unit            : str          = Field(default="Hz", description="Unit of the frequency axis (default: Hertz).")
    frequency                 : IntSeries    = Field(..., description="List of subcarrier center frequencies.")
    complex                   : ComplexArray = Field(..., description="Raw complex channel estimation coefficients as [real, imag] pairs.")
    complex_dimension         : int          = Field(..., description="Dimensionality of the complex array (should be 1 for per-carrier sequence).")
    magnitudes                : FloatSeries  = Field(..., description="Per-subcarrier magnitude response in linear scale.")
    group_delay               : GroupDelayStats = Field(..., description="Group delay analysis results for the channel estimate.")
    occupied_channel_bandwidth: int          = Field(..., description="Occupied channel bandwidth in Hertz.")


class DsChannelEstAnalysisModel(BaseAnalysisModel):
    subcarrier_spacing         : int                    = Field(..., description="Subcarrier frequency spacing in Hertz.")
    first_active_subcarrier_index: int                  = Field(..., description="Index of the first active OFDM subcarrier (0-based).")
    subcarrier_zero_frequency  : int                    = Field(..., description="Absolute frequency of subcarrier k=0 in Hertz.")
    carrier_values             : ChanEstCarrierModel    = Field(..., description="Detailed per-subcarrier channel estimation results.")
    signal_statistics          : SignalStatisticsModel  = Field(..., description="Computed time-domain statistics of the channel estimate signal.")
