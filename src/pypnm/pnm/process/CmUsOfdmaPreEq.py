# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from struct import calcsize, unpack
from typing import Optional, List, Tuple, Dict, Any, cast

from pydantic import ConfigDict, Field

from pypnm.lib.constants import KHZ
from pypnm.lib.types import ComplexArray, ComplexSeries
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


class CmUsOfdmaPreEqModel(PnmBaseModel):
    model_config                   = ConfigDict(extra="ignore")

    cmts_mac_address: str          = Field(..., description="CMTS MAC address associated with this measurement.")
    value_length: int              = Field(..., ge=0, description="Number of complex coefficient pairs (non-negative).")
    value_unit: str                = Field(default="[Real, Imaginary]", description="Unit representation of complex values.")
    values: ComplexArray           = Field(..., min_length=1, description="Pre-equalization coefficients as [real, imaginary] pairs.")


class CmUsOfdmaPreEq(PnmHeader):
    """
    Parses and decodes CM OFDMA Upstream Pre-Equalization data from binary input.

    Produces a validated `CmUsOfdmaPreEqModel` that includes:
      - PNM header fields (via PnmBaseModel)
      - CM/CMTS MAC addresses
      - Channel/frequency metadata (subcarrier 0, first active index, spacing in Hz)
      - Complex pre-equalization coefficients as [real, imag] pairs
    """

    def __init__(self, binary_data: bytes, sm_n_format: Tuple[int, int] = (1, 14)):
        super().__init__(binary_data)
        self.logger                          = logging.getLogger(self.__class__.__name__)

        self._sm_n_format                    = sm_n_format

        self._channel_id                     : int
        self._mac_address                    : str
        self._cmts_mac_address               : str
        self._subcarrier_zero_frequency      : int
        self._first_active_subcarrier_index  : int
        self._subcarrier_spacing_khz         : int
        self._pre_eq_data_length             : int
        self._pre_eq_coefficient_data        : bytes
        self._decoded_coefficients           : ComplexSeries

        self._model                          : CmUsOfdmaPreEqModel

        self.__process()

    def __process(self) -> None:
        """
        Parse header and coefficient block; decode fixed-point complex values; build BaseModel.
        Header format (big-endian):
            >B 6s 6s I H B I
             | |  |  | | | +-- pre-eq data length (bytes)
             | |  |  | | +---- subcarrier spacing (kHz, 1-byte)
             | |  |  | +------ first active subcarrier index (H)
             | |  |  +-------- subcarrier zero frequency (Hz, I)
             | |  +----------- CMTS MAC (6s)
             | +-------------- CM MAC (6s)
             +---------------- upstream channel id (B)
        """
        # Validate file type (allow "last update" variant)
        if (self.get_pnm_file_type() != PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS) and \
           (self.get_pnm_file_type() != PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE):
            expected       = PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS.get_pnm_cann()
            got            = self.get_pnm_file_type().get_pnm_cann()
            raise ValueError(f"PNM File Stream is not file type: {expected}, Error: {got}")

        header_format = ">B6s6sIHB I".replace(" ", "")   # >B6s6sIHB I → >B6s6sIHBI
        header_size   = calcsize(header_format)
        if len(self.pnm_data) < header_size:
            raise ValueError("Insufficient data for CmUsOfdmaPreEq header.")

        (
            self._channel_id,
            cm_mac,
            cmts_mac,
            self._subcarrier_zero_frequency,
            self._first_active_subcarrier_index,
            self._subcarrier_spacing_khz,
            self._pre_eq_data_length,
        ) = unpack(header_format, self.pnm_data[:header_size])

        self._mac_address                  = self._format_mac(cm_mac)
        self._cmts_mac_address             = self._format_mac(cmts_mac)
        self._pre_eq_coefficient_data      = self.pnm_data[header_size:]

        if len(self._pre_eq_coefficient_data) != self._pre_eq_data_length:
            raise ValueError(
                f"Mismatch between reported ({self._pre_eq_data_length}) and actual ({len(self._pre_eq_coefficient_data)}) Pre-EQ data length."
            )

        # Decode fixed-point complex coefficients → List[complex]
        decoded:ComplexSeries = self.process_pre_eq_coefficient_data()
        if not decoded:
            raise ValueError("No pre-equalization coefficients decoded.")

        # Convert to ComplexArray: List[List[float, float]]
        complex_pairs:ComplexArray    = cast(ComplexArray, [[c.real, c.imag] for c in decoded])

        # Build BaseModel (convert spacing to Hz; PnmBaseModel expects Hz)
        self._model                        = CmUsOfdmaPreEqModel(
            pnm_header                     = self.getPnmHeaderParameterModel(),
            channel_id                     = int(self._channel_id),
            mac_address                    = self._mac_address,
            subcarrier_zero_frequency      = int(self._subcarrier_zero_frequency),
            first_active_subcarrier_index  = int(self._first_active_subcarrier_index),
            subcarrier_spacing             = int(int(self._subcarrier_spacing_khz) * KHZ),

            cmts_mac_address               = self._cmts_mac_address,
            value_length                   = int(self._pre_eq_data_length),
            value_unit                     = "[Real, Imaginary]",
            values                         = complex_pairs,
        )

    @staticmethod
    def _format_mac(mac_bytes: bytes) -> str:
        return ":".join(f"{b:02x}" for b in mac_bytes)

    def process_pre_eq_coefficient_data(self) -> ComplexSeries:
        """
        Decode fixed-point complex coefficients using (s,m.n) format.
        """
        if not self._pre_eq_coefficient_data:
            return []

        self._decoded_coefficients         = FixedPointDecoder.decode_complex_data(
            self._pre_eq_coefficient_data,
            self._sm_n_format,
        )
        return self._decoded_coefficients

    def get_coefficients(self) -> ComplexSeries:
        """
        Return previously decoded coefficients if available; otherwise decode on demand.
        """
        if self._decoded_coefficients is not None:
            return self._decoded_coefficients
        return self.process_pre_eq_coefficient_data()

    def to_model(self) -> CmUsOfdmaPreEqModel:
        return self._model

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a plain dictionary via the Pydantic model.
        """
        return self._model.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """
        Convert to a JSON string via the Pydantic model.
        """
        return self._model.model_dump_json(indent=indent)

    def __repr__(self) -> str:
        return f"<CmUsOfdmaPreEq(chid={self._channel_id}, cm={self._mac_address}, cmts={self._cmts_mac_address})>"
