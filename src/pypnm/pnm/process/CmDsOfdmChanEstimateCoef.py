# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from struct import calcsize, unpack
from typing import List, Optional, Tuple, Dict, cast

from pydantic import Field

from pypnm.api.routes.docs.pnm.files.service import MacAddress
from pypnm.lib.constants import INVALID_CHANNEL_ID, KHZ
from pypnm.lib.types import ComplexArray
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


class CmDsOfdmChanEstimateCoefModel(PnmBaseModel):
    """
    """
    data_length: int                        = Field(..., ge=0, description="Number of points (subcarriers)")
    occupied_channel_bandwidth: int         = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units:str                         = Field(default="complex", description="Non-mutable")
    values:ComplexArray                     = Field(..., description="")

class CmDsOfdmChanEstimateCoef(PnmHeader):
    """
    Parses DOCSIS OFDM Downstream Channel Estimation Coefficients from binary data.

    Expected binary format:
        - Channel ID: 1 byte
        - MAC Address: 6 bytes
        - Zero Frequency (Hz): 4 bytes
        - First Active Subcarrier Index: 2 bytes
        - Subcarrier Spacing (kHz): 1 byte
        - Coefficient Data Length (bytes): 4 bytes
        - Complex Coefficient Data: Variable length (fixed-point complex values)
    """

    def __init__(self, binary_data: bytes, sm_n_format: Tuple[int, int] = (2, 13), round_precision: int = 6):
        """
        Initialize and decode the binary coefficient data.

        Args:
            binary_data (bytes): Raw binary input from SNMP/TFTP.
            sm_n_format (Tuple[int, int]): Signed-Magnitude fixed-point format (integer bits, fractional bits).
            round_precision
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._sm_n_format = sm_n_format
        self._round_precision = round_precision
        
        self._channel_id: int                                = INVALID_CHANNEL_ID
        self._mac_address: Optional[str]                     = MacAddress.null()
        self._subcarrier_zero_frequency: int                 = -1
        self._first_active_subcarrier_index: int             = -1
        self._subcarrier_spacing: int                        = -1
        self._coefficient_data_length: int                   = -1
        self._coefficient_data: Optional[List[complex]]      = None
        self._coeff_values_rounded: ComplexArray

        self._model:CmDsOfdmChanEstimateCoefModel

        self._process()

    def _process(self) -> None:
        """
        Internal method to parse and decode channel estimation coefficients.
        """
        if self.get_pnm_file_type() != PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT:
            cann = PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        header_format = '>B6sIHBI'
        header_size = calcsize(header_format)

        if len(self.pnm_data) < header_size:
            raise ValueError("Insufficient binary data for CmDsOfdmChanEstimateCoef header.")

        (
            self._channel_id,
            mac_raw,
            self._subcarrier_zero_frequency,
            self._first_active_subcarrier_index,
            self._subcarrier_spacing,
            self._coefficient_data_length
        ) = unpack(header_format, self.pnm_data[:header_size])

        if self._coefficient_data_length % 4 != 0:
            raise ValueError("Coefficient data length must be a multiple of 4 bytes (2 bytes real + 2 bytes imag).")

        coef_start = header_size
        coef_end = coef_start + self._coefficient_data_length
        if len(self.pnm_data) < coef_end:
            raise ValueError("Coefficient data segment is truncated or incomplete.")

        complex_bytes = self.pnm_data[coef_start:coef_end]
        self._coefficient_data = FixedPointDecoder.decode_complex_data(complex_bytes, self._sm_n_format)

        self._mac_address = ':'.join(f'{b:02x}' for b in mac_raw)
        self._subcarrier_spacing = self._subcarrier_spacing * cast(int,KHZ)
        obw:int = (len(self._coefficient_data) * self._subcarrier_spacing)

        self._coeff_values_rounded = [
            [round(c.real, self._round_precision), 
             round(c.imag, self._round_precision)] if self._round_precision is not None else [c.real, c.imag]
            for c in self._coefficient_data
        ]        

        self._model = CmDsOfdmChanEstimateCoefModel(
            pnm_header                      = self.getPnmHeaderParameterModel(),
            channel_id                      = self._channel_id,
            mac_address                     = self._mac_address,
            subcarrier_zero_frequency       = self._first_active_subcarrier_index,
            subcarrier_spacing              = self._subcarrier_spacing,
            data_length                     = self._coefficient_data_length,
            first_active_subcarrier_index   = self._first_active_subcarrier_index,
            occupied_channel_bandwidth      = obw,
            values                          = self._coeff_values_rounded,
        )

    def get_coefficients(self, precision:str="rounded") -> ComplexArray:
        """
        Returns:
            Optional[List[complex]]: List of complex channel estimation coefficients.
            precision: str rounded | raw
        """
        if precision == "rounded":
            return self._coeff_values_rounded
        
        return cast(ComplexArray, self._coefficient_data)
        

    def to_model(self) -> CmDsOfdmChanEstimateCoefModel:
        return self._model

    def to_dict(self) -> Dict:
        """
        Returns a dictionary of all parsed header and coefficient metadata.

        Args:
            round_precision (Optional[int]): Decimal precision to round real/imag parts of coefficients.
                                             If None, no rounding is applied.

        Returns:
            dict: Dictionary with lowercase snake_case keys.
        """              
        return self.to_model().model_dump()

    def to_json(self, indent:int=2) -> str:
        """
        Serializes parsed data to JSON.

        Args:

        Returns:
            str: JSON string.
        """
        return self.to_model().model_dump_json(indent=indent)
