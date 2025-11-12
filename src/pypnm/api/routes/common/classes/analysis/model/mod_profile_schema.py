
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Annotated, List, Literal, Union
from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.common.classes.analysis.model.schema import BaseAnalysisModel
from pypnm.lib.types import FloatSeries, FrequencyHz, FrequencySeriesHz, ProfileId


class CarrierItemModel(BaseModel):
    """Per-carrier record."""
    frequency: FrequencyHz       = Field(..., description="Carrier center frequency (Hz)")
    modulation: str              = Field(..., description="Modulation-Order-Type (e.g., 'qam_256', 'plc', 'exclusion')")
    shannon_min_mer: float       = Field(..., description="Minimum supported Shannon MER (dB) for the modulation")

class CarrierValuesSplitModel(BaseModel):
    """Parallel-array layout (compact, vector-friendly)."""
    layout: Literal["split"]     = Field("split", description="Layout discriminator")
    frequency: FrequencySeriesHz = Field(default_factory=list, description="Frequencies (Hz)")
    modulation: List[str]        = Field(default_factory=list, description="Per-carrier modulation names")
    shannon_min_mer: FloatSeries = Field(default_factory=list, description="Per-carrier Shannon minimum MER (dB)")

class CarrierValuesListModel(BaseModel):
    """Verbose list layout (easier for debugging/logging)."""
    layout: Literal["list"]      = Field("list", description="Layout discriminator")
    carriers: List[CarrierItemModel] = Field(default_factory=list, description="Per-carrier records")

CarrierValuesModel = Annotated[
    Union[CarrierValuesSplitModel, CarrierValuesListModel],
    Field(discriminator="layout")
]

class ProfileAnalysisEntryModel(BaseModel):
    """Per-profile container of carrier values."""
    profile_id: ProfileId                   = Field(..., ge=0, description="Profile identifier")
    carrier_values: CarrierValuesModel

class DsModulationProfileAnalysisModel(BaseAnalysisModel):
    """
    Downstream OFDM Modulation Profile analysis result.

    Inherits header fields from BaseAnalysisModel:
      - device_details, pnm_header, mac_address, channel_id.

    The `profiles[*].carrier_values` field is a discriminated union:
      * layout='split'  → `CarrierValuesSplitModel` (parallel arrays)
      * layout='list'   → `CarrierValuesListModel`  (explicit records)
    """
    model_config = ConfigDict(extra="ignore")

    frequency_unit: Literal["Hz"]     = Field("Hz", description="Frequency unit")
    shannon_min_unit: Literal["dB"]   = Field("dB", description="Shannon minimum MER unit")
    profiles: List[ProfileAnalysisEntryModel] = Field(default_factory=list, description="Per-profile results")
