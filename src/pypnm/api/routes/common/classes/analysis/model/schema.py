# SPDX-License-Identifier: MIT
# Author: Maurice Garcia (2025)

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from pypnm.lib.mac_address import MacAddress
from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.types import ComplexArray

class BaseAnalysisModel(BaseModel):
    device_details: Mapping[str, Any]           = Field(default_factory=dict, description="Device Details SysDescr")
    pnm_header: Mapping[str, Any]               = Field(default_factory=dict, description="PNM metadata header as a free-form mapping.")
    mac_address: Optional[str]                  = Field(default=MacAddress.null(), description="CPE MAC address (string).")
    channel_id: Optional[int]                   = Field(default=INVALID_CHANNEL_ID, description="Upstream/downstream channel identifier.")

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
    symmetry: Optional[int]             = Field(..., description="Histogram symmetry flag as reported by the device (implementation- or vendor-defined).")
    dwell_count: Optional[int]          = Field(..., description="Measurement dwell/accumulation count used when collecting the histogram.")
    hit_counts: Optional[List[int]]     = Field(..., description="Per-bin hit counts; index i corresponds to bin i. Length equals number of bins.")

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

