from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from struct import calcsize, unpack
from typing import Dict, Optional, Tuple, overload, Literal, Union

from pydantic import Field

from pypnm.api.routes.docs.pnm.files.service import MacAddress
from pypnm.lib.constants import INVALID_CHANNEL_ID, INVALID_SUB_CARRIER_ZERO_FREQ, KHZ
from pypnm.lib.mac_address import MacAddressFormat
from pypnm.lib.types import ChannelId, ComplexArray, ComplexSeries, FrequencyHz, MacAddressStr
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder, FractionalBits, IntegerBits
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


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
    occupied_channel_bandwidth: int         = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units: str                        = Field(default="complex", description="Non-mutable")
    values: ComplexArray                    = Field(..., description="Per-subcarrier [real, imag] pairs")


class CmDsOfdmChanEstimateCoef(PnmHeader):
    """
    Parser/adapter for DOCSIS OFDM Downstream Channel Estimation Coefficients.

    Expected header format (big-endian): '>B6sIHBI'
        B   : channel_id (uint8)
        6s  : mac (6 bytes)
        I   : subcarrier_zero_frequency (Hz, uint32)
        H   : first_active_subcarrier_index (uint16)
        B   : subcarrier_spacing (kHz, uint8; later scaled by KHZ to Hz)
        I   : coefficient payload length (bytes, uint32; multiple of 4)
    """

    def __init__(
        self,
        binary_data: bytes,
        q_format: Tuple[IntegerBits, FractionalBits] = (IntegerBits(2), FractionalBits(13)),
        round_precision: Optional[int] = 6,
    ):
        """
        Parameters
        ----------
        binary_data : bytes
            Raw PNM buffer.
        sm_n_format : Tuple[IntegerBits, FractionalBits]
            Signed-magnitude fixed-point config (integer_bits, fractional_bits).
        round_precision : Optional[int]
            Decimal places to round [real, imag] pairs. If None, no rounding is applied.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._q_format: Tuple[IntegerBits, FractionalBits] = q_format
        self._round_precision: Optional[int] = round_precision

        self._channel_id: ChannelId                  = INVALID_CHANNEL_ID
        self._mac_address: MacAddressStr             = MacAddress.null()
        self._subcarrier_zero_frequency: FrequencyHz = INVALID_SUB_CARRIER_ZERO_FREQ
        self._first_active_subcarrier_index: int     = -1
        self._subcarrier_spacing: int                = -1
        self._coefficient_data_length: int           = -1

        # Raw complex values and rounded pairs (types corrected)
        self._coefficient_data: ComplexSeries = []      # list[complex]
        self._coeff_values_rounded: ComplexArray = []   # list[list[float, float]]

        self._model: CmDsOfdmChanEstimateCoefModel
        self.__process()

    def __process(self) -> None:
        if self.get_pnm_file_type() != PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT:
            cann = PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.get_pnm_cann()
            raise ValueError(
                f"PNM File Stream is not RxMER file type: {cann}, "
                f"Error: {self.get_pnm_file_type().get_pnm_cann()}" # type: ignore
            )

        header_format = '>B6sIHBI'
        header_size = calcsize(header_format)
        if len(self.pnm_data) < header_size:
            raise ValueError("Insufficient binary data for CmDsOfdmChanEstimateCoef header.")

        (
            self._channel_id,
            mac_raw,
            self._subcarrier_zero_frequency,
            self._first_active_subcarrier_index,
            spacing_khz,
            self._coefficient_data_length,
        ) = unpack(header_format, self.pnm_data[:header_size])

        if self._coefficient_data_length % 4 != 0:
            raise ValueError("Coefficient data length must be a multiple of 4 bytes (2 bytes real + 2 bytes imag).")

        coef_start = header_size
        coef_end = coef_start + self._coefficient_data_length
        if len(self.pnm_data) < coef_end:
            raise ValueError("Coefficient data segment is truncated or incomplete.")

        complex_bytes = self.pnm_data[coef_start:coef_end]
        self._coefficient_data = FixedPointDecoder.decode_complex_data(complex_bytes, self._q_format)

        self._mac_address = MacAddress(mac_raw).to_mac_format(MacAddressFormat.COLON)
        self._subcarrier_spacing = int(spacing_khz) * KHZ

        obw = len(self._coefficient_data) * self._subcarrier_spacing

        # Rounded view (if requested)
        if self._round_precision is not None:
            rp = int(self._round_precision)
            self._coeff_values_rounded = [[round(c.real, rp), round(c.imag, rp)] for c in self._coefficient_data]   # type: ignore
        else:
            self._coeff_values_rounded = [[c.real, c.imag] for c in self._coefficient_data]                         # type: ignore

        self._model = CmDsOfdmChanEstimateCoefModel(
            pnm_header                      =   self.getPnmHeaderParameterModel(),
            channel_id                      =   self._channel_id,
            mac_address                     =   self._mac_address,
            subcarrier_zero_frequency       =   self._subcarrier_zero_frequency,
            subcarrier_spacing              =   self._subcarrier_spacing,
            data_length                     =   self._coefficient_data_length,
            first_active_subcarrier_index   =   self._first_active_subcarrier_index,
            occupied_channel_bandwidth      =   obw,
            values                          =   self._coeff_values_rounded,
        )

    # Overloads provide precise return types to the type checker
    @overload
    def get_coefficients(self, precision: Literal["rounded"] = "rounded") -> ComplexArray: ...
    @overload
    def get_coefficients(self, precision: Literal["raw"]) -> ComplexSeries: ...

    def get_coefficients(self, precision: Literal["rounded", "raw"] = "rounded") -> Union[ComplexArray, ComplexSeries]:
        """
        Retrieve channel-estimation coefficients.

        precision:
            - "rounded": returns [[real, imag], ...] with rounding applied if configured.
            - "raw": returns list[complex] decoded from the payload.
        """
        if precision == "rounded":
            return self._coeff_values_rounded
        return self._coefficient_data

    def to_model(self) -> CmDsOfdmChanEstimateCoefModel:
        """Return the fully-populated pydantic model representation."""
        return self._model

    def to_dict(self) -> Dict:
        """Export model as a Python dict (suitable for JSON serialization)."""
        return self.to_model().model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Export model as a JSON string."""
        return self.to_model().model_dump_json(indent=indent)
