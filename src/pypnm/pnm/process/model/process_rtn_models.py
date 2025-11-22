
from __future__ import annotations
from typing import Any, Dict, Literal

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import FrequencyHz, ComplexArray, MacAddressStr, IntSeries, FloatSeries, FrequencySeriesHz
from pydantic import Field, BaseModel, ConfigDict, field_serializer
from pypnm.pnm.lib.signal_statistics import SignalStatisticsModel
from pypnm.pnm.process.CmSpectrumAnalysisSnmp import SpecAnalysisSnmpConfigModel
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeaderParameters


class CmDsOfdmChanEstimateCoefModel(PnmBaseModel):
    """
    Canonical payload for DOCSIS OFDM downstream channel-estimation coefficients.

    Notes
    -----
    - `value_units` is fixed to "complex".
    - `data_length` is the byte length of the coefficient payload (2 bytes real + 2 bytes imag per subcarrier).
    - Number of complex points = `data_length // 4`.
    - `occupied_channel_bandwidth` = (#points) * subcarrier_spacing (Hz).
    """
    data_length: int                        = Field(..., ge=0, description="Coefficient payload length (bytes)")
    occupied_channel_bandwidth: FrequencyHz = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units: str                        = Field(default="complex", description="Non-mutable")
    values: ComplexArray                    = Field(..., description="Per-subcarrier [real, imag] pairs")

class CmDsHistModel(BaseModel):
    pnm_header:PnmHeaderParameters  = Field(..., description="")
    mac_address:MacAddressStr       = Field(default=MacAddress.null(), description="Device MAC address")
    symmetry: int                   = Field(..., description="Histogram symmetry indicator (device-specific meaning).")
    dwell_count_values_length: int  = Field(..., description="Number of dwell count entries reported.")
    dwell_count_values: IntSeries   = Field(..., description="Dwell count values per bin.")
    hit_count_values_length: int    = Field(..., description="Number of hit count entries reported.")
    hit_count_values: IntSeries     = Field(..., description="Hit count values per bin.")

class CmDsConstDispMeasModel(PnmBaseModel):
    actual_modulation_order: int    = Field(..., ge=0, description="")
    num_sample_symbols: int         = Field(..., ge=0, description="Number of constellation soft-decision symbol samples")
    sample_length: int              = Field(..., ge=0, description="Number of constellation soft-decision complex pairs")
    sample_units: str               = Field(default="[Real(I), Imaginary(Q)]", description="Non-mutable")
    samples: ComplexArray           = Field(..., description="Constellation soft-decision samples")

class CmDsOfdmRxMerModel(PnmBaseModel):
    data_length: int                        = Field(..., ge=0, description="Number of RxMER points (subcarriers)")
    occupied_channel_bandwidth: FrequencyHz = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units:str                         = Field(default="dB", description="Non-mutable")
    values:FloatSeries                      = Field(..., description="RxMER values per active subcarrier (dB)")
    signal_statistics:SignalStatisticsModel = Field(..., description="Aggregate statistics computed from values")
    modulation_statistics:Dict[str, Any]    = Field(..., description="Shannon-based modulation metrics")

class CmUsOfdmaPreEqModel(PnmBaseModel):
    model_config                            = ConfigDict(extra="ignore")
    cmts_mac_address: MacAddressStr         = Field(..., description="CMTS MAC address associated with this measurement.")
    value_length: int                       = Field(..., ge=0, description="Number of complex coefficient pairs (non-negative).")
    value_unit: Literal["[Real, Imaginary]"] = Field("[Real, Imaginary]", description="Unit representation of complex values.")
    values: ComplexArray                    = Field(..., min_length=1, description="Pre-equalization coefficients as [real, imaginary] pairs.")
    occupied_channel_bandwidth: FrequencyHz = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")

class CmSpectrumAnalysisSnmpModel(BaseModel):
    """
    Canonical payload for SNMP-based CM Spectrum Analysis amplitude results.

    This model aggregates the flattened frequency and amplitude vectors across
    all parsed spectrum groups along with the associated configuration header
    and the raw amplitude bytes.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True, ser_json_bytes="base64")
    spectrum_config: SpecAnalysisSnmpConfigModel = Field(..., description="Spectrum configuration header derived from the first parsed spectrum group.")
    pnm_file_type: str              = Field(default=PnmFileType.CM_SPECTRUM_ANALYSIS_SNMP_AMP_DATA.name, description="(Special Case) PNM file type identifier.")
    total_samples: int              = Field(..., ge=0, description="Total number of amplitude samples parsed across all spectrum groups.")
    frequency: FrequencySeriesHz    = Field(..., description="Flattened frequency bin values in Hz across all spectrum groups.")
    amplitude: FloatSeries          = Field(..., description="Flattened amplitude values in dBmV corresponding to each frequency bin.")
    amplitude_bytes: bytes          = Field(..., description="Raw concatenated amplitude bytes across all parsed spectrum groups.")

    @field_serializer("amplitude_bytes")
    def _ser_amplitude_bytes(self, value: bytes, _info) -> str:
        return value.hex()
