# SPDX-License-Identifier: MIT
# Author: Maurice Garcia (2025)

from __future__ import annotations

from typing import Any, Mapping, Optional, Literal
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
