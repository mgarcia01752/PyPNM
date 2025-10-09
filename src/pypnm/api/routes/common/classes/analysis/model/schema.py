# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

# Author: Maurice Garcia (2025)

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from pypnm.lib.mac_address import MacAddress
from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.signal_processing.shan.series import ShannonSeriesModel
from pypnm.lib.types import ComplexArray, FloatSeries, FloatSeries
from pypnm.pnm.lib.signal_statistics import SignalStatisticsModel

class BaseAnalysisModel(BaseModel):
    device_details: Mapping[str, Any]   = Field(default_factory=dict, description="Device Details SysDescr")
    pnm_header: Mapping[str, Any]       = Field(default_factory=dict, description="PNM metadata header as a free-form mapping.")
    mac_address: str                    = Field(default=MacAddress.null(), description="CPE MAC address (string).")
    channel_id: int                     = Field(default=INVALID_CHANNEL_ID, description="Upstream/downstream channel identifier.")

class GrpDelayStatsModel(BaseModel):
    group_delay_unit : str         = Field(..., description="Unit of group delay values (e.g., microseconds).")
    magnitude        : FloatSeries = Field(..., description="Per-subcarrier group delay values in specified units.")


class ComplexDataCarrierModel(BaseModel):
    carrier_count             : int              = Field(..., description="Total number of active subcarriers included in the estimation.")
    frequency_unit            : str              = Field(default="Hz", description="Unit of the frequency axis (default: Hertz).")
    frequency                 : FloatSeries        = Field(..., description="List of subcarrier center frequencies.")
    complex                   : ComplexArray     = Field(..., description="Raw complex channel estimation coefficients as [real, imag] pairs.")
    complex_dimension         : int              = Field(..., description="Dimensionality of the complex array (should be 1 for per-carrier sequence).")
    magnitudes                : FloatSeries      = Field(..., description="Per-subcarrier magnitude response in linear scale.")
    group_delay               : GrpDelayStatsModel  = Field(..., description="Group delay analysis results for the channel estimate.")
    occupied_channel_bandwidth: int              = Field(..., description="Occupied channel bandwidth in Hertz.")


class ComplexDataAnalysisModel(BaseAnalysisModel):
    subcarrier_spacing           : int                        = Field(..., description="Subcarrier frequency spacing in Hertz.")
    first_active_subcarrier_index: int                        = Field(..., description="Index of the first active OFDM subcarrier (0-based).")
    subcarrier_zero_frequency    : int                        = Field(..., description="Absolute frequency of subcarrier k=0 in Hertz.")
    carrier_values               : ComplexDataCarrierModel    = Field(..., description="Detailed per-subcarrier results.")
    signal_statistics            : SignalStatisticsModel      = Field(..., description="Computed time-domain statistics of the channel estimate signal.")


class RegressionModel(BaseModel):
    slope:FloatSeries                   = Field(..., description="")

class ConstellationDisplayAnalysisModel(BaseAnalysisModel):
    """Canonical payload for a constellation display dataset. Use `from_measurement(...)` to build from a raw measurement dict."""

    model_config = ConfigDict(populate_by_name=True)
    num_sample_symbols: Optional[int]           = Field(default=None, ge=0, description="Number of constellation symbols captured.")
    modulation_order: Optional[QamModulation]   = Field(default=QamModulation.UNKNOWN, description="Modulation order (e.g., 16, 64, 256).")
    complex_unit: Literal["[Real, Imaginary]"]  = Field(default="[Real, Imaginary]", description="Units for the complex pairs (I=Real, Q=Imaginary).")
    soft: ComplexArray                          = Field(default=[(0,0)], description="IQ soft decisions as (real, imag) float pairs.")
    hard: ComplexArray                          = Field(default=[(0,0)], description="IQ hard decisions as (real, imag) float pairs.")

class DsHistogramAnalysisModel(BaseAnalysisModel):
    """Canonical payload for a **Downstream Histogram** measurement in PyPNM.

    This model represents pre-binned counts produced by a CM/PNM capture. Each entry of
    `hit_counts[i]` is the number of observations that fell into bin *i*; the implicit x-axis
    is therefore the bin index range ``0..len(hit_counts)-1``. Any vendor-/device-specific
    metadata may be carried in `device_details` and `pnm_header` without strict schema.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    symmetry: int             = Field(..., description="Histogram symmetry flag as reported by the device (implementation- or vendor-defined).")
    dwell_count: FloatSeries    = Field(..., description="Measurement dwell/accumulation count used when collecting the histogram.")
    hit_counts: FloatSeries     = Field(..., description="Per-bin hit counts; index i corresponds to bin i. Length equals number of bins.")

class FecSummaryCodeWordModel(BaseModel):
    """Vectorized FEC codeword summary for a single OFDM profile.

    Each list is aligned by index: ``timestamp[i]`` corresponds to
    ``total_codewords[i]``, ``corrected[i]``, and ``uncorrected[i]``.
    """
    model_config                = ConfigDict(populate_by_name=True, extra="ignore")
    timestamps: List[int]       = Field(default_factory=list, description="Epoch timestamps (seconds) per codeword sample.")
    total_codewords: List[int]  = Field(default_factory=list, description="Total codewords observed per timestamp.")
    corrected: List[int]        = Field(default_factory=list, description="Corrected codewords per timestamp.")
    uncorrected: List[int]      = Field(default_factory=list, description="Uncorrectable codewords per timestamp.")

class OfdmFecSummaryProfileModel(BaseModel):
    """Per-profile summary bundle: metadata + vectorized codeword series."""
    model_config                        = ConfigDict(populate_by_name=True, extra="ignore")
    profile: int                        = Field(..., description="OFDM profile identifier (e.g., 0..15).")
    number_of_sets: int                 = Field(..., description="Number of codeword entry sets reported for this profile.")
    codewords: FecSummaryCodeWordModel  = Field(..., description="Vectorized codeword time-series for the profile.")

class OfdmFecSummaryAnalysisModel(BaseAnalysisModel):
    """Top-level DS OFDM FEC summary analysis payload.

    Inherits common analysis fields from ``BaseAnalysisModel`` (e.g., ``device_details``,
    ``pnm_header``, ``mac_address``, ``channel_id``) and carries a list of per-profile
    summaries in ``profiles``.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    profiles: List[OfdmFecSummaryProfileModel] = Field(default_factory=list, description="All per-profile FEC summaries for the channel.")

class RxMerCarrierValuesModel(BaseModel):
    carrier_status_map:Dict[str,Any]    = Field(..., description="")
    magnitude_unit: str                 = Field(default="dB", description="")
    frequency_unit: str                 = Field(default="Hz", description="")    
    carrier_count: int                  = Field(..., description="")
    magnitude: FloatSeries              = Field(..., description="")
    frequency: FloatSeries                = Field(..., description="")
    carrier_status:FloatSeries            = Field(..., description="")

class DsRxMerAnalysisModel(BaseAnalysisModel):
    subcarrier_spacing:int                      = Field(..., description="")
    first_active_subcarrier_index:int           = Field(..., description="")
    subcarrier_zero_frequency:int               = Field(..., description="")           
    carrier_values: RxMerCarrierValuesModel     = Field(..., description="")
    regression: RegressionModel                 = Field(..., description="")
    modulation_statistics:ShannonSeriesModel    = Field(..., description="")

class OfdmaUsPreEqCarrierModel(ComplexDataCarrierModel):
    """"""

class UsOfdmaUsPreEqAnalysisModel(ComplexDataAnalysisModel):
    """"""
