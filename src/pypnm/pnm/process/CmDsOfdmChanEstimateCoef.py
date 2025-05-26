# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import json
from struct import calcsize, unpack
from typing import List, Optional, Tuple, Dict

from pnm.lib.fixed_point_decoder import FixedPointDecoder
from pnm.process.pnm_file_type import PnmFileType
from pnm.process.pnm_header import PnmHeader


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

    def __init__(self, binary_data: bytes, sm_n_format: Tuple[int, int] = (2, 13)):
        """
        Initialize and decode the binary coefficient data.

        Args:
            binary_data (bytes): Raw binary input from SNMP/TFTP.
            sm_n_format (Tuple[int, int]): Signed-Magnitude fixed-point format (integer bits, fractional bits).
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sm_n_format = sm_n_format
        
        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.first_active_subcarrier_index: Optional[int] = None
        self.subcarrier_spacing: Optional[int] = None
        self.coefficient_data_length: Optional[int] = None
        self.coefficient_data: Optional[List[complex]] = None

        self._parse_header_and_coefficients()

    def _parse_header_and_coefficients(self) -> None:
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
            self.channel_id,
            mac_raw,
            self.subcarrier_zero_frequency,
            self.first_active_subcarrier_index,
            self.subcarrier_spacing,
            self.coefficient_data_length
        ) = unpack(header_format, self.pnm_data[:header_size])

        self.mac_address = ':'.join(f'{b:02x}' for b in mac_raw)

        if self.coefficient_data_length % 4 != 0:
            raise ValueError("Coefficient data length must be a multiple of 4 bytes (2 bytes real + 2 bytes imag).")

        coef_start = header_size
        coef_end = coef_start + self.coefficient_data_length
        if len(self.pnm_data) < coef_end:
            raise ValueError("Coefficient data segment is truncated or incomplete.")

        complex_bytes = self.pnm_data[coef_start:coef_end]
        self.coefficient_data = FixedPointDecoder.decode_complex_data(complex_bytes, self.sm_n_format)

    def get_coefficient_data(self) -> Optional[List[complex]]:
        """
        Returns:
            Optional[List[complex]]: List of complex channel estimation coefficients.
        """
        return self.coefficient_data

    def to_dict(self, round_precision: Optional[int] = 6) -> Dict:
        """
        Returns a dictionary of all parsed header and coefficient metadata.

        Args:
            round_precision (Optional[int]): Decimal precision to round real/imag parts of coefficients.
                                             If None, no rounding is applied.

        Returns:
            dict: Dictionary with lowercase snake_case keys.
        """
        coeffs = self.coefficient_data or []
        coeff_values = [
            [round(c.real, round_precision), round(c.imag, round_precision)] if round_precision is not None else [c.real, c.imag]
            for c in coeffs
        ]
        
        sub_car_spacing:int = int(self.subcarrier_spacing) * 1000   # Hz
        
        data = self.getPnmHeader(header_only=True)
        
        data.update ({
            "channel_id": self.channel_id,
            "mac_address": self.mac_address,
            "zero_frequency": self.subcarrier_zero_frequency,
            "first_active_subcarrier_index": self.first_active_subcarrier_index,
            "subcarrier_spacing": sub_car_spacing,
            "coefficient_data_length": self.coefficient_data_length,
            "number_of_coefficients": len(coeffs),
            "occupied_channel_bandwidth": (len(coeffs) * sub_car_spacing),
            "value_units":"[Real(I),Imaginary(Q)]",
            "values": coeff_values,
        })
        
        return data

    def to_json(self, header_only: bool = False, round_precision: Optional[int] = 6) -> str:
        """
        Serializes parsed data to JSON.

        Args:
            header_only (bool): If True, exclude coefficient values.
            round_precision (Optional[int]): Decimal precision for real/imag rounding in output.

        Returns:
            str: JSON string.
        """
        data = self.to_dict(round_precision=round_precision)
        if header_only:
            data.pop("coefficient_values", None)
            data.pop("number_of_coefficients", None)
        return json.dumps(data, indent=2)

    def to_csv(self) -> str:
        """
        Exports the coefficient values to a CSV-formatted string.

        Returns:
            str: CSV with 'index,real,imag' rows.
        """
        if not self.coefficient_data:
            return ""

        lines = ["index,real,imag"]
        for idx, coeff in enumerate(self.coefficient_data):
            lines.append(f"{idx},{coeff.real},{coeff.imag}")
        return "\n".join(lines)
