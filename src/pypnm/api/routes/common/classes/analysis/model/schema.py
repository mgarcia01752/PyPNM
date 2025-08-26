# SPDX-License-Identifier: MIT
# Author: Maurice Garcia (2025)

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from pypnm.lib.qam.types import QamModulation
from pypnm.lib.types import ComplexArray

class ConstellationDisplayAnalysisModel(BaseModel):
    """Canonical payload for a constellation display dataset. Use `from_measurement(...)` to build from a raw measurement dict."""

    model_config = ConfigDict(populate_by_name=True)
    device_details: Mapping[str, Any]           = Field(default_factory=dict, description="Device Details SysDescr")
    pnm_header: Mapping[str, Any]               = Field(default_factory=dict, description="PNM metadata header as a free-form mapping.")
    mac_address: Optional[str]                  = Field(default=None, description="CPE MAC address (string).")
    channel_id: Optional[int]                   = Field(default=None, description="Upstream/downstream channel identifier.")
    num_sample_symbols: Optional[int]           = Field(default=None, ge=0, description="Number of constellation symbols captured.")
    modulation_order: Optional[QamModulation]   = Field(default=QamModulation.UNKNOWN, description="Modulation order (e.g., 16, 64, 256).")
    complex_unit: Literal["[Real, Imaginary]"]  = Field(default="[Real, Imaginary]", description="Units for the complex pairs (I=Real, Q=Imaginary).")
    soft: ComplexArray                          = Field(default_factory=list, validation_alias="complex", serialization_alias="complex", description="IQ soft decisions as (real, imag) float pairs.")
    hard: ComplexArray                          = Field(default_factory=list, validation_alias="complex", serialization_alias="complex", description="IQ hard decisions as (real, imag) float pairs.")

class DsHistogramAnalysisModel(BaseModel):
    """Canonical payload for a **Downstream Histogram** measurement in PyPNM.

    This model represents pre-binned counts produced by a CM/PNM capture. Each entry of
    `hit_counts[i]` is the number of observations that fell into bin *i*; the implicit x-axis
    is therefore the bin index range ``0..len(hit_counts)-1``. Any vendor-/device-specific
    metadata may be carried in `device_details` and `pnm_header` without strict schema.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    device_details: Mapping[str, Any]   = Field(default_factory=dict, description="Free-form device metadata (e.g., sysDescr, sysObjectID, vendor/model).")
    pnm_header: Mapping[str, Any]       = Field(default_factory=dict, description="PNM capture metadata (e.g., timestamps, capture_id, source, units).")
    mac_address: Optional[str]          = Field(..., description="Cable modem MAC address, colon-delimited (e.g., 'aa:bb:cc:dd:ee:ff').")
    channel_id: Optional[int]           = Field(..., description="Downstream channel ID (docsIfDownChannelId).")
    symmetry: Optional[int]             = Field(..., description="Histogram symmetry flag as reported by the device (implementation- or vendor-defined).")
    dwell_count: Optional[int]          = Field(..., description="Measurement dwell/accumulation count used when collecting the histogram.")
    hit_counts: Optional[List[int]]     = Field(..., description="Per-bin hit counts; index i corresponds to bin i. Length equals number of bins.")
